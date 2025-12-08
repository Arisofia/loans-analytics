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

from python.ingestion import CascadeIngestion
from python.transformation import DataTransformation, transform_data
from python.validation import validate_dataframe
from python.kpi_engine import KPIEngine, calculate_kpis
from python.dashboard import show_dashboard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ingest_data(filepath):
    try:
        df = pd.read_csv(filepath)
        assert not df.empty, "DataFrame is empty"
        return df
    except Exception as e:
        raise RuntimeError(f"Ingestion failed: {e}")

def main():
    """Run complete data pipeline."""
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
        
        # Step 3: Validate ingested data
        logger.info("Step 3: Validating ingested data...")
        df = validate_dataframe(df)
        summary = ingester.get_ingest_summary()
        logger.info(f"Ingestion summary: {summary['total_errors']} errors")
        if summary['total_errors'] > 0:
            logger.error('Validation/ingestion errors detected, aborting pipeline.')
            return False
        
        # Step 4: Calculate KPIs
        logger.info("Step 4: Calculating financial KPIs...")
        kpis = calculate_kpis(kpi_df)
        kpi_engine = KPIEngine(kpi_df)
        
        # Calculate metrics
        par_90, par_90_details = kpi_engine.calculate_par_90()
        rdr_90, rdr_90_details = kpi_engine.calculate_rdr_90()
        
        # Mock collection data for demo
        mock_collections = pd.DataFrame({'amount': [kpi_df['principal_balance'].sum() * 0.02]})
        collection_rate, collection_details = kpi_engine.calculate_collection_rate(mock_collections)
        
        portfolio_health = kpi_engine.calculate_portfolio_health(par_90, rdr_90, collection_rate)
        
        logger.info(f"PAR 90: {par_90:.2f}%")
        logger.info(f"RDR 90: {rdr_90:.2f}%")
        logger.info(f"Collection Rate: {collection_rate:.2f}%")
        logger.info(f"Portfolio Health Score: {portfolio_health:.2f}/10")
        
        # Validate calculations
        validation_results = kpi_engine.validate_calculations()
        logger.info(f"Calculation validation: {validation_results}")
        
        # Export audit trail
        audit_df = kpi_engine.get_audit_trail()
        logger.info(f"Audit trail: {len(audit_df)} records")
        
        # Step 5: Show dashboard
        logger.info("Step 5: Displaying dashboard...")
        show_dashboard(kpis)
        
        logger.info("Pipeline execution completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
