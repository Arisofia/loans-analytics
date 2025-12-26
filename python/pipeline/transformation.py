import logging
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class TransformationResult:
    """Container for transformation outputs and lineage."""
    def __init__(self, df: pd.DataFrame, run_id: str, lineage: List[Dict[str, Any]]):
        self.df = df
        self.run_id = run_id
        self.lineage = lineage
        self.timestamp = datetime.now(timezone.utc).isoformat()

class UnifiedTransformation:
    """Phase 2: Data Transformation and PII Masking."""

    PII_KEYWORDS = ["name", "email", "phone", "address", "ssn", "tin", "identifier", "id_number"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("pipeline", {}).get("phases", {}).get("transformation", {})
        self.run_id = f"tx_{uuid.uuid4().hex[:12]}"
        self.lineage: List[Dict[str, Any]] = []

    def _log_step(self, step: str, status: str, **details: Any) -> None:
        entry = {
            "run_id": self.run_id,
            "step": step,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        }
        self.lineage.append(entry)
        logger.info(f"[Transformation:{step}] {status} | {details}")

    def _mask_value(self, value: Any) -> str:
        if pd.isnull(value):
            return value
        text = str(value)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"MASKED:{digest[:8]}"

    def _apply_pii_masking(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Identify and mask PII columns based on keywords."""
        if not self.config.get("pii_masking", {}).get("enabled", True):
            return df, []

        masked_df = df.copy()
        lowered_cols = [c.lower() for c in masked_df.columns]
        pii_cols = []

        for col in masked_df.columns:
            if any(key in col.lower() for key in self.PII_KEYWORDS):
                masked_df[col] = masked_df[col].apply(self._mask_value)
                pii_cols.append(col)

        return masked_df, pii_cols

    def transform(self, df: pd.DataFrame) -> TransformationResult:
        """Execute the transformation phase."""
        self._log_step("start", "initiated", input_rows=len(df))

        try:
            # Phase 2.1: Normalization
            clean_df = df.copy()
            if self.config.get("normalization", {}).get("lowercase_columns", True):
                clean_df.columns = [c.lower().strip() for c in clean_df.columns]
            
            self._log_step("normalization", "success", columns=list(clean_df.columns))

            # Phase 2.2: PII Masking
            clean_df, masked_cols = self._apply_pii_masking(clean_df)
            self._log_step("pii_masking", "completed", masked_columns=masked_cols)

            # Phase 2.3: Derived Columns (Initial Ratios)
            # Add placeholders for future derived logic if needed
            
            clean_df["_tx_run_id"] = self.run_id
            clean_df["_tx_timestamp"] = datetime.now(timezone.utc).isoformat()

            self._log_event = self._log_step # Compatibility with existing audit log patterns
            self._log_step("complete", "success", output_rows=len(clean_df))
            
            return TransformationResult(clean_df, self.run_id, self.lineage)

        except Exception as e:
            self._log_step("fatal_error", "failed", error=str(e))
            raise
