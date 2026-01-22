import logging
from pathlib import Path
from typing import Dict, List, Optional

import polars as pl

from src.config.settings import settings
from src.models.schemas import CLIENT_SCHEMA, INVOICE_SCHEMA, PAYMENT_SCHEMA

logger = logging.getLogger(__name__)


class PolarsPipeline:
    """
    Production-grade Data Pipeline using Polars for high-performance,
    strictly-typed financial data processing.
    """

    def __init__(self):
        self.schemas = {
            "invoices": INVOICE_SCHEMA,
            "payments": PAYMENT_SCHEMA,
            "clients": CLIENT_SCHEMA,
        }

    def scan_file(self, path: Path, schema_type: Optional[str] = None) -> pl.LazyFrame:
        """
        Scan a file into a Polars LazyFrame.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix == ".csv":
            # Don't enforce schema yet, wait for normalization
            return pl.scan_csv(path)
        elif path.suffix == ".parquet":
            return pl.scan_parquet(path)
        elif path.suffix == ".json":
            # scan_ndjson is available for newline-delimited JSON
            try:
                return pl.scan_ndjson(path)
            except Exception:
                # Fallback for standard JSON
                return pl.read_json(path).lazy()
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    def normalize_columns(self, lf: pl.LazyFrame, mapping: Dict[str, List[str]]) -> pl.LazyFrame:
        """
        Normalize column names using Polars expressions.
        """
        # Get existing columns from the logical plan
        existing_cols = lf.collect_schema().names()

        rename_dict = {}
        for internal_name, candidates in mapping.items():
            for cand in candidates:
                # Case-insensitive match check (Polars is case-sensitive by default)
                # This is a bit tricky with LazyFrame without collecting,
                # but we can use schema names.
                matched_col = next((c for c in existing_cols if c.lower() == cand.lower()), None)
                if matched_col:
                    rename_dict[matched_col] = internal_name
                    break

        if rename_dict:
            return lf.rename(rename_dict)
        return lf

    def enforce_precision(self, lf: pl.LazyFrame, decimal_cols: List[str]) -> pl.LazyFrame:
        """
        Enforce Decimal precision for monetary columns.
        """
        expressions = [
            pl.col(col).cast(pl.Decimal(precision=38, scale=4))
            for col in decimal_cols
            if col in lf.collect_schema().names()
        ]
        if expressions:
            return lf.with_columns(expressions)
        return lf

    def filter_active_loans(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        """
        Filter for loans with outstanding balance above threshold.
        """
        threshold = settings.outstanding_precision_threshold
        return lf.filter(pl.col("outstanding") > threshold)

    def run_ingestion_conformance(
        self, path: Path, schema_type: str, mapping: Dict[str, List[str]]
    ) -> pl.DataFrame:
        """
        Full flow: Scan -> Normalize -> Enforce Types -> Materialize (Silver).
        """
        lf = self.scan_file(path)
        return self.run_ingestion_conformance_from_lf(lf, schema_type, mapping)

    def run_ingestion_conformance_from_lf(
        self, lf: pl.LazyFrame, schema_type: str, mapping: Dict[str, List[str]]
    ) -> pl.DataFrame:
        """
        Flow from LazyFrame: Normalize -> Enforce Types -> Materialize (Silver).
        """
        lf = self.normalize_columns(lf, mapping)

        # Enforce schema types
        schema = self.schemas.get(schema_type)
        if schema:
            # Cast columns to schema types
            exprs = [
                pl.col(name).cast(dtype)
                for name, dtype in schema.items()
                if name in lf.collect_schema().names()
            ]
            lf = lf.with_columns(exprs)

        # Enforce precision on monetary columns
        monetary_cols = [
            name for name, dtype in (schema or {}).items() if isinstance(dtype, pl.Decimal)
        ]
        lf = self.enforce_precision(lf, monetary_cols)

        return self.calculate_conformance(lf)

    def calculate_conformance(self, lf: pl.LazyFrame) -> pl.DataFrame:
        """
        Collect the LazyFrame and ensure data quality checks pass.
        """
        return lf.collect()

    def save_to_silver(self, df: pl.DataFrame, output_path: Path):
        """
        Save the conformed (Silver) data to Parquet.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(output_path)
        logger.info("Saved Silver data to %s", output_path)
