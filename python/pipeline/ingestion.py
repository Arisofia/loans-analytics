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

from python.validation import validate_dataframe
from python.pipeline.utils import CircuitBreaker, RateLimiter, RetryPolicy, hash_file, utc_now

logger = logging.getLogger(__name__)


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


class UnifiedIngestion:
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
            validated_df, record_errors = self._validate_records(df)
            errors = schema_errors + record_errors

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
            }

            self._log_event("complete", "success", row_count=len(validated_df))
            return IngestionResult(validated_df, self.run_id, metadata, source_hash=checksum, raw_path=archived)

        except Exception as exc:
            self._record_error("fatal_error", exc)
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
        }

        self._log_event("http_complete", "success", row_count=len(validated_df))
        return IngestionResult(validated_df, self.run_id, metadata, source_hash=checksum, raw_path=None)
