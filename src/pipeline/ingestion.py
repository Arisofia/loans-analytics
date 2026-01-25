import hashlib
import json
import logging
import shutil
import uuid
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field, ValidationError

from src.pipeline.utils import CircuitBreaker, RateLimiter, RetryPolicy, hash_file, utc_now
from src.pipeline.validation import DataQualityReport, DataQualityReporter
from src.pipeline.mixins import IngestionMixin

logger = logging.getLogger("abaco.ingestion")

# DPD (Days Past Due) threshold constants aligned with loan tape bucket definitions
DPD_THRESHOLD_7 = 7
DPD_THRESHOLD_30 = 30
DPD_THRESHOLD_60 = 60
DPD_THRESHOLD_90 = 90


class LoanRecord(BaseModel):
    """Schema enforcement for individual loan or portfolio records."""

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

    class Config:
        populate_by_name = True
        extra = "allow"


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

    def __init__(self, config: Dict[str, Any], run_id: Optional[str] = None):
        self.config = config.get("pipeline", {}).get("phases", {}).get("ingestion", {})
        self.run_id = run_id or f"ingest_{uuid.uuid4().hex[:12]}"
        self.audit_log: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.schema_validator = self._load_schema_validator()
        self.rate_limiter = self._build_rate_limiter(config)
        self.retry_policy = self._build_retry_policy(config)
        self.circuit_breaker = self._build_circuit_breaker(config)

    def _build_retry_policy(self, config: Dict[str, Any]) -> RetryPolicy:
        retry_cfg = config.get("warehouse", {}).get("http", {}).get("retry", {})
        return RetryPolicy(
            max_retries=retry_cfg.get("max_retries", 3),
            backoff_seconds=retry_cfg.get("backoff_seconds", 1.0),
            jitter_seconds=retry_cfg.get("jitter_seconds", 0.0),
        )

    def _build_rate_limiter(self, config: Dict[str, Any]) -> RateLimiter:
        rate_cfg = config.get("warehouse", {}).get("http", {}).get("rate_limit", {})
        return RateLimiter(max_requests_per_minute=rate_cfg.get("max_requests_per_minute", 60))

    def _build_circuit_breaker(self, config: Dict[str, Any]) -> CircuitBreaker:
        cb_cfg = config.get("warehouse", {}).get("http", {}).get("circuit_breaker", {})
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

    def _log_event(
        self,
        event: str,
        status: str,
        phase: Optional[str] = None,
        source: Optional[str] = None,
        **details: Any,
    ) -> None:
        entry = {
            "run_id": self.run_id,
            "event": event,
            "status": status,
            "phase": phase,
            "source": source,
            "timestamp": utc_now(),
            **details,
        }
        # Remove None values for cleaner logs/audit entries
        entry = {k: v for k, v in entry.items() if v is not None}
        self.audit_log.append(entry)
        logger.info("[Ingestion:%s] %s | %s", event, status, json.dumps(entry))

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

    def _run_quality_audit(self, df: pd.DataFrame) -> DataQualityReport:
        validation_cfg = self.config.get("validation", {})
        reporter = DataQualityReporter(df)
        return reporter.run_audit(
            required_columns=validation_cfg.get("required_columns"),
            numeric_columns=validation_cfg.get("numeric_columns"),
            date_columns=validation_cfg.get("date_columns"),
        )

    def _select_column(self, columns: List[str], candidates: List[str]) -> Optional[str]:
        column_map = {col.lower(): col for col in columns}
        for candidate in candidates:
            key = candidate.lower()
            if key in column_map:
                return column_map[key]
        return None

    def ingest_file(self, file_path: Path, archive_dir: Optional[Path] = None) -> IngestionResult:

        self._log_event("start", "initiated", file_path=str(file_path))
        if not file_path.exists():
            self._log_event("file_check", "failed", error="File not found")
            raise FileNotFoundError(f"Input file not found: {file_path}")

        checksum = hash_file(file_path)
        try:
            suffix = file_path.suffix.lower()
            if suffix in {".parquet", ".pq"}:
                df = pd.read_parquet(file_path)
            elif suffix in {".xlsx", ".xls"}:
                df = pd.read_excel(file_path)
            elif suffix == ".json":
                # Support newline-delimited JSON first, then standard JSON
                try:
                    df = pd.read_json(file_path, lines=True)
                except ValueError:
                    df = pd.read_json(file_path)
            else:
                df = pd.read_csv(file_path)
            self._log_event(
                "raw_read", "success", rows=len(df), checksum=checksum, file_type=suffix
            )

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
            quality_report = self._run_quality_audit(validated_df)

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

    def ingest_http(self, url: str, headers: Optional[Dict[str, str]] = None) -> IngestionResult:

        import requests

        headers = headers or {}
        self._log_event("http_start", "initiated", url=url)

        def _do_request() -> requests.Response:
            """
            Performs a HTTP request after checking the circuit breaker and rate limiter.

            Args:
                self (UnifiedIngestion): The UnifiedIngestion object.

            Returns:
                requests.Response: The HTTP response.
            """
            if not self.circuit_breaker.allow():
                raise RuntimeError("Circuit breaker open for HTTP ingestion")
            self.rate_limiter.wait()
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response

        try:
            response = self.retry_policy.execute(
                _do_request,
                on_retry=lambda exc: self._log_event(
                    "http_retry", "retrying", error=str(exc)
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

        df = None
        # Try JSON first if headers indicate JSON or the content appears to be JSON
        is_json = "json" in content_type or content.lstrip().startswith((b"{", b"["))
        if is_json:
            try:
                stripped = content.lstrip()
                if stripped.startswith(b"["):
                    df = pd.read_json(BytesIO(content))
                else:
                    try:
                        df = pd.read_json(BytesIO(content), lines=True)
                    except ValueError:
                        df = pd.read_json(BytesIO(content))
            except Exception as exc:
                self._record_error("http_parse_json", exc, url=url)
                df = None

        if df is None:
            # Fall back to CSV parsing
            try:
                encoding = response.encoding or "utf-8"
                df = pd.read_csv(StringIO(content.decode(encoding)))
            except Exception as exc:
                self._record_error("http_parse_csv", exc, url=url)
                raise ValueError("Failed to parse HTTP response as JSON or CSV")

        # log parsed rows for observability
        try:
            self._log_event("http_parsed", "success", rows=len(df), checksum=checksum)
        except Exception:
            # Best-effort logging - do not fail
            pass

        schema_errors = self._validate_schema(df)
        validated_df, record_errors = self._validate_records(df)
        # If validation produced no validated records but original df had rows,
        # fall back to using the parsed dataframe (best-effort recovery).
        if validated_df.empty and len(df) > 0:
            self._log_event("validation", "fallback", reason="using_parsed_df", rows=len(df))

            parsed = df.copy()
            if "loan_id" not in {str(c).lower() for c in parsed.columns}:
                parsed["loan_id"] = [f"agg_{i}" for i in range(len(parsed))]
            validated_df = parsed
            record_errors = record_errors or []
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
        quality_report = self._run_quality_audit(validated_df)
        return IngestionResult(
            validated_df,
            self.run_id,
            metadata,
            source_hash=checksum,
            raw_path=None,
            quality_report=quality_report,
        )


__all__ = [
    "LoanRecord",
    "UnifiedIngestion",
]
