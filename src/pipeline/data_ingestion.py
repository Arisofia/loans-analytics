from __future__ import annotations

import hashlib
import logging
import shutil
import uuid
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import polars as pl

from src.agents.tools import send_slack_notification
from src.pipeline.data_validation import (DataQualityReport,
                                          DataQualityReporter,
                                          validate_dataframe)
from src.pipeline.ingestion_validator import IngestionValidator
from src.pipeline.looker_converter import LookerConverter
from src.pipeline.models import IngestionResult
from src.pipeline.utils import (CircuitBreaker, RateLimiter, RetryPolicy,
                                hash_file, utc_now)

logger = logging.getLogger(__name__)

# DPD (Days Past Due) threshold constants aligned with loan tape bucket definitions
DPD_THRESHOLD_7 = 7
DPD_THRESHOLD_30 = 30
DPD_THRESHOLD_60 = 60
DPD_THRESHOLD_90 = 90


class UnifiedIngestion:
    """Phase 1: Robust ingestion with validation, checksum, and auditability."""

    def __init__(self, config: Dict[str, Any], run_id: Optional[str] = None):
        self.config = config.get("pipeline", {}).get("phases", {}).get("ingestion", {})
        self.run_id = run_id or f"ingest_{uuid.uuid4().hex[:12]}"
        self.timestamp = utc_now()
        self.audit_log: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.raw_files: List[Dict[str, Any]] = []
        self._summary: Dict[str, Any] = {}

        self.validator = IngestionValidator(self.config)
        self.looker_converter = LookerConverter(self.config)

        self.rate_limiter = self._build_rate_limiter(config)
        self.retry_policy = self._build_retry_policy(config)
        self.circuit_breaker = self._build_circuit_breaker(config)

    def ingest_parquet(self, filename: str) -> pd.DataFrame:
        """High-performance Parquet ingestion using Polars."""
        # Note: data_dir is usually passed in config or derived
        path = Path(self.config.get("data_dir", "data/raw")) / filename
        try:
            df_polars = pl.read_parquet(path)
            df = df_polars.to_pandas()
            return self.ingest_dataframe(df)
        except Exception as exc:
            logger.error("Parquet ingestion failed: %s", exc)
            return pd.DataFrame()

    def ingest_excel(self, filename: str) -> pd.DataFrame:
        """High-performance Excel ingestion using Polars."""
        path = Path(self.config.get("data_dir", "data/raw")) / filename
        try:
            df = pl.read_excel(path).to_pandas()
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
        """Legacy helper used by unit tests. Adds a boolean `_validation_passed` column."""
        validated, errors = self.validator.validate_pandera(df)
        res = validated.copy()
        res["_validation_passed"] = len(errors) == 0
        for err in errors:
            self._record_error("validation_schema_assertion", Exception(err))
        return res

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
            self._log_event("archive", "success", file=str(file_path), archived=str(archived))
            return archived
        except Exception as exc:
            self._record_error("archive", exc, file=str(file_path))
            return None

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        validation_cfg = self.config.get("validation", {})
        validate_dataframe(
            df,
            required_columns=validation_cfg.get("required_columns"),
            numeric_columns=validation_cfg.get("numeric_columns"),
            date_columns=validation_cfg.get("date_columns"),
        )

    def _run_quality_audit(self, df: pd.DataFrame) -> DataQualityReport:
        validation_cfg = self.config.get("validation", {})
        reporter = DataQualityReporter(df)
        return reporter.run_audit(
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

    # --- Compatibility Aliases for Legacy Tests ---
    def _load_looker_financials(self, path: Optional[Path]) -> Dict[str, float]:
        """Shim for legacy tests."""
        res, _ = self.looker_converter.load_financials(path)
        return {d: m.get("cash_balance_usd", 0.0) for d, m in res.items()}

    def _looker_par_balances_to_loan_tape(
        self, df: pd.DataFrame, cash_by_date: Dict[str, float]
    ) -> pd.DataFrame:
        """Shim for legacy tests."""
        nested_cash = {d: {"cash_balance_usd": v} for d, v in cash_by_date.items()}
        return self.looker_converter.convert_par_balances(df, nested_cash)

    def _looker_dpd_to_loan_tape(
        self, df: pd.DataFrame, cash_by_date: Dict[str, float]
    ) -> pd.DataFrame:
        """Shim for legacy tests."""
        nested_cash = {d: {"cash_balance_usd": v} for d, v in cash_by_date.items()}
        return self.looker_converter.convert_dpd_loans(df, nested_cash)

    # ----------------------------------------------

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
                try:
                    df = pd.read_json(file_path)
                except ValueError:
                    df = pd.read_json(file_path, lines=True)
            elif file_path.suffix.lower() in {".xlsx", ".xls"}:
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)

            self._log_event("raw_read", "success", rows=len(df), checksum=checksum)

            schema_errors = self.validator.validate_schema(df)
            df, pandera_errors = self.validator.validate_pandera(df)
            validated_df, record_errors = self.validator.validate_models(df)
            errors = schema_errors + pandera_errors + record_errors

            if errors:
                self._log_event("validation", "completed", error_count=len(errors))
                critical_violation = any(
                    ("contract" in str(e).lower() or "future" in str(e).lower())
                    and "not found" not in str(e).lower()
                    and "column" not in str(e).lower()
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

            quality_report = self._run_quality_audit(validated_df)

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
                "quality_score": quality_report.score,
            }

            self._log_event("complete", "success", row_count=len(validated_df))
            return IngestionResult(
                validated_df,
                self.run_id,
                metadata,
                source_hash=checksum,
                raw_path=archived,
                quality_report=quality_report,
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

            # Detect schema drift
            schema_diff = self.validator.detect_looker_schema_drift(set(df.columns))
            if schema_diff.get("missing"):
                self._log_event("looker_schema_drift", "warning", missing=schema_diff["missing"])
                if self.config.get("validation", {}).get("strict", True):
                    raise ValueError(
                        f"Looker schema drift detected. Missing columns: {schema_diff['missing']}"
                    )

            financials_by_date, financials_meta = self.looker_converter.load_financials(
                financials_path
            )

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
                or {"dpd", "outstanding_balance_usd"}.issubset(columns_lower)
                or {"days_past_due", "outstanding_balance"}.issubset(columns_lower)
            )

            if has_par:
                normalized_df = self.looker_converter.convert_par_balances(df, financials_by_date)
                source_mode = "looker_par_balances"
            elif has_dpd:
                normalized_df = self.looker_converter.convert_dpd_loans(df, financials_by_date)
                source_mode = "looker_loans"
            else:
                raise ValueError(
                    "Looker loans file missing required PAR or DPD columns for conversion"
                )

            if normalized_df.empty:
                raise ValueError("Looker loan tape conversion produced no rows")

            schema_errors = self.validator.validate_schema(normalized_df)
            validated_df, record_errors = self.validator.validate_models(normalized_df)
            errors = schema_errors + record_errors
            if errors:
                self._log_event("validation", "completed", error_count=len(errors))

            self._validate_dataframe(validated_df)

            if errors and self.config.get("validation", {}).get("strict", True):
                raise ValueError(f"Schema validation failed for {len(errors)} rows")

            validated_df, deduped_count = self._apply_deduplication(validated_df)
            if deduped_count:
                self._log_event("deduplication", "completed", removed=deduped_count)

            quality_report = self._run_quality_audit(validated_df)

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
                "quality_score": quality_report.score,
            }

            self._log_event("looker_complete", "success", row_count=len(validated_df))
            return IngestionResult(
                validated_df,
                self.run_id,
                metadata,
                source_hash=checksum,
                raw_path=archived,
                quality_report=quality_report,
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

        schema_errors = self.validator.validate_schema(df)
        validated_df, record_errors = self.validator.validate_models(df)
        errors = schema_errors + record_errors
        if errors:
            self._log_event("validation", "completed", error_count=len(errors))

        quality_report = self._run_quality_audit(validated_df)

        metadata = {
            "source_url": url,
            "checksum": checksum,
            "row_count": len(validated_df),
            "error_count": len(errors),
            "audit_log": self.audit_log,
            "validation_errors": errors,
            "quality_score": quality_report.score,
        }

        self._log_event("http_complete", "success", row_count=len(validated_df))
        return IngestionResult(
            validated_df, self.run_id, metadata, source_hash=checksum, quality_report=quality_report
        )
