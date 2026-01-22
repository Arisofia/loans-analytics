from datetime import datetime
from pathlib import Path

import polars as pl
from prefect import flow, task

from src.pipeline.data_validation import DataValidator
from src.pipeline.event_store import EventStore
from src.pipeline.polars_pipeline import PolarsPipeline
from src.utils.data_normalization import COLUMN_MAPPING


@task(retries=3, retry_delay_seconds=60)
def ingest_and_validate_bronze(path: Path, schema_type: str) -> pl.DataFrame:
    """
    Bronze Task: Scan raw data and validate basic integrity.
    """
    pipeline = PolarsPipeline()
    validator = DataValidator()
    event_store = EventStore()

    lf = pipeline.scan_file(path)
    df_raw = lf.collect()

    validation_results = validator.validate_bronze(df_raw)

    event_store.append(
        "BronzeValidationCompleted",
        {"file": str(path), "success": validation_results["success"]},
    )

    if not validation_results["success"]:
        raise ValueError(f"Bronze validation failed for {path}")

    return df_raw


@task(retries=3, retry_delay_seconds=60)
def transform_to_silver(df_raw: pl.DataFrame, schema_type: str) -> pl.DataFrame:
    """
    Silver Task: Transform, Normalize, and Validate conformed data.
    """
    pipeline = PolarsPipeline()
    validator = DataValidator()
    event_store = EventStore()

    lf = df_raw.lazy()

    # Enforce schema and precision through the specialized flow
    df_silver = pipeline.run_ingestion_conformance_from_lf(lf, schema_type, COLUMN_MAPPING)

    validation_results = validator.validate_silver(df_silver)

    event_store.append(
        "SilverValidationCompleted",
        {"schema_type": schema_type, "success": validation_results["success"]},
    )

    if not validation_results["success"]:
        raise ValueError("Silver validation failed")

    return df_silver


@flow(name="Daily Ingestion Flow")
def daily_ingestion_flow(input_path: Path, schema_type: str = "invoices"):
    """
    Main Orchestration Flow for Abaco Analytics v2.0.
    """
    df_raw = ingest_and_validate_bronze(input_path, schema_type)
    df_silver = transform_to_silver(df_raw, schema_type)

    output_path = Path(f"data/silver/{schema_type}_{datetime.now().strftime('%Y%m%d')}.parquet")
    PolarsPipeline().save_to_silver(df_silver, output_path)

    return df_silver


if __name__ == "__main__":
    # Example execution for local testing
    # daily_ingestion_flow(Path("data/raw/invoices.csv"))
    pass
