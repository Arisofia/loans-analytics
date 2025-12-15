import pandas as pd
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from python.validation import validate_dataframe, NUMERIC_COLUMNS

class CascadeIngestion:
    def __init__(self, data_dir: str = "."):
        """
        CascadeIngestion handles CSV ingestion and validation.
        Args:
            data_dir (str): Directory for input files. Defaults to current directory.
        Notes:
            - DataFrame returned by validate_loans will be mutated (adds _validation_passed column).
            - ingest_csv returns an empty DataFrame on error; check self.errors for details.
        """
        self.data_dir = Path(data_dir)
        self.run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.errors: List[Dict[str, Any]] = []
        self._summary: Dict[str, Any] = {}

    def _update_summary(self, count: int, filename: str = None) -> None:
        self._summary.setdefault("rows_ingested", 0)
        self._summary["rows_ingested"] += count
        if filename:
            self._summary.setdefault("files", {})
            self._summary["files"].setdefault(filename, 0)
            self._summary["files"][filename] += count

    def ingest_csv(self, filename: str) -> pd.DataFrame:
        """
        Ingest a CSV file. Returns an empty DataFrame on error, but details are always appended to self.errors.
        Callers should check self.errors to distinguish between missing file, empty file, or parse error.
        """
        try:
            file_path = self.data_dir / filename
            if not file_path.exists():
                self.errors.append({
                    "file": filename,
                    "error": f"No such file or directory: {filename}",
                    "timestamp": self.timestamp,
                    "run_id": self.run_id,
                    "stage": "ingestion"
                })
                return pd.DataFrame()
            df = pd.read_csv(file_path)
            self._update_summary(len(df), filename)
            df["_ingest_run_id"] = self.run_id
            df["_ingest_timestamp"] = self.timestamp
            return df
        except pd.errors.EmptyDataError:
            self.errors.append({
                "file": filename,
                "error": "File is empty or malformed",
                "timestamp": self.timestamp,
                "run_id": self.run_id,
                "stage": "ingestion"
            })
            return pd.DataFrame()
        except Exception as e:
            self.errors.append({
                "file": filename,
                "error": str(e),
                "timestamp": self.timestamp,
                "run_id": self.run_id,
                "stage": "ingestion"
            })
            return pd.DataFrame()

    def ingest_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ingest a DataFrame directly (e.g. from tests or memory)."""
        self._update_summary(len(df))
        
        df = df.copy()
        df["_ingest_run_id"] = self.run_id
        df["_ingest_timestamp"] = self.timestamp
        return df

    def validate_loans(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate loan DataFrame and add a '_validation_passed' column.
        Note: This mutates the input DataFrame by adding a column. Callers should copy if mutation is not desired.
        Enforces:
          - Numeric columns are present and non-negative
          - Percentage columns are between 0 and 100
          - Date columns are valid ISO 8601
          - Monotonicity for count/total/cumulative columns
          - No nulls in required/numeric columns
        """
        from python.validation import (
            validate_numeric_bounds, validate_percentage_bounds, validate_iso8601_dates,
            validate_monotonic_increasing, validate_no_nulls
        )
        if df.empty:
            return df
        df["_validation_passed"] = True
        try:
            present_cols = [col for col in NUMERIC_COLUMNS if col in df.columns]
            missing_cols = [col for col in NUMERIC_COLUMNS if col not in df.columns]
            if present_cols:
                validate_dataframe(df, numeric_columns=present_cols)
            if missing_cols:
                validate_dataframe(df, required_columns=NUMERIC_COLUMNS)
            # Numeric positivity check
            numeric_results = validate_numeric_bounds(df, present_cols)
            for col, ok in numeric_results.items():
                if not ok:
                    raise ValueError(f"Column failed positivity check: {col}")
            # Percentage bounds check
            pct_results = validate_percentage_bounds(df)
            for col, ok in pct_results.items():
                if not ok:
                    raise ValueError(f"Column failed percentage bounds check: {col}")
            # ISO 8601 date check
            iso_results = validate_iso8601_dates(df)
            for col, ok in iso_results.items():
                if not ok:
                    raise ValueError(f"Column failed ISO 8601 date check: {col}")
            # Monotonicity check
            mono_results = validate_monotonic_increasing(df)
            for col, ok in mono_results.items():
                if not ok:
                    raise ValueError(f"Column failed monotonicity check: {col}")
            # Null check
            null_results = validate_no_nulls(df)
            for col, ok in null_results.items():
                if not ok:
                    raise ValueError(f"Column failed null check: {col}")
        except ValueError as e:
            msg = str(e)
            found_col = None
            for col in NUMERIC_COLUMNS:
                if col in msg:
                    found_col = col
                    break
            if found_col:
                msg = f"Validation error in column '{found_col}': {msg}"
            else:
                for col in NUMERIC_COLUMNS:
                    if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                        msg = f"Validation error in column '{col}': {msg}"
                        break
            self.record_error("validation", msg)
            df["_validation_passed"] = False
        return df

    def get_ingest_summary(self) -> Dict[str, Any]:
        summary = self._summary.copy()
        summary.update({
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "total_errors": len(self.errors),
            "errors": self.errors
        })
        return summary

    def record_error(self, stage: str, message: str):
        self.errors.append({"stage": stage, "error": message, "timestamp": self.timestamp, "run_id": self.run_id})