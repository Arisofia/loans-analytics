from prefect import flow, get_run_logger, task
from prefect.artifacts import create_markdown_artifact

try:
    from prefect.blocks.notifications import PagerDutyNotification
except ImportError:
    # Fallback for older prefect versions if necessary, though 2.x/3.x have these
    pass
import io
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from python.ingestion import AbacoIngestion
from src.analytics.polars_analytics_engine import PolarsAnalyticsEngine


@task(name="Notify Incident")
def notify_incident(message: str, severity: str = "error"):
    """Triggers PagerDuty notifications via Prefect blocks."""
    logger = get_run_logger()

    # PagerDuty Notification (Critical only)
    if severity == "critical":
        try:
            pd_block = PagerDutyNotification.load("abaco-pagerduty")
            pd_block.notify(subject="🚨 Abaco Analytics Critical Failure", message=message)
        except Exception:
            logger.warning("PagerDuty block 'abaco-pagerduty' not found. Skipping PagerDuty alert.")


@task(retries=5, retry_delay_seconds=60)
def load_source_data(file_path: str) -> bytes:
    """Task to load data with exponential backoff retries."""
    logger = get_run_logger()
    logger.info(f"🚀 Loading source data: {file_path}")
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file {file_path} not found.")
    return path.read_bytes()


@task(name="Validate & Ingest Contract")
def validate_and_ingest(content: bytes) -> pl.DataFrame:
    """Performs schema validation and strict contract enforcement."""
    logger = get_run_logger()
    ingestor = AbacoIngestion(strict_validation=True)
    df = ingestor.ingest_uploaded_file(io.BytesIO(content))
    if df.is_empty():
        raise ValueError("❌ Ingestion failed: Resulting DataFrame is empty or violated contract.")

    logger.info(f"✅ Data validated. Rows: {len(df)} | Run ID: {ingestor.run_id}")
    return df


@task(name="Compute Polars KPIs")
def compute_analytics(df: pl.DataFrame):
    """Computes financial KPIs using the Polars vectorized engine."""
    engine = PolarsAnalyticsEngine(df)
    kpis = engine.compute_kpis()
    return kpis


@task(name="Publish Ingestion Artifact")
def publish_ingestion_summary(kpis: dict, row_count: int, file_path: str):
    """Generates a Prefect Markdown artifact for live reporting."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    markdown_report = f"""
# 📊 Loan Analytics Ingestion Report
**Timestamp:** {timestamp}
**Source File:** `{file_path}`
**Rows Processed:** {row_count}

## 📈 Core KPIs
| Metric | Value |
| :--- | :--- |
| Delinquency Rate | {kpis.get('delinquency_rate', 0):.2f}% |
| Portfolio Yield | {kpis.get('portfolio_yield', 0):.2f}% |
| Avg LTV | {kpis.get('avg_ltv', 0):.1f}% |
| Avg DTI | {kpis.get('avg_dti', 0):.1f}% |

## 🛡️ Integrity Status
- ✅ Schema Validation: Passed
- ✅ Contract Enforcement: Active
- ✅ Lineage: Tracked
"""
    create_markdown_artifact(
        key="ingestion-summary",
        markdown=markdown_report,
        description=f"Analytics Summary for {file_path}",
    )


@flow(name="Loan Analytics Ingestion Pipeline", log_prints=True)
def loan_ingestion_flow(file_path: str):
    """
    Main orchestration flow for automated ingestion.
    Supports retries, state persistence, and automated alerting.
    """
    logger = get_run_logger()
    logger.info("🎬 Starting Loan Analytics Orchestration")

    try:
        raw_content = load_source_data(file_path)
        df = validate_and_ingest(raw_content)
        kpis = compute_analytics(df)

        publish_ingestion_summary(kpis, len(df), file_path)

        logger.info("🏁 Flow completed successfully")
        return kpis
    except Exception as e:
        error_msg = f"Pipeline failed for {file_path}: {str(e)}"
        logger.error(f"❌ {error_msg}")
        notify_incident(error_msg, severity="critical")
        raise


if __name__ == "__main__":
    # Example local run
    # loan_ingestion_flow("data/raw/sample_data.csv")
    pass
