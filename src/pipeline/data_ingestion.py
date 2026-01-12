import logging
from pathlib import Path
from typing import Any, Dict, Optional

import polars as pl

from src.pipeline.polars_pipeline import PolarsPipeline

logger = logging.getLogger(__name__)


class UnifiedIngestion:
    """
    Unified data ingestion phase using Polars for high performance.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.pipeline = PolarsPipeline()

    def ingest_file(self, file_path: Path, schema_type: str = "invoices") -> pl.DataFrame:
        """
        Ingest data from a file into a Polars DataFrame.
        """
        logger.info("Ingesting file with Polars: %s", file_path)
        # Using the new Polars-based pipeline for scanning
        lf = self.pipeline.scan_file(file_path, schema_type=schema_type)
        return lf.collect()
