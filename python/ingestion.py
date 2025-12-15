import pandas as pd
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from python.validation import validate_dataframe, NUMERIC_COLUMNS

class CascadeIngestion:
    def __init__(self, data_dir: str = "."):
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
            self._summary["files"][filename] = count

    def ingest_csv(self, filename: str) -> pd.DataFrame:
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
            # Coderabbit: Accumulate total rows ingested and track per-file ingestion count
            self._update_summary(len(df), filename)
            # Add ingestion metadata
            df["_ingest_run_id"] = self.run_id
            df["_ingest_timestamp"] = self.timestamp
            return df
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
        if df.empty:
            return df
        # Add validation flag
        df["_validation_passed"] = True
        try:
            present_cols = [col for col in NUMERIC_COLUMNS if col in df.columns]
            missing_cols = [col for col in NUMERIC_COLUMNS if col not in df.columns]
            # First, check numeric types for present columns
            if present_cols:
                validate_dataframe(df, numeric_columns=present_cols)
            # Then, check for missing columns
            if missing_cols:
                validate_dataframe(df, required_columns=NUMERIC_COLUMNS)
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
            self._record_error("validation", msg)
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

    def _record_error(self, stage: str, message: str):
        self.errors.append({"stage": stage, "error": message, "timestamp": self.timestamp, "run_id": self.run_id})