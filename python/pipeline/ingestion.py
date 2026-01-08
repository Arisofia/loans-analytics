import hashlib
import json
import logging
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from jsonschema import Draft202012Validator
from .utils import (CircuitBreaker, RateLimiter, RetryPolicy,
                            hash_file, utc_now, select_column)
from .validation import DataQualityReport, DataQualityReporter, validate_dataframe
from .looker import LookerConverter
from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger("abaco.ingestion")

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
        self.looker_converter = LookerConverter(config)

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

    # --- Compatibility Shims for Legacy Tests ---
    def _select_column(self, columns: List[str], candidates: List[str]) -> Optional[str]:
        return select_column(columns, candidates)

    def _load_looker_financials(self, financials_path: Optional[Path]) -> Dict[str, float]:
        return self.looker_converter.load_financials(financials_path)

    def _looker_par_balances_to_loan_tape(
        self, df: pd.DataFrame, cash_by_date: Dict[str, float]
    ) -> pd.DataFrame:
        return self.looker_converter.convert_par_balances(df, cash_by_date)

    def _looker_dpd_to_loan_tape(
        self, df: pd.DataFrame, cash_by_date: Dict[str, float]
    ) -> pd.DataFrame:
        return self.looker_converter.convert_dpd_loans(df, cash_by_date)
    # --------------------------------------------

    def _process_dataframe(
        self, df: pd.DataFrame, allow_fallback: bool = False
    ) -> Tuple[pd.DataFrame, List[str], int, DataQualityReport]:
        """Consolidate validation, deduplication, and quality audit."""
        schema_errors = self._validate_schema(df)
        validated_df, record_errors = self._validate_records(df)
        
        # Fallback logic for best-effort ingestion if requested
        if validated_df.empty and len(df) > 0 and allow_fallback:
            self._log_event("validation", "fallback", reason="using_original_df", rows=len(df))
            validated_df = df.copy()
            cols_lower = {str(c).lower() for c in validated_df.columns}
            if "loan_id" not in cols_lower:
                validated_df["loan_id"] = [f"agg_{i}" for i in range(len(validated_df))]
            record_errors = record_errors or []

        errors = schema_errors + record_errors
        
        if errors:
            self._log_event("validation", "completed", error_count=len(errors))

        self._validate_dataframe(validated_df)

        if errors and not allow_fallback and self.config.get("validation", {}).get("strict", True):
            raise ValueError(f"Schema validation failed for {len(errors)} rows")

        processed_df, deduped_count = self._apply_deduplication(validated_df)
        if deduped_count:
            self._log_event("deduplication", "completed", removed=deduped_count)

        quality_report = self._run_quality_audit(processed_df)
        return processed_df, errors, deduped_count, quality_report

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

            validated_df, errors, deduped_count, quality_report = self._process_dataframe(df)

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
            cash_by_date = self.looker_converter.load_financials(financials_path)
            columns_lower = {col.lower() for col in df.columns}
            has_par = {
                "reporting_date",
                "par_7_balance_usd",
                "par_30_balance_usd",
                "par_60_balance_usd",
                "par_90_balance_usd",
            }.issubset(columns_lower)
            has_dpd = {"dpd", "outstanding_balance"}.issubset(columns_lower) or {
                "dpd",
                "outstanding_balance_usd",
            }.issubset(columns_lower)

            if has_par:
                normalized_df = self.looker_converter.convert_par_balances(df, cash_by_date)
                source_mode = "looker_par_balances"
            elif has_dpd:
                normalized_df = self.looker_converter.convert_dpd_loans(df, cash_by_date)
                source_mode = "looker_loans"
            else:
                raise ValueError(
                    "Looker loans file missing required PAR or DPD columns for conversion"
                )
            if normalized_df.empty:
                raise ValueError("Looker loan tape conversion produced no rows")

            validated_df, errors, deduped_count, quality_report = self._process_dataframe(normalized_df)

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
                "cash_dates": len(cash_by_date),
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

        validated_df, errors, deduped_count, quality_report = self._process_dataframe(
            df, allow_fallback=True
        )

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
            validated_df,
            self.run_id,
            metadata,
            source_hash=checksum,
            raw_path=None,
            quality_report=quality_report,
        )
