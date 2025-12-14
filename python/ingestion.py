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

    def ingest_csv(self, filename: str) -> pd.DataFrame:
        try:
            file_path = self.data_dir / filename
            if not file_path.exists():
                 self._record_error("ingestion", f"File not found: {filename}")
                 return pd.DataFrame()
            
            df = pd.read_csv(file_path)
            # Coderabbit: Accumulate total rows ingested and track per-file ingestion count
            if "rows_ingested" not in self._summary:
                self._summary["rows_ingested"] = 0
            self._summary["rows_ingested"] += len(df)
            if "files" not in self._summary:
                self._summary["files"] = {}
            self._summary["files"][filename] = len(df)
            
            # Add ingestion metadata
            df["_ingest_run_id"] = self.run_id
            df["_ingest_timestamp"] = self.timestamp
            return df
        except Exception as e:
            self._record_error("ingestion", str(e))
            return pd.DataFrame()

    def ingest_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ingest a DataFrame directly (e.g. from tests or memory)."""
        if "rows_ingested" not in self._summary:
            self._summary["rows_ingested"] = 0
        self._summary["rows_ingested"] += len(df)
        
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
            # Validate presence of critical numeric columns for KPIs
            validate_dataframe(df, required_columns=NUMERIC_COLUMNS)
        except ValueError as e:
            self._record_error("validation", str(e))
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
        self.errors.append({"stage": stage, "message": message})