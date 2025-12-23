import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from python.validation import (NUMERIC_COLUMNS, assert_dataframe_schema,
                               validate_dataframe)

logger = logging.getLogger(__name__)


class CascadeIngestion:
    def __init__(self, data_dir: str = ".", strict_validation: bool = False):
        """
        CascadeIngestion handles CSV ingestion and validation.
        Args:
            data_dir (str): Directory for input files. Defaults to current directory.
            strict_validation (bool): If True, fail ingestion on schema/type issues instead of warning.
        Notes:
            - DataFrame returned by validate_loans will be mutated (adds _validation_passed column).
            - ingest_csv returns an empty DataFrame on error; check self.errors for details.
        """
        self.data_dir = Path(data_dir)
        self.run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.strict_validation = strict_validation
        self.errors: List[Dict[str, Any]] = []
        self._summary: Dict[str, Any] = {}
        self.raw_files: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}

    def set_context(self, **context: Any) -> None:
        for key, value in context.items():
            if value is not None:
                self.context[key] = value

    def _log_step(self, stage: str, message: str, **details: Any) -> None:
        detail_parts = [f"{key}={value!r}" for key, value in details.items() if value is not None]
        context_parts = [
            f"{key}={value!r}" for key, value in self.context.items() if value is not None
        ]
        segments = [f"[{stage}]", message]
        if detail_parts:
            segments.append(", ".join(detail_parts))
        if context_parts:
            segments.append(f"context({', '.join(context_parts)})")
        logger.info(" | ".join(segments))

    def _collect_context(self) -> Dict[str, Any]:
        return {key: value for key, value in self.context.items() if value is not None}

    def _update_summary(self, count: int, filename: Optional[str] = None) -> None:
        self._summary.setdefault("rows_ingested", 0)
        self._summary["rows_ingested"] = count
        if filename:
            self._summary.setdefault("files", {})
            self._summary["files"][filename] = count

    def _record_raw_file(
        self,
        file_path: Path,
        rows: Optional[int] = None,
        status: str = "ingested",
        message: Optional[str] = None,
    ) -> None:
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

    def _validate_input_schema(self, df: pd.DataFrame, file_path: Path) -> bool:
        missing = [col for col in NUMERIC_COLUMNS if col not in df.columns]
        if missing:
            message = f"Missing required numeric columns: {missing}"
            self.record_error(
                "ingestion_validation", message, file=str(file_path), missing_columns=missing
            )
            self._record_raw_file(file_path, rows=len(df), status="invalid_schema", message=message)
            self._log_step(
                (
                    "ingestion:validation_failed"
                    if self.strict_validation
                    else "ingestion:validation_warning"
                ),
                (
                    "Input schema validation failed"
                    if self.strict_validation
                    else "Input schema missing columns (warning)"
                ),
                file=str(file_path),
                missing_columns=missing,
            )
            return not self.strict_validation
        self._log_step(
            "ingestion:validation", "Required numeric columns present", file=str(file_path)
        )
        return True

    def ingest_csv(self, filename: str) -> pd.DataFrame:
        """
        Ingest a CSV file. Returns an empty DataFrame on error, but details are always appended to self.errors.
        Callers should check self.errors to distinguish between missing file, empty file, or parse error.
        """
        file_path = self.data_dir / filename
        self._log_step("ingestion:start", "Starting CSV ingestion", file=str(file_path))
        try:
            if not file_path.exists():
                message = f"No such file or directory: {filename}"
                self.record_error("ingestion", message, file=filename)
                self._record_raw_file(file_path, rows=0, status="missing", message=message)
                self._log_step(
                    "ingestion:missing", "File not found", file=str(file_path), error=message
                )
                return pd.DataFrame()
            df = pd.read_csv(file_path)
            self._log_step(
                "ingestion:file_read", "Parsed CSV file", file=str(file_path), rows=len(df)
            )
            self._update_summary(len(df), filename)
            if not self._validate_input_schema(df, file_path):
                return pd.DataFrame()
            try:
                assert_dataframe_schema(
                    df,
                    required_columns=NUMERIC_COLUMNS,
                    numeric_columns=NUMERIC_COLUMNS,
                    stage="ingestion",
                )
            except AssertionError as error:
                message = str(error)
                self.record_error("ingestion_schema_assertion", message, file=str(file_path))
                self._record_raw_file(
                    file_path, rows=len(df), status="invalid_schema", message=message
                )
                self._log_step(
                    "ingestion:assertion_failed",
                    "Schema assertion failed",
                    file=str(file_path),
                    error=message,
                )
                return pd.DataFrame()
            df["_ingest_run_id"] = self.run_id
            df["_ingest_timestamp"] = self.timestamp
            self._record_raw_file(file_path, rows=len(df), status="ingested")
            self._log_step(
                "ingestion:completed", "CSV ingestion complete", file=str(file_path), rows=len(df)
            )
            return df
        except pd.errors.EmptyDataError:
            message = "File is empty or malformed"
            self.record_error("ingestion", message, file=filename)
            self._record_raw_file(file_path, rows=0, status="empty", message=message)
            self._log_step(
                "ingestion:empty", "Empty or malformed CSV", file=str(file_path), error=message
            )
            return pd.DataFrame()
        except Exception as error:
            message = str(error)
            self.record_error("ingestion", message, file=filename)
            self._record_raw_file(file_path, rows=0, status="error", message=message)
            self._log_step(
                "ingestion:error", "Unexpected ingestion error", file=str(file_path), error=message
            )
            return pd.DataFrame()

    def ingest_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ingest a DataFrame directly (e.g. from tests or memory)."""
        self._log_step("ingestion:inmemory", "Starting in-memory ingestion", rows=len(df))
        self._update_summary(len(df))
        df = df.copy()
        try:
            assert_dataframe_schema(
                df,
                required_columns=NUMERIC_COLUMNS,
                numeric_columns=NUMERIC_COLUMNS,
                stage="ingestion_inmemory",
            )
        except (ValueError, TypeError) as error:
            message = str(error)
            self.record_error("ingestion", message)
            self._log_step(
                "ingestion:error",
                "In-memory ingestion validation failed",
                error=message,
                rows=len(df),
            )
            return df
        df["_ingest_run_id"] = self.run_id
        df["_ingest_timestamp"] = self.timestamp
        self._record_raw_file(
            Path("<dataframe>"), rows=len(df), status="ingested", message="in-memory ingestion"
        )
        self._log_step("ingestion:completed", "In-memory ingestion recorded", rows=len(df))
        return df

    def validate_loans(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate loan DataFrame and add a '_validation_passed' column.
    
        WARNING: This function mutates the input DataFrame by adding the '_validation_passed' column.
        If you do not want the input DataFrame to be changed, pass a copy (e.g., df.copy()) instead.
    
        Enforces:
            - Numeric columns are present and non-negative
            - Percentage columns are between 0 and 100
            - Date columns are valid ISO 8601
            - Monotonicity for count/total/cumulative columns
            - No nulls in required/numeric columns
        """
        from python.validation import (validate_iso8601_dates,
                                       validate_monotonic_increasing,
                                       validate_no_nulls,
                                       validate_numeric_bounds,
                                       validate_percentage_bounds)
    
        if df.empty:
            self._log_step("validation:skip", "Skipping validation for empty DataFrame")
            return df
    
        # Ensure chronological order for monotonicity checks
        working_df = df.copy()
        if "measurement_date" in working_df.columns:
            working_df = working_df.sort_values("measurement_date", ascending=True).reset_index(drop=True)
    
        working_df["_validation_passed"] = True
        self._log_step("validation:start", "Validating loan records", rows=len(working_df))
        try:
            assert_dataframe_schema(
                working_df,
                required_columns=NUMERIC_COLUMNS,
                numeric_columns=NUMERIC_COLUMNS,
                stage="validation",
            )
            present_cols = [col for col in NUMERIC_COLUMNS if col in working_df.columns]
            missing_cols = [col for col in NUMERIC_COLUMNS if col not in working_df.columns]
            if present_cols:
                validate_dataframe(working_df, numeric_columns=present_cols)
            if missing_cols:
                validate_dataframe(working_df, required_columns=NUMERIC_COLUMNS)
            numeric_results = validate_numeric_bounds(working_df, present_cols)
            for col, ok in numeric_results.items():
                if not ok:
                    raise ValueError(f"Column failed positivity check: {col}")
            pct_results = validate_percentage_bounds(working_df)
            for col, ok in pct_results.items():
                if not ok:
                    raise ValueError(f"Column failed percentage bounds check: {col}")
            iso_results = validate_iso8601_dates(working_df)
            for col, ok in iso_results.items():
                if not ok:
                    raise ValueError(f"Column failed ISO 8601 date check: {col}")
            mono_results = validate_monotonic_increasing(working_df)
            for col, ok in mono_results.items():
                if not ok:
                    raise ValueError(f"Column failed monotonicity check: {col}")
            null_results = validate_no_nulls(working_df)
            for col, ok in null_results.items():
                if not ok:
                    raise ValueError(f"Column failed null check: {col}")
            self._log_step("validation:success", "Validation succeeded", rows=len(working_df))
        except (AssertionError, ValueError, TypeError) as error:
            message = str(error)
            found_col = None
            for col in NUMERIC_COLUMNS:
                if col in message:
                    found_col = col
                    break
            # Always include the column name in the error message if found
            if found_col and f"'{found_col}'" not in message:
                message = f"Validation error in column '{found_col}': {message}"
            elif not found_col:
                for col in NUMERIC_COLUMNS:
                    if col in working_df.columns and not pd.api.types.is_numeric_dtype(working_df[col]):
                        message = f"Validation error in column '{col}': {message}"
                        break
            # Use correct error stage for schema/type errors
            if "schema" in message or "must be numeric" in message or "non-numeric" in message or "missing required" in message:
                self.record_error("validation_schema_assertion", message)
            else:
                self.record_error("validation", message)
            working_df["_validation_passed"] = False
            self._log_step("validation:failure", "Validation failed", error=message, rows=len(working_df))
            # Always set _validation_passed to False on error
            working_df["_validation_passed"] = False
            # If exception is raised, still return mutated DataFrame if possible
            return working_df
        return working_df

    def get_ingest_summary(self) -> Dict[str, Any]:
        summary = self._summary.copy()
        summary.update(
            {
                "run_id": self.run_id,
                "timestamp": self.timestamp,
                "total_errors": len(self.errors),
                "errors": self.errors,
                "raw_files": self.raw_files,
                "context": self.context.copy(),
            }
        )
        return summary

    def record_error(self, stage: str, message: str, **details: Any) -> None:
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
