from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import uuid
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import pandera as pa
import polars as pl
from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, ValidationError

import requests

from src.pipeline.data_validation import DataQualityReport
from src.pipeline.schema import LoanTapeSchema
from src.pipeline.utils import CircuitBreaker, RateLimiter, RetryPolicy, hash_file, utc_now
from src.pipeline.mixins import IngestionMixin

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
    quality_report: Optional[DataQualityReport] = None


class UnifiedIngestion(IngestionMixin):
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

        # Security: Size check
        max_size_mb = self.config.get("max_file_size_mb", 50)
        if path.exists() and path.stat().st_size > max_size_mb * 1024 * 1024:
            self._record_error(
                "ingestion_read",
                Exception(f"File size exceeds limit of {max_size_mb}MB"),
                file=filename,
            )
            return pd.DataFrame()

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

        # Security: Size check
        max_size_mb = self.config.get("max_file_size_mb", 50)
        if path.exists() and path.stat().st_size > max_size_mb * 1024 * 1024:
            self._record_error(
                "ingestion_read_parquet",
                Exception(f"File size exceeds limit of {max_size_mb}MB"),
                file=filename,
            )
            return pd.DataFrame()

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

        # Security: Size check
        max_size_mb = self.config.get("max_file_size_mb", 50)
        if path.exists() and path.stat().st_size > max_size_mb * 1024 * 1024:
            self._record_error(
                "ingestion_read_excel",
                Exception(f"File size exceeds limit of {max_size_mb}MB"),
                file=filename,
            )
            return pd.DataFrame()

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
        # Example numeric columns to check; adjust as needed for your schema
        numeric_columns = [
            "total_receivable_usd",
            "total_eligible_usd",
            "discounted_balance_usd",
            "cash_available_usd",
            "dpd_0_7_usd",
        ]
        validated = ingested.copy()
        passed = True
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
        retry_cfg = config.get("http", {}).get("retry", {})
        return RetryPolicy(
            max_retries=retry_cfg.get("max_retries", 3),
            backoff_seconds=retry_cfg.get("backoff_seconds", 1.0),
            jitter_seconds=retry_cfg.get("jitter_seconds", 0.0),
        )

    def _build_rate_limiter(self, config: Dict[str, Any]) -> RateLimiter:
        rate_cfg = config.get("http", {}).get("rate_limit", {})
        return RateLimiter(max_requests_per_minute=rate_cfg.get("max_requests_per_minute", 60))

    def _build_circuit_breaker(self, config: Dict[str, Any]) -> CircuitBreaker:
        cb_cfg = config.get("http", {}).get("circuit_breaker", {})
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
            checksum = hash_file(file_path)
            # Use content hash in filename to prevent collisions and ensure auditability
            archived = archive_dir / f"{file_path.stem}.{checksum}{file_path.suffix}"
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

    def ingest(
        self,
        input_file: Path,
        archive_dir: Optional[Path] = None,
    ) -> IngestionResult:
        """Execute ingestion based on configuration source."""
        source = self.config.get("source", "file")
        logger.info("Starting ingestion from source: %s", source)

        # Default: File source
        return self.ingest_file(input_file, archive_dir=archive_dir)

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

                # Circuit Breaker: Halt on critical contract violations.
                critical_violation = any(
                    "contract" in str(e).lower()
                    or "not found" in str(e).lower()
                    or "future" in str(e).lower()
                    for e in errors
                )
                if critical_violation:
                    msg = f"🚨 CIRCUIT BREAKER: Critical data contract violation in {file_path.name}. Halting ingestion."
                    logger.critical(msg)
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

    def ingest_http(self, url: str, headers: Optional[Dict[str, str]] = None) -> IngestionResult:

        headers = headers or {}
        self._log_event("http_start", "initiated", url=url)

        def _do_request() -> requests.Response:
            if not self.circuit_breaker.allow():
                raise RuntimeError("Circuit breaker open for HTTP ingestion")
            self.rate_limiter.wait()
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response

        try:
            response = self.retry_policy.execute(
                _do_request,
                on_retry=lambda exc: self._log_event("http_retry", "retrying", error=str(exc)),
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
