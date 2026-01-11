from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import pandera as pa
import polars as pl
from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.agents.tools import send_slack_notification
from src.analytics.schema import LoanTapeSchema
from src.pipeline.data_validation import validate_dataframe
from src.pipeline.utils import (CircuitBreaker, RateLimiter, RetryPolicy,
                                hash_file, utc_now)

logger = logging.getLogger(__name__)


class LoanRecord(BaseModel):
    """Schema enforcement for individual loan or portfolio records."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    loan_id: Optional[str] = Field(None, alias="loan_id")
    total_receivable_usd: float = Field(ge=0)
    total_eligible_usd: float = Field(ge=0)
    discounted_balance_usd: float = Field(ge=0)
    cash_available_usd: float = Field(default=0.0, ge=0)
    dpd_0_7_usd: float = Field(default=0.0, ge=0)
    dpd_7_30_usd: float = Field(default=0.0, ge=0)
    dpd_30_60_usd: float = Field(default=0.0, ge=0)
    dpd_60_90_usd: float = Field(default=0.0, ge=0)
    dpd_90_plus_usd: float = Field(default=0.0, ge=0)
    measurement_date: Optional[str] = None


@dataclass
class IngestionResult:
    """Container for ingestion outputs and metadata."""

    df: pd.DataFrame
    run_id: str
    metadata: Dict[str, Any]
    source_hash: Optional[str] = None
    raw_path: Optional[Path] = None


class UnifiedIngestion:
    """Phase 1: Robust ingestion with validation, checksum, and auditability."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
        data_dir: str | Path | None = None,
        strict_validation: bool = False,
    ):
        root_cfg: Dict[str, Any] = config or {}
        self.config = root_cfg.get("pipeline", {}).get("phases", {}).get("ingestion", {})
        self.run_id = run_id or f"ingest_{uuid.uuid4().hex[:12]}"
        self.data_dir = Path(data_dir) if data_dir is not None else Path(".")
        self.strict_validation = strict_validation
        self.timestamp = utc_now()
        self.audit_log: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.raw_files: List[Dict[str, Any]] = []
        self._summary: Dict[str, Any] = {"rows_ingested": 0, "files": {}}
        self.schema_validator = self._load_schema_validator()
        self.rate_limiter = self._build_rate_limiter(root_cfg)
        self.retry_policy = self._build_retry_policy(root_cfg)
        self.circuit_breaker = self._build_circuit_breaker(root_cfg)

    def ingest_csv(self, filename: str) -> pd.DataFrame:
        """High-performance CSV ingestion using Polars."""

        path = self.data_dir / filename
        try:
            # Polars for high-speed reading
            lf = pl.scan_csv(path)
            df_polars = lf.collect()
            # Convert to pandas for downstream compatibility
            df = df_polars.to_pandas()
        except Exception as exc:
            self.errors.append(
                {
                    "run_id": self.run_id,
                    "timestamp": utc_now(),
                    "file": filename,
                    "stage": "ingestion_read",
                    "error": str(exc),
                }
            )
            return pd.DataFrame()

        ingested = self.ingest_dataframe(df)

        if self.strict_validation:
            required_numeric = [
                "total_receivable_usd",
                "total_eligible_usd",
                "discounted_balance_usd",
                "dpd_0_7_usd",
                "dpd_7_30_usd",
                "dpd_30_60_usd",
                "dpd_60_90_usd",
                "dpd_90_plus_usd",
            ]
            missing_numeric = [c for c in required_numeric if c not in ingested.columns]
            if missing_numeric:
                self.errors.append(
                    {
                        "run_id": self.run_id,
                        "timestamp": utc_now(),
                        "file": filename,
                        "stage": "ingestion_validation",
                        "error": "missing required numeric columns",
                    }
                )
                return pd.DataFrame()

        self._update_summary(len(ingested), filename)
        self.raw_files.append(
            {
                "file": filename,
                "status": "ingested",
                "rows": int(len(ingested)),
                "timestamp": utc_now(),
            }
        )
        return ingested

    def ingest_parquet(self, filename: str) -> pd.DataFrame:
        """High-performance Parquet ingestion using Polars."""
        path = self.data_dir / filename
        try:
            df_polars = pl.read_parquet(path)
            df = df_polars.to_pandas()
            return self.ingest_dataframe(df)
        except Exception as exc:
            logger.error("Parquet ingestion failed: %s", exc)
            return pd.DataFrame()

    def ingest_excel(self, filename: str) -> pd.DataFrame:
        """High-performance Excel ingestion using Polars."""
        path = self.data_dir / filename
        try:
            df_polars = pl.read_excel(path)
            df = df_polars.to_pandas()
            return self.ingest_dataframe(df)
        except Exception as exc:
            logger.error("Excel ingestion failed: %s", exc)
            return pd.DataFrame()

    def ingest_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Legacy helper used by unit tests: normalize and return a copy."""

        ingested = df.copy()
        ingested.columns = pd.Index([str(c).strip() for c in ingested.columns])

        self._update_summary(len(ingested))
        ts = utc_now()
        ingested["_ingest_run_id"] = self.run_id
        ingested["_ingest_timestamp"] = ts
        return ingested

    def validate_loans(self, df: pd.DataFrame) -> pd.DataFrame:
        """Legacy helper used by unit tests.

        Adds a boolean `_validation_passed` column; does not raise.
        """

        required_columns = [
            "loan_id",
            "period",
            "measurement_date",
            "total_receivable_usd",
            "total_eligible_usd",
            "discounted_balance_usd",
            "dpd_0_7_usd",
            "dpd_7_30_usd",
            "dpd_30_60_usd",
            "dpd_60_90_usd",
            "dpd_90_plus_usd",
        ]
        numeric_columns = [
            "total_receivable_usd",
            "total_eligible_usd",
            "discounted_balance_usd",
            "dpd_0_7_usd",
            "dpd_7_30_usd",
            "dpd_30_60_usd",
            "dpd_60_90_usd",
            "dpd_90_plus_usd",
        ]

        validated = df.copy()
        passed = True

        missing = [c for c in required_columns if c not in validated.columns]
        if missing:
            passed = False
            self.errors.append(
                {
                    "run_id": self.run_id,
                    "timestamp": utc_now(),
                    "stage": "validation_schema_assertion",
                    "error": f"missing required columns: {', '.join(missing)}",
                }
            )

        for col in numeric_columns:
            if col not in validated.columns:
                continue
            try:
                pd.to_numeric(validated[col], errors="raise")
            except Exception as exc:
                passed = False
                self.errors.append(
                    {
                        "run_id": self.run_id,
                        "timestamp": utc_now(),
                        "stage": "validation_schema_assertion",
                        "error": f"non-numeric column: {col} ({exc})",
                    }
                )

        validated["_validation_passed"] = passed
        return validated

    def _update_summary(self, rows: int, filename: str | None = None) -> None:
        self._summary["rows_ingested"] = int(self._summary.get("rows_ingested", 0)) + int(rows)
        files = self._summary.setdefault("files", {})
        if filename:
            files[filename] = int(files.get(filename, 0)) + int(rows)

    def get_ingest_summary(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "rows_ingested": int(self._summary.get("rows_ingested", 0)),
            "files": dict(self._summary.get("files", {})),
            "total_errors": len(self.errors),
            "errors": list(self.errors),
        }

    def _build_retry_policy(self, config: Dict[str, Any]) -> RetryPolicy:
        retry_cfg = config.get("cascade", {}).get("http", {}).get("retry", {})
        return RetryPolicy(
            max_retries=retry_cfg.get("max_retries", 3),
            backoff_seconds=retry_cfg.get("backoff_seconds", 1.0),
            jitter_seconds=retry_cfg.get("jitter_seconds", 0.0),
        )

    def _build_rate_limiter(self, config: Dict[str, Any]) -> RateLimiter:
        rate_cfg = config.get("cascade", {}).get("http", {}).get("rate_limit", {})
        return RateLimiter(max_requests_per_minute=rate_cfg.get("max_requests_per_minute", 60))

    def _build_circuit_breaker(self, config: Dict[str, Any]) -> CircuitBreaker:
        cb_cfg = config.get("cascade", {}).get("http", {}).get("circuit_breaker", {})
        return CircuitBreaker(
            failure_threshold=cb_cfg.get("failure_threshold", 3),
            reset_seconds=cb_cfg.get("reset_seconds", 60),
        )

    def _load_schema_validator(self) -> Optional[Draft202012Validator]:
        schema_path = self.config.get("validation", {}).get("schema_path")
        if not schema_path:
            return None
        path = Path(schema_path)
        if not path.exists():
            logger.warning("Schema path missing: %s", path)
            return None
        schema = json.loads(path.read_text(encoding="utf-8"))
        return Draft202012Validator(schema)

    def _log_event(self, event: str, status: str, **details: Any) -> None:
        entry = {
            "run_id": self.run_id,
            "event": event,
            "status": status,
            "timestamp": utc_now(),
            **details,
        }
        self.audit_log.append(entry)
        logger.info("[Ingestion:%s] %s | %s", event, status, details)

    def _record_error(self, stage: str, error: Exception, **details: Any) -> None:
        payload = {
            "run_id": self.run_id,
            "stage": stage,
            "error": str(error),
            "timestamp": utc_now(),
            **details,
        }
        self.errors.append(payload)
        logger.error("[Ingestion:%s] %s", stage, payload)

    def _archive_raw(self, file_path: Path, archive_dir: Path) -> Optional[Path]:
        try:
            archive_dir.mkdir(parents=True, exist_ok=True)
            archived = archive_dir / file_path.name
            shutil.copy2(file_path, archived)
            return archived
        except Exception as exc:
            self._record_error("archive", exc, file=str(file_path))
            return None

    def _validate_schema_pandera(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Validate dataframe using Pandera schemas."""
        try:
            validated_df = LoanTapeSchema.validate(df)
            return validated_df, []
        except pa.errors.SchemaError as exc:
            logger.error("Pandera schema validation failed: %s", exc)
            return df, [str(exc)]

    def _validate_schema(self, df: pd.DataFrame) -> List[str]:
        errors: List[str] = []
        if self.schema_validator is None:
            return errors
        for idx, record in enumerate(df.to_dict(orient="records")):
            for error in self.schema_validator.iter_errors(record):
                errors.append(f"row {idx}: {error.message}")
        return errors

    def _validate_records(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        records = df.to_dict(orient="records")
        validated_records = []
        errors: List[str] = []

        for idx, record in enumerate(records):
            try:
                clean_record = {str(k).strip().lower(): v for k, v in record.items()}
                if "loan_id" not in clean_record:
                    clean_record["loan_id"] = f"agg_{idx}"
                validated_records.append(LoanRecord(**clean_record).model_dump(by_alias=True))
            except ValidationError as exc:
                errors.append(f"row {idx}: {exc}")

        return pd.DataFrame(validated_records), errors

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        validation_cfg = self.config.get("validation", {})
        validate_dataframe(
            df,
            required_columns=validation_cfg.get("required_columns"),
            numeric_columns=validation_cfg.get("numeric_columns"),
            date_columns=validation_cfg.get("date_columns"),
        )

    def _apply_deduplication(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        dedup_cfg = self.config.get("deduplication", {})
        if not dedup_cfg.get("enabled", False):
            return df, 0
        keys = dedup_cfg.get("key_columns")
        if not keys:
            return df, 0
        before = len(df)
        deduped = df.drop_duplicates(subset=keys)
        return deduped, before - len(deduped)

    def _normalize_token(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()

    def _select_column(self, columns: List[str], candidates: Iterable[str]) -> Optional[str]:
        if not candidates:
            return None
        lower_map = {col.lower(): col for col in columns}
        for candidate in candidates:
            key = str(candidate).lower()
            if key in lower_map:
                return lower_map[key]
        normalized_map = {self._normalize_token(col): col for col in columns}
        for candidate in candidates:
            norm = self._normalize_token(candidate)
            if norm in normalized_map:
                return normalized_map[norm]
        for candidate in candidates:
            norm = self._normalize_token(candidate)
            if not norm:
                continue
            for col_norm, col in normalized_map.items():
                if norm in col_norm:
                    return col
        return None

    def _match_metric(self, metric_name: str, mapping: Dict[str, List[str]]) -> Optional[str]:
        metric_norm = self._normalize_token(metric_name)
        if not metric_norm:
            return None
        for key, candidates in mapping.items():
            for candidate in candidates:
                cand_norm = self._normalize_token(candidate)
                if cand_norm and (cand_norm in metric_norm or metric_norm in cand_norm):
                    return key
        return None

    def _default_financials_mapping(self) -> Dict[str, List[str]]:
        return {
            "cash_balance_usd": [
                "cash_balance_usd",
                "cash_balance",
                "cash_usd",
                "cash",
                "cash_on_hand",
                "efectivo",
                "caja",
            ],
            "total_assets_usd": [
                "total_assets_usd",
                "total_assets",
                "assets_total",
                "total_activos",
                "activos_totales",
            ],
            "total_liabilities_usd": [
                "total_liabilities_usd",
                "total_liabilities",
                "liabilities_total",
                "total_pasivos",
                "pasivos_totales",
            ],
            "net_worth_usd": [
                "net_worth_usd",
                "net_worth",
                "equity",
                "total_equity",
                "equity_total",
                "patrimonio",
                "patrimonio_total",
            ],
            "net_income_usd": [
                "net_income_usd",
                "net_income",
                "net_profit",
                "utilidad_neta",
                "utilidad",
                "resultado_neto",
            ],
            "runway_months": [
                "runway_months",
                "runway",
                "months_of_runway",
                "meses_runway",
            ],
            "debt_to_equity_ratio": [
                "debt_to_equity_ratio",
                "debt_equity_ratio",
                "debt_to_equity",
                "deuda_patrimonio",
            ],
        }

    def _load_looker_financials(
        self, financials_path: Optional[Path]
    ) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Any]]:
        if not financials_path:
            return {}, {"files": [], "dates": 0, "metrics": []}
        path = Path(financials_path)
        files: List[Path] = []
        if path.is_dir():
            files = sorted(
                [
                    *path.glob("*.csv"),
                    *path.glob("*.xlsx"),
                    *path.glob("*.xls"),
                ],
                key=lambda p: p.stat().st_mtime,
            )
        elif path.exists():
            files = [path]
        if not files:
            self._log_event("looker_financials", "skipped", reason="no_files_found")
            return {}, {"files": [], "dates": 0, "metrics": []}

        looker_cfg = self.config.get("looker", {})
        mapping = looker_cfg.get("financials_metrics") or self._default_financials_mapping()
        date_candidates = looker_cfg.get(
            "financials_date_column_candidates",
            ["reporting_date", "as_of_date", "date", "fecha", "fecha_corte"],
        )
        metric_candidates = looker_cfg.get(
            "financials_metric_column_candidates",
            ["metric", "account", "line_item", "concept", "concepto", "cuenta", "name"],
        )
        value_candidates = looker_cfg.get(
            "financials_value_column_candidates",
            ["value", "amount", "balance", "saldo", "total", "monto", "usd"],
        )
        format_mode = str(looker_cfg.get("financials_format", "auto")).lower()
        default_date_strategy = str(
            looker_cfg.get("financials_default_date_strategy", "file_mtime")
        ).lower()

        financials_by_date: Dict[str, Dict[str, float]] = {}
        for file_path in files:
            try:
                if file_path.suffix.lower() in {".xlsx", ".xls"}:
                    financials_df = pd.read_excel(file_path)
                else:
                    financials_df = pd.read_csv(file_path)
            except Exception as exc:
                self._record_error("looker_financials_read", exc, file=str(file_path))
                continue
            if financials_df.empty:
                continue

            columns = list(financials_df.columns)
            date_col = self._select_column(columns, date_candidates)
            metric_col = self._select_column(columns, metric_candidates)
            value_col = self._select_column(columns, value_candidates)

            if format_mode == "auto":
                is_long = bool(metric_col and value_col)
            else:
                is_long = format_mode == "long"

            if date_col:
                date_series = pd.to_datetime(financials_df[date_col], errors="coerce").dt.strftime(
                    "%Y-%m-%d"
                )
            else:
                if default_date_strategy == "file_mtime":
                    default_date = (
                        datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc)
                        .date()
                        .isoformat()
                    )
                else:
                    default_date = datetime.now(timezone.utc).date().isoformat()
                date_series = pd.Series(
                    [default_date] * len(financials_df), index=financials_df.index
                )

            if is_long:
                if not metric_col or not value_col:
                    self._log_event(
                        "looker_financials",
                        "skipped",
                        reason="missing_metric_or_value",
                        file=str(file_path),
                    )
                    continue
                values = pd.to_numeric(financials_df[value_col], errors="coerce")
                for idx, metric_name in financials_df[metric_col].items():
                    metric_key = self._match_metric(metric_name, mapping)
                    if not metric_key:
                        continue
                    metric_value = values[idx]
                    if pd.isna(metric_value):
                        continue
                    date_value = date_series[idx]
                    if not date_value or pd.isna(date_value):
                        continue
                    metrics = financials_by_date.setdefault(str(date_value), {})
                    metrics[metric_key] = float(metric_value)
            else:
                for metric_key, candidates in mapping.items():
                    column = self._select_column(columns, candidates)
                    if not column:
                        continue
                    values = pd.to_numeric(financials_df[column], errors="coerce")
                    for idx, metric_value in values.items():
                        if pd.isna(metric_value):
                            continue
                        date_value = date_series[idx]
                        if not date_value or pd.isna(date_value):
                            continue
                        metrics = financials_by_date.setdefault(str(date_value), {})
                        metrics[metric_key] = float(metric_value)

        for metrics in financials_by_date.values():
            assets = metrics.get("total_assets_usd")
            liabilities = metrics.get("total_liabilities_usd")
            if (
                metrics.get("net_worth_usd") is None
                and assets is not None
                and liabilities is not None
            ):
                metrics["net_worth_usd"] = float(assets) - float(liabilities)
            net_worth = metrics.get("net_worth_usd")
            if (
                metrics.get("debt_to_equity_ratio") is None
                and liabilities is not None
                and net_worth not in (None, 0)
            ):
                metrics["debt_to_equity_ratio"] = float(liabilities or 0.0) / float(
                    net_worth or 1.0
                )

        metrics_set = sorted({key for values in financials_by_date.values() for key in values})
        meta = {
            "files": [str(p) for p in files],
            "dates": len(financials_by_date),
            "metrics": metrics_set,
        }
        if financials_by_date:
            self._log_event("looker_financials", "loaded", dates=len(financials_by_date))
        return financials_by_date, meta

    def _apply_financials_to_snapshot(
        self, df: pd.DataFrame, financials_by_date: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        if df.empty:
            return df
        metrics = [
            "cash_balance_usd",
            "total_assets_usd",
            "total_liabilities_usd",
            "net_worth_usd",
            "net_income_usd",
            "runway_months",
            "debt_to_equity_ratio",
        ]
        for metric in metrics:
            df[metric] = df["measurement_date"].map(
                lambda date, m=metric: financials_by_date.get(str(date), {}).get(m)
            )
        if "cash_available_usd" not in df.columns:
            df["cash_available_usd"] = 0.0
        if "cash_balance_usd" in df.columns:
            df["cash_available_usd"] = df["cash_available_usd"].fillna(df["cash_balance_usd"])
        df["cash_available_usd"] = df["cash_available_usd"].fillna(0.0)
        return df

    def _looker_par_balances_to_loan_tape(
        self, df: pd.DataFrame, financials_by_date: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        column_map = {col.lower(): col for col in df.columns}
        reporting_col = column_map.get("reporting_date")
        outstanding_col = column_map.get("outstanding_balance_usd") or column_map.get(
            "outstanding_balance"
        )
        par_7_col = column_map.get("par_7_balance_usd")
        par_30_col = column_map.get("par_30_balance_usd")
        par_60_col = column_map.get("par_60_balance_usd")
        par_90_col = column_map.get("par_90_balance_usd")

        missing = [
            name
            for name, col in {
                "reporting_date": reporting_col,
                "outstanding_balance_usd": outstanding_col,
                "par_7_balance_usd": par_7_col,
                "par_30_balance_usd": par_30_col,
                "par_60_balance_usd": par_60_col,
                "par_90_balance_usd": par_90_col,
            }.items()
            if col is None
        ]
        if missing:
            raise ValueError(f"Missing Looker PAR columns: {', '.join(missing)}")

        measurement_date = pd.to_datetime(df[reporting_col], errors="coerce").dt.strftime(
            "%Y-%m-%d"
        )
        total_receivable = pd.to_numeric(df[outstanding_col], errors="coerce")
        par_7 = pd.to_numeric(df[par_7_col], errors="coerce")
        par_30 = pd.to_numeric(df[par_30_col], errors="coerce")
        par_60 = pd.to_numeric(df[par_60_col], errors="coerce")
        par_90 = pd.to_numeric(df[par_90_col], errors="coerce")

        frame = pd.DataFrame(
            {
                "measurement_date": measurement_date,
                "total_receivable_usd": total_receivable,
                "dpd_90_plus_usd": par_90,
                "dpd_60_90_usd": (par_60 - par_90).clip(lower=0),
                "dpd_30_60_usd": (par_30 - par_60).clip(lower=0),
                "dpd_7_30_usd": (par_7 - par_30).clip(lower=0),
                "dpd_0_7_usd": (total_receivable - par_7).clip(lower=0),
            }
        ).dropna(subset=["measurement_date"])

        grouped = (
            frame.groupby("measurement_date", dropna=False).sum(numeric_only=True).reset_index()
        )
        grouped["total_eligible_usd"] = grouped["total_receivable_usd"]
        grouped["discounted_balance_usd"] = grouped["total_receivable_usd"]
        grouped["loan_id"] = grouped["measurement_date"].apply(
            lambda date: f"looker_snapshot_{str(date).replace('-', '')}"
        )
        grouped = self._apply_financials_to_snapshot(grouped, financials_by_date)
        return grouped

    def _looker_dpd_to_loan_tape(
        self, df: pd.DataFrame, financials_by_date: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        column_map = {col.lower(): col for col in df.columns}
        dpd_col = column_map.get("dpd") or column_map.get("days_past_due")
        balance_col = column_map.get("outstanding_balance_usd") or column_map.get(
            "outstanding_balance"
        )
        if not dpd_col or not balance_col:
            raise ValueError("Missing Looker loan columns: dpd, outstanding_balance")

        looker_cfg = self.config.get("looker", {})
        measurement_col = looker_cfg.get("measurement_date_column")
        strategy = looker_cfg.get("measurement_date_strategy", "today")

        measurement_date = None
        if measurement_col:
            resolved = self._select_column(list(df.columns), [measurement_col])
            if resolved:
                measurement_date = pd.to_datetime(df[resolved], errors="coerce").dt.strftime(
                    "%Y-%m-%d"
                )
        if measurement_date is None:
            if strategy == "max_disburse_date":
                resolved = self._select_column(
                    list(df.columns), ["disburse_date", "disbursement_date"]
                )
            elif strategy == "max_maturity_date":
                resolved = self._select_column(list(df.columns), ["maturity_date", "loan_end_date"])
            else:
                resolved = None
            if resolved:
                max_date = pd.to_datetime(df[resolved], errors="coerce").max()
                date_value = max_date.date().isoformat() if pd.notna(max_date) else None
            else:
                date_value = None
            if not date_value:
                date_value = datetime.now(timezone.utc).date().isoformat()
            measurement_date = pd.Series([date_value] * len(df), index=df.index)

        balance = pd.to_numeric(df[balance_col], errors="coerce").fillna(0.0)
        dpd = pd.to_numeric(df[dpd_col], errors="coerce").fillna(0.0)

        frame = pd.DataFrame(
            {
                "measurement_date": measurement_date,
                "total_receivable_usd": balance,
                "dpd_90_plus_usd": balance.where(dpd >= 90, 0.0),
                "dpd_60_90_usd": balance.where((dpd >= 60) & (dpd < 90), 0.0),
                "dpd_30_60_usd": balance.where((dpd >= 30) & (dpd < 60), 0.0),
                "dpd_7_30_usd": balance.where((dpd >= 7) & (dpd < 30), 0.0),
                "dpd_0_7_usd": balance.where(dpd < 7, 0.0),
            }
        ).dropna(subset=["measurement_date"])

        grouped = (
            frame.groupby("measurement_date", dropna=False).sum(numeric_only=True).reset_index()
        )
        grouped["total_eligible_usd"] = grouped["total_receivable_usd"]
        grouped["discounted_balance_usd"] = grouped["total_receivable_usd"]
        grouped["loan_id"] = grouped["measurement_date"].apply(
            lambda date: f"looker_snapshot_{str(date).replace('-', '')}"
        )
        grouped = self._apply_financials_to_snapshot(grouped, financials_by_date)
        return grouped

    def ingest_file(self, file_path: Path, archive_dir: Optional[Path] = None) -> IngestionResult:
        self._log_event("start", "initiated", file_path=str(file_path))
        if not file_path.exists():
            self._log_event("file_check", "failed", error="File not found")
            raise FileNotFoundError(f"Input file not found: {file_path}")

        checksum = hash_file(file_path)
        try:
            if file_path.suffix.lower() in {".parquet", ".pq"}:
                df = pd.read_parquet(file_path)
            elif file_path.suffix.lower() in {".json"}:
                df = pd.read_json(file_path)
            else:
                df = pd.read_csv(file_path)
            self._log_event("raw_read", "success", rows=len(df), checksum=checksum)

            schema_errors = self._validate_schema(df)

            # Pandera Strict Contract Validation (Engineering Excellence Mandate)
            df, pandera_errors = self._validate_schema_pandera(df)

            validated_df, record_errors = self._validate_records(df)
            errors = schema_errors + pandera_errors + record_errors

            if errors:
                self._log_event("validation", "completed", error_count=len(errors))

                # Circuit Breaker: Halt on critical contract violations and alert via Slack
                critical_violation = any(
                    "contract" in str(e).lower()
                    or "not found" in str(e).lower()
                    or "future" in str(e).lower()
                    for e in errors
                )
                if critical_violation:
                    msg = f"🚨 CIRCUIT BREAKER: Critical data contract violation in {file_path.name}. Halting ingestion."
                    logger.critical(msg)
                    try:
                        send_slack_notification(msg, channel="#data-engineering-alerts")
                    except Exception as slack_err:
                        logger.error("Failed to send Slack alert: %s", slack_err)
                    return IngestionResult(
                        pd.DataFrame(),
                        self.run_id,
                        {"status": "halted", "error": "critical_violation"},
                    )

            self._validate_dataframe(validated_df)

            if errors and self.config.get("validation", {}).get("strict", True):
                raise ValueError(f"Schema validation failed for {len(errors)} rows")

            validated_df, deduped_count = self._apply_deduplication(validated_df)
            if deduped_count:
                self._log_event("deduplication", "completed", removed=deduped_count)

            archived = None
            if archive_dir:
                archived = self._archive_raw(file_path, archive_dir)

            metadata = {
                "source_file": str(file_path),
                "checksum": checksum,
                "row_count": len(validated_df),
                "error_count": len(errors),
                "deduped_count": deduped_count,
                "audit_log": self.audit_log,
                "archived_path": str(archived) if archived else None,
                "validation_errors": errors,
            }

            self._log_event("complete", "success", row_count=len(validated_df))
            return IngestionResult(
                validated_df, self.run_id, metadata, source_hash=checksum, raw_path=archived
            )

        except Exception as exc:
            self._record_error("fatal_error", exc)
            raise

    def ingest_looker(
        self,
        loans_path: Path,
        financials_path: Optional[Path] = None,
        archive_dir: Optional[Path] = None,
    ) -> IngestionResult:
        self._log_event(
            "looker_start",
            "initiated",
            loans_path=str(loans_path),
            financials_path=str(financials_path) if financials_path else None,
        )
        if not loans_path.exists():
            self._log_event("looker_file_check", "failed", error="Loans file not found")
            raise FileNotFoundError(f"Looker loans file not found: {loans_path}")

        checksum = hash_file(loans_path)
        try:
            df = pd.read_csv(loans_path)
            financials_by_date, financials_meta = self._load_looker_financials(financials_path)

            columns_lower = {col.lower() for col in df.columns}
            has_par = {
                "reporting_date",
                "par_7_balance_usd",
                "par_30_balance_usd",
                "par_60_balance_usd",
                "par_90_balance_usd",
            }.issubset(columns_lower)
            has_dpd = (
                {"dpd", "outstanding_balance"}.issubset(columns_lower)
                or {
                    "dpd",
                    "outstanding_balance_usd",
                }.issubset(columns_lower)
                or {"days_past_due", "outstanding_balance"}.issubset(columns_lower)
            )

            if has_par:
                normalized_df = self._looker_par_balances_to_loan_tape(df, financials_by_date)
                source_mode = "looker_par_balances"
            elif has_dpd:
                normalized_df = self._looker_dpd_to_loan_tape(df, financials_by_date)
                source_mode = "looker_loans"
            else:
                raise ValueError(
                    "Looker loans file missing required PAR or DPD columns for conversion"
                )
            if normalized_df.empty:
                raise ValueError("Looker loan tape conversion produced no rows")

            schema_errors = self._validate_schema(normalized_df)
            validated_df, record_errors = self._validate_records(normalized_df)
            errors = schema_errors + record_errors
            if errors:
                self._log_event("validation", "completed", error_count=len(errors))

            self._validate_dataframe(validated_df)

            if errors and self.config.get("validation", {}).get("strict", True):
                raise ValueError(f"Schema validation failed for {len(errors)} rows")

            validated_df, deduped_count = self._apply_deduplication(validated_df)
            if deduped_count:
                self._log_event("deduplication", "completed", removed=deduped_count)

            archived = None
            if archive_dir:
                archived = self._archive_raw(loans_path, archive_dir)

            metadata = {
                "source_looker_loans": str(loans_path),
                "financials_path": str(financials_path) if financials_path else None,
                "source_mode": source_mode,
                "checksum": checksum,
                "row_count": len(validated_df),
                "error_count": len(errors),
                "deduped_count": deduped_count,
                "audit_log": self.audit_log,
                "archived_path": str(archived) if archived else None,
                "validation_errors": errors,
                "financials": financials_meta,
            }

            self._log_event("looker_complete", "success", row_count=len(validated_df))
            return IngestionResult(
                validated_df, self.run_id, metadata, source_hash=checksum, raw_path=archived
            )

        except Exception as exc:
            self._record_error("looker_fatal_error", exc)
            raise

    def ingest_http(self, url: str, headers: Optional[Dict[str, str]] = None) -> IngestionResult:
        import requests

        headers = headers or {}
        self._log_event("http_start", "initiated", url=url)

        def _do_request() -> requests.Response:
            if not self.circuit_breaker.allow():
                raise RuntimeError("Circuit breaker open for Cascade HTTP ingestion")
            self.rate_limiter.wait()
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response

        try:
            response = self.retry_policy.execute(
                _do_request,
                on_retry=lambda attempt, exc: self._log_event(
                    "http_retry", "retrying", attempt=attempt, error=str(exc)
                ),
            )
            self.circuit_breaker.record_success()
        except Exception as exc:
            self.circuit_breaker.record_failure()
            self._record_error("http_failed", exc, url=url)
            raise

        content = response.content
        checksum = hashlib.sha256(content).hexdigest()
        content_type = response.headers.get("Content-Type", "").lower()
        if "json" in content_type:
            df = pd.read_json(BytesIO(content))
        else:
            df = pd.read_csv(StringIO(content.decode("utf-8")))

        schema_errors = self._validate_schema(df)
        validated_df, record_errors = self._validate_records(df)
        errors = schema_errors + record_errors
        if errors:
            self._log_event("validation", "completed", error_count=len(errors))

        self._validate_dataframe(validated_df)

        if errors and self.config.get("validation", {}).get("strict", True):
            raise ValueError(f"Schema validation failed for {len(errors)} rows")

        validated_df, deduped_count = self._apply_deduplication(validated_df)
        if deduped_count:
            self._log_event("deduplication", "completed", removed=deduped_count)

        metadata = {
            "source_url": url,
            "checksum": checksum,
            "row_count": len(validated_df),
            "error_count": len(errors),
            "deduped_count": deduped_count,
            "audit_log": self.audit_log,
            "validation_errors": errors,
        }

        self._log_event("http_complete", "success", row_count=len(validated_df))
        return IngestionResult(
            validated_df, self.run_id, metadata, source_hash=checksum, raw_path=None
        )
