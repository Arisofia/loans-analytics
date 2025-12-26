import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd

from python.validation import NUMERIC_COLUMNS, validate_dataframe

logger = logging.getLogger(__name__)


class DataTransformation:
    """Legacy-compatible transformation wrapper for KPI datasets."""

    def __init__(self):
        self._lineage: List[Dict[str, Any]] = []
        self._summary: Dict[str, Any] = {
            "started_at": datetime.now(timezone.utc).isoformat()
        }

    def transform_to_kpi_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            raise ValueError("Missing required columns: empty dataset")

        missing = [col for col in NUMERIC_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        validate_dataframe(
            df,
            required_columns=NUMERIC_COLUMNS,
            numeric_columns=NUMERIC_COLUMNS,
            date_columns=["measurement_date"],
        )

        transformed = df.copy()
        self._lineage.append(
            {
                "event": "transform_to_kpi_dataset",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rows": len(transformed),
            }
        )
        self._summary.update({"rows_processed": len(transformed)})
        return transformed

    def get_processing_summary(self) -> Dict[str, Any]:
        return dict(self._summary)

    def get_lineage(self) -> List[Dict[str, Any]]:
        return list(self._lineage)
