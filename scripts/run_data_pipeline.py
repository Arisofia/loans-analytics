#!/usr/bin/env python3
"""
Data Pipeline Runner
End-to-end orchestration for Cascade Debt data ingestion, transformation, and KPI calculation.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd


# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.transformation import transform_data
from python.validation import validate_dataframe
from python.kpi_engine import KPIEngine
from python.dashboard import show_dashboard


logging.basicConfig(
    level=logging.INFO,
    format=(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
)
logger = logging.getLogger(__name__)

def ingest_data(filepath):
    """
    Ingest data from a CSV file and return a DataFrame.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    try:
        df = pd.read_csv(filepath)
        assert not df.empty, "DataFrame is empty"
        return df
    except Exception as e:
        raise RuntimeError(f"Ingestion failed: {e}")

def main():
    """
    Run complete data pipeline: ingest, transform, validate, and calculate KPIs.
    """
    try:
        logger.info("Starting data pipeline execution...")
        
        # Step 1: Ingest data
        logger.info("Step 1: Ingesting Cascade data...")
        df = ingest_data('data/abaco_portfolio_calculations.csv')
        
        logger.info(f"Ingested {len(df)} records")
        
        # Step 2: Transform data
        logger.info("Step 2: Transforming data for KPI calculation...")
        kpi_df = transform_data(df)
        
        # Validate transformation
        if not transformer.validate_transformations(df, kpi_df):
            logger.error("Transformation validation failed")
            return False
        
        logger.info(f"Transformation complete. {len(kpi_df)} records processed")
        
        # Step 1: Ingest data
        logger.info("Step 1: Ingesting Cascade data...")
        df = ingest_data('data/abaco_portfolio_calculations.csv')
        logger.info(f"Ingested {len(df)} records")

        # Step 2: Transform data
        logger.info("Step 2: Transforming data for KPI calculation...")
        kpi_df = transform_data(df)
        logger.info(f"Transformation complete. {len(kpi_df)} records processed")

        # Step 3: Validate ingested data
        logger.info("Step 3: Validating ingested data...")
        df = validate_dataframe(df)

        # Step 4: Calculate KPIs
        logger.info("Step 4: Calculating financial KPIs...")
        kpi_engine = KPIEngine(kpi_df)

        # Calculate metrics
        par_90, _ = kpi_engine.calculate_par_30()
        # Uncomment and implement if needed:
        # rdr_90, _ = kpi_engine.calculate_rdr_90()

        # Mock collection data for demo
        mock_collections = pd.DataFrame({
            'amount': [kpi_df['principal_balance'].sum() * 0.02]
        })
        collection_rate, _ = kpi_engine.calculate_collection_rate(mock_collections)

        portfolio_health = kpi_engine.calculate_portfolio_health(par_90, collection_rate)
        
        logger.info("Pipeline execution completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
