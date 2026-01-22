import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Union

import polars as pl

from python.schemas import INGESTION_SCHEMA, validate_ingestion_contract
from python.validation import safe_numeric_polars

logger = logging.getLogger(__name__)


class AbacoIngestion:
    def __init__(self, strict_validation: bool = False):
        """
        Unified Ingestion Engine for Abaco Analytics.
        Handles both manual UI-driven uploads and automated API-driven ingestion.
        Enforces strict data contracts and performs lineage tracking via run_id.
        """
        self.run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.strict_validation = strict_validation
        self.errors: List[Dict[str, Any]] = []
        self._summary: Dict[str, Any] = {}
        self.context: Dict[str, Any] = {}

    def set_context(self, **context: Any) -> None:
        for key, value in context.items():
            if value is not None:
                self.context[key] = value

    def _log_step(self, stage: str, message: str, **details: Any) -> None:
        detail_parts = [
            f"{key}={value!r}" for key, value in details.items() if value is not None
        ]
        context_parts = [
            f"{key}={value!r}"
            for key, value in self.context.items()
            if value is not None
        ]
        segments = [f"[{stage}]", message]
        if detail_parts:
            segments.append(", ".join(detail_parts))
        if context_parts:
            segments.append(f"context({', '.join(context_parts)})")
        logger.info(" | ".join(segments))

    def _collect_context(self) -> Dict[str, Any]:
        return {key: value for key, value in self.context.items() if value is not None}

    def _update_summary(self, count: int) -> None:
        self._summary.setdefault("rows_ingested", 0)
        self._summary["rows_ingested"] += count

    def ingest_uploaded_file(
        self, file_content: Union[bytes, io.BytesIO]
    ) -> pl.DataFrame:
        """
        Ingest a file (CSV) from a bytes stream.
        Applies cleaning, schema enforcement, and contract validation.
        """
        self._log_step("ingestion:start", "Starting data ingestion processing")

        try:
            # 1. Initial Load (allow dynamic types for cleaning if needed)
            df = pl.read_csv(file_content)

            # 2. Data Cleaning (Polars-native)
            numeric_cols = [
                col
                for col, dtype in INGESTION_SCHEMA.items()
                if dtype in [pl.Float64, pl.Int64]
            ]
            df = safe_numeric_polars(df, numeric_cols)

            # 3. Strict Schema Enforcement
            df = df.cast(INGESTION_SCHEMA)

            # 4. Business Contract Validation
            validate_ingestion_contract(df)

            self._update_summary(len(df))
            self._log_step("ingestion:completed", "Ingestion complete", rows=len(df))
            return df
        except Exception as e:
            message = f"Ingestion failed: {str(e)}"
            self.record_error("ingestion_failed", message)
            return pl.DataFrame()

    def get_ingest_summary(self) -> Dict[str, Any]:
        summary = self._summary.copy()
        summary.update(
            {
                "run_id": self.run_id,
                "timestamp": self.timestamp,
                "total_errors": len(self.errors),
                "errors": self.errors,
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
