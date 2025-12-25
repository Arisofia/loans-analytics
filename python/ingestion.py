import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional  # <-- FIX: Use typing.Dict, typing.List, etc.

import pandas as pd

from python.validation import (
    NUMERIC_COLUMNS,
    assert_dataframe_schema,
    validate_dataframe,
    validate_numeric_bounds,
    validate_percentage_bounds,
    validate_iso8601_dates,
    validate_monotonic_increasing,
)

logger = logging.getLogger(__name__)


class CascadeIngestion:
    """CSV ingestion with validation, error tracking, and audit logging."""

    def __init__(self, data_dir: str = ".", strict_validation: bool = False):
        """
        Initialize ingestion engine.

        Args:
            data_dir: Directory for input files. Defaults to current directory.
            strict_validation: If True, fail on schema/type issues instead of warning.
        """
        self.data_dir = Path(data_dir)
        self.run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.strict_validation = strict_validation
        self.errors: List[Dict[str, Any]] = []  # FIX: Use typing.List/Dict
        self._summary: Dict[str, Any] = {}
        self.raw_files: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}

    def set_context(self, **context: Any) -> None:
        """Set contextual metadata for logging."""
        for key, value in context.items():
            if value is not None:
                self.context[key] = value

    def _log_step(self, stage: str, message: str, **details: Any) -> None:
        """Log a processing step with context."""
        detail_parts = [f"{k}={v!r}" for k, v in details.items() if v is not None]
        context_parts = [f"{k}={v!r}" for k, v in self.context.items() if v is not None]
        segments = [f"[{stage}]", message]
        if detail_parts:
            segments.append(", ".join(detail_parts))
        if context_parts:
            segments.append(f"context({', '.join(context_parts)})")
        logger.info(" | ".join(segments))

    def _collect_context(self) -> Dict[str, Any]:
        """Return non-None context values."""
        return {k: v for k, v in self.context.items() if v is not None}

    def _update_summary(self, count: int, filename: Optional[str] = None) -> None:
        """Update processing summary."""
        self._summary.setdefault("rows_ingested", 0)
        self._summary["rows_ingested"] += count
        if filename:
            self._summary.setdefault("files", {})
            self._summary["files"].setdefault(filename, 0)
            self._summary["files"][filename] += count

    def _record_raw_file(
        self,
        file_path: Path,
        rows: Optional[int] = None,
        status: str = "ingested",
        message: Optional[str] = None,
    ) -> None:
        """Track raw file processing."""
        entry: Dict[str, Any] = {
            "file": str(file_path.resolve()),
            "status": status,
            "rows": rows,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "strict_validation": self.strict_validation,
        }
        if message:
            entry["message"] = message
        entry.update(self._collect_context())
        self.raw_files.append(entry)

    def _handle_ingestion_error(
        self,
        file_path: Path,
        filename: str,
        status: str,
        message: str,
        rows: int = 0,
        **log_details
    ) -> pd.DataFrame:
        """Centralized error handling for ingestion failures."""
        self.record_error("ingestion", message, file=filename)
        self._record_raw_file(file_path, rows=rows, status=status, message=message)
        self._log_step(
            f"ingestion:{status}",
            f"Ingestion {status.replace('_', ' ')}",
            file=str(file_path),
            error=message,
            **log_details
        )
        return pd.DataFrame()

    def _validate_schema(self, df: pd.DataFrame, file_path: Path) -> bool:
        """Validate required columns present and numeric."""
        missing = [col for col in NUMERIC_COLUMNS if col not in df.columns]
        if not missing:
            self._log_step("ingestion:validation", "Required columns present", file=str(file_path))
            return True

        message = f"Missing required numeric columns: {missing}"
        level = "validation_failed" if self.strict_validation else "validation_warning"
        self._record_raw_file(file_path, rows=len(df), status="invalid_schema", message=message)
        self.record_error(
            "ingestion_validation", message, file=str(file_path), missing_columns=missing
        )
        self._log_step(
            f"ingestion:{level}",
            f"Schema validation {'failed' if self.strict_validation else 'warning'}",
            file=str(file_path),
            missing_columns=missing,
        )
        return not self.strict_validation

    def ingest_csv(self, filename: str) -> pd.DataFrame:
        """
        Ingest CSV file with validation.

        Returns empty DataFrame on error; check self.errors for details.
        """
        file_path = self.data_dir / filename
        self._log_step("ingestion:start", "Starting CSV ingestion", file=str(file_path))

        if not file_path.exists():
            return self._handle_ingestion_error(
                file_path,
                filename,
                "missing",
                f"No such file or directory: {filename}"
            )

        try:
            df = pd.read_csv(file_path)
            self._log_step("ingestion:file_read", "CSV parsed", file=str(file_path), rows=len(df))
            self._update_summary(len(df), filename)

            if not self._validate_schema(df, file_path):
                return pd.DataFrame()

            assert_dataframe_schema(
                df,
                required_columns=NUMERIC_COLUMNS,
                numeric_columns=NUMERIC_COLUMNS,
                stage="ingestion",
            )

            df["_ingest_run_id"] = self.run_id
            df["_ingest_timestamp"] = self.timestamp
            self._record_raw_file(file_path, rows=len(df), status="ingested")
            self._log_step(
                "ingestion:completed",
                "CSV ingestion complete",
                file=str(file_path),
                rows=len(df),
            )
            return df

        except pd.errors.EmptyDataError:
            return self._handle_ingestion_error(
                file_path,
                filename,
                "empty",
                "File is empty or malformed"
            )
        except AssertionError as e:
            return self._handle_ingestion_error(
                file_path,
                filename,
                "invalid_schema",
                str(e),
                rows=len(df) if 'df' in locals() else 0
            )
        except Exception as e:
            return self._handle_ingestion_error(
                file_path,
                filename,
                "error",
                str(e)
            )

    def ingest_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ingest DataFrame directly."""
        self._log_step("ingestion:inmemory", "In-memory ingestion", rows=len(df))
        self._update_summary(len(df))

        df = df.copy()
        assert_dataframe_schema(
            df,
            required_columns=NUMERIC_COLUMNS,
            numeric_columns=NUMERIC_COLUMNS,
            stage="ingestion_inmemory",
        )

        df["_ingest_run_id"] = self.run_id
        df["_ingest_timestamp"] = self.timestamp
        self._record_raw_file(Path("<dataframe>"), rows=len(df), status="ingested")
        self._log_step("ingestion:completed", "In-memory ingestion recorded", rows=len(df))
        return df

    def validate_loans(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate loan DataFrame and add '_validation_passed' column.

        Validates:
        - Numeric columns are present and non-negative
        - Percentage columns are between 0 and 100
        - Date columns are valid ISO 8601
        - Monotonic increasing for count/cumulative columns
        - No nulls in required columns
        """
        if df.empty:
            self._log_step("validation:skip", "Skipping empty DataFrame")
            return df

        if "measurement_date" in df.columns:
            df = df.sort_values("measurement_date", ascending=True).reset_index(drop=True)

        df["_validation_passed"] = True
        self._log_step("validation:start", "Validating loan records", rows=len(df))

        try:
            assert_dataframe_schema(
                df,
                required_columns=NUMERIC_COLUMNS,
                numeric_columns=NUMERIC_COLUMNS,
                stage="validation",
            )

            present_cols = [col for col in NUMERIC_COLUMNS if col in df.columns]
            validate_dataframe(df, numeric_columns=present_cols)

            for col, ok in validate_numeric_bounds(df, present_cols).items():
                if not ok:
                    raise ValueError(f"Column failed positivity check: {col}")

            for col, ok in validate_percentage_bounds(df).items():
                if not ok:
                    raise ValueError(f"Column failed percentage bounds: {col}")

            for col, ok in validate_iso8601_dates(df).items():
                if not ok:
                    raise ValueError(f"Column failed ISO 8601 check: {col}")

            for col, ok in validate_monotonic_increasing(df).items():
                if not ok:
                    raise ValueError(f"Column failed monotonicity check: {col}")

            for col, ok in validate_no_nulls(df).items():
                if not ok:
                    raise ValueError(f"Column failed null check: {col}")

            self._log_step("validation:success", "Validation passed", rows=len(df))

        except (AssertionError, ValueError) as e:
            message = str(e)
            found_col = None
            for col in NUMERIC_COLUMNS:
                if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                    found_col = col
                    break
            if found_col and f"'{found_col}'" not in message:
                message = f"Validation error in column '{found_col}': {message}"

            is_schema_error = (
                "schema" in message.lower()
                or "must be numeric" in message.lower()
                or "missing required" in message.lower()
            )
            if is_schema_error:
                self.record_error("validation_schema_assertion", message)
            else:
                self.record_error("validation", message)
            df["_validation_passed"] = False
            self._log_step("validation:failure", "Validation failed", error=message, rows=len(df))

        return df

    def get_ingest_summary(self) -> Dict[str, Any]:
        """Get processing summary."""
        summary = self._summary.copy()
        summary.update({
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "total_errors": len(self.errors),
            "errors": self.errors,
            "raw_files": self.raw_files,
            "context": self.context.copy(),
        })
        return summary

    def record_error(self, stage: str, message: str, **details: Any) -> None:
        """Record an error event."""
        entry: Dict[str, Any] = {
            "stage": stage,
            "error": message,
            "timestamp": self.timestamp,
            "run_id": self.run_id,
        }
        entry.update(details)
        entry.update(self._collect_context())
        self.errors.append(entry)
        logger.error("%s error (run=%s): %s", stage, self.run_id, message)

def _raise_for_failed_columns(results, error_message):
    """Raise ValueError for any failed validation in results dict."""
    for col, ok in results.items():
        if not ok:
            raise ValueError(f"{error_message}: {col}")

def _run_validations(df):
    present_cols = [col for col in NUMERIC_COLUMNS if col in df.columns]
    validate_dataframe(df, numeric_columns=present_cols)
    validations = [
        (validate_numeric_bounds, present_cols, "Column failed positivity check"),
        (validate_percentage_bounds, None, "Column failed percentage bounds"),
        (validate_iso8601_dates, None, "Column failed ISO 8601 check"),
        (validate_monotonic_increasing, None, "Column failed monotonicity check"),
        (validate_no_nulls, None, "Column contains nulls"),
    ]
    for func, cols, msg in validations:
        args = (df, cols) if cols is not None else (df,)
        _raise_for_failed_columns(func(*args), msg)

def validate_loans(df):
    """
    Validate the loans DataFrame for schema, numeric, percentage, date, monotonicity, and null checks.
    Raises ValueError on first failure.
    """
    _run_validations(df)
    if len(df) == 0:
        raise ValueError("DataFrame is empty")
    return df
