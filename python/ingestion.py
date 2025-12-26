import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from python.validation import NUMERIC_COLUMNS, validate_dataframe

logger = logging.getLogger(__name__)


class CascadeIngestion:
    """Legacy-compatible ingestion wrapper with hardened validation."""

    def __init__(self, data_dir: Optional[str] = None, strict_validation: bool = False):
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.strict_validation = strict_validation
        self.run_id = f"ingest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.errors: List[Dict[str, Any]] = []
        self.raw_files: List[Dict[str, Any]] = []
        self._summary = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "rows_ingested": 0,
            "files": {},
        }

    def _record_error(self, stage: str, message: str, **details: Any) -> None:
        payload = {
            "stage": stage,
            "error": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            **details,
        }
        self.errors.append(payload)
        logger.error("[CascadeIngestion:%s] %s", stage, payload)

    def _update_summary(self, rows: int, filename: Optional[str] = None) -> None:
        self._summary["rows_ingested"] += rows
        if filename:
            files = self._summary.setdefault("files", {})
            files[filename] = files.get(filename, 0) + rows

    def ingest_csv(self, filename: str) -> pd.DataFrame:
        file_path = self.data_dir / filename
        if not file_path.exists():
            self._record_error("ingestion_file", f"No such file: {file_path}", file=filename)
            return pd.DataFrame()
        if file_path.stat().st_size == 0:
            self._record_error("ingestion_file", f"Empty file: {file_path}", file=filename)
            return pd.DataFrame()

        df = pd.read_csv(file_path)
        df["_ingest_run_id"] = self.run_id
        df["_ingest_timestamp"] = datetime.now(timezone.utc).isoformat()

        self.raw_files.append(
            {
                "file": filename,
                "status": "ingested",
                "rows": len(df),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._update_summary(len(df), filename)

        validated = self.validate_loans(df)
        if self.strict_validation and not bool(validated.get("_validation_passed", True).all()):
            error_message = "Validation failed"
            if self.errors:
                error_message = self.errors[-1].get("error", error_message)
            payload = {
                "stage": "ingestion_validation",
                "error": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "run_id": self.run_id,
                "file": filename,
            }
            self.errors.insert(0, payload)
            logger.error("[CascadeIngestion:ingestion_validation] %s", payload)
            return pd.DataFrame()

        return validated

    def ingest_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["_ingest_run_id"] = self.run_id
        df["_ingest_timestamp"] = datetime.now(timezone.utc).isoformat()
        self._update_summary(len(df))
        return df

    def validate_loans(self, df: pd.DataFrame) -> pd.DataFrame:
        validated = df.copy()
        missing_numeric = [col for col in NUMERIC_COLUMNS if col not in validated.columns]
        if missing_numeric:
            message = f"Missing required numeric columns: {', '.join(missing_numeric)}"
            validated["_validation_passed"] = False
            self._record_error("validation_schema_assertion", message)
            return validated
        try:
            validate_dataframe(
                validated,
                required_columns=NUMERIC_COLUMNS,
                numeric_columns=NUMERIC_COLUMNS,
                date_columns=["measurement_date"],
            )
            validated["_validation_passed"] = True
        except ValueError as exc:
            validated["_validation_passed"] = False
            self._record_error("validation_schema_assertion", str(exc))
        return validated

    def get_ingest_summary(self) -> Dict[str, Any]:
        return {
            **self._summary,
            "total_errors": len(self.errors),
            "errors": list(self.errors),
        }
