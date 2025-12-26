import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

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

class IngestionResult:
    """Container for ingestion outputs and metadata."""
    def __init__(self, df: pd.DataFrame, run_id: str, metadata: Dict[str, Any]):
        self.df = df
        self.run_id = run_id
        self.metadata = metadata
        self.timestamp = datetime.now(timezone.utc).isoformat()

class UnifiedIngestion:
    """Phase 1: Robust Ingestion with validation and auditability."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("pipeline", {}).get("phases", {}).get("ingestion", {})
        self.run_id = f"ingest_{uuid.uuid4().hex[:12]}"
        self.audit_log: List[Dict[str, Any]] = []

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of the input file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _log_event(self, event: str, status: str, **details: Any) -> None:
        entry = {
            "run_id": self.run_id,
            "event": event,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        }
        self.audit_log.append(entry)
        logger.info(f"[Ingestion:{event}] {status} | {details}")

    def ingest_file(self, file_path: Path) -> IngestionResult:
        """Execute the ingestion phase for a local file."""
        self._log_event("start", "initiated", file_path=str(file_path))
        
        if not file_path.exists():
            self._log_event("file_check", "failed", error="File not found")
            raise FileNotFoundError(f"Input file not found: {file_path}")

        checksum = self._calculate_checksum(file_path)
        
        try:
            # Phase 1.1: Raw Read
            df = pd.read_csv(file_path)
            self._log_event("raw_read", "success", rows=len(df), checksum=checksum)

            # Phase 1.2: Schema Validation (Pydantic)
            records = df.to_dict(orient="records")
            validated_records = []
            errors = []

            for i, record in enumerate(records):
                try:
                    # Clean column names for Pydantic alias mapping
                    clean_record = {k.strip().lower(): v for k, v in record.items()}
                    
                    # Handle missing loan_id for aggregate/portfolio files
                    if 'loan_id' not in clean_record and 'loan_id' not in record:
                        clean_record['loan_id'] = f"agg_{i}"
                    
                    validated_records.append(LoanRecord(**clean_record).model_dump(by_alias=True))
                except ValidationError as e:
                    errors.append({"row": i, "error": str(e)})


            if errors and self.config.get("validation", {}).get("strict", True):
                self._log_event("validation", "failed", error_count=len(errors))
                raise ValueError(f"Schema validation failed for {len(errors)} rows.")

            validated_df = pd.DataFrame(validated_records)
            
            metadata = {
                "source_file": str(file_path),
                "checksum": checksum,
                "row_count": len(validated_df),
                "error_count": len(errors),
                "audit_log": self.audit_log
            }

            self._log_event("complete", "success", row_count=len(validated_df))
            return IngestionResult(validated_df, self.run_id, metadata)

        except Exception as e:
            self._log_event("fatal_error", "failed", error=str(e))
            raise
