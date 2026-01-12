import logging
from typing import Any, Dict, Optional

import polars as pl

from src.pipeline.polars_pipeline import PolarsPipeline
from src.utils.data_normalization import COLUMN_MAPPING

logger = logging.getLogger(__name__)


class UnifiedTransformation:
    """Unified data transformation phase using Polars."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.pipeline = PolarsPipeline()

    def transform(self, df: pl.DataFrame, schema_type: str = "invoices") -> pl.DataFrame:
        """Apply transformations to the Polars DataFrame."""
        logger.info("Transforming Polars DataFrame with %d rows", len(df))
        lf = df.lazy()

        # Use PolarsPipeline's conformed flow for normalization and type enforcement
        return self.pipeline.run_ingestion_conformance_from_lf(lf, schema_type, COLUMN_MAPPING)
