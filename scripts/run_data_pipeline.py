#!/usr/bin/env python3
"""
Data Pipeline Runner
End-to-end orchestration for Cascade Debt data ingestion, transformation, and KPI calculation.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.ingestion import CascadeIngestion
from python.transformation import DataTransformation
from python.kpi_engine import KPIEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run complete data pipeline."""
    try:
        logger.info("Starting data pipeline execution...")
        
        # Step 1: Ingest data
        logger.info("Step 1: Ingesting Cascade data...")
        ingester = CascadeIngestion(data_dir='data/cascade')
        df = ingester.ingest_csv('abaco_portfolio_calculations.csv')
        
        if df.empty:
            logger.error("No data ingested. Aborting pipeline.")
            return False
        
        logger.info(f"Ingested {len(df)} records")
        
        # Step 2: Validate ingested data
        logger.info("Step 2: Validating ingested data...")
        df = ingester.validate_loans(df)
        summary = ingester.get_ingest_summary()
        logger.info(f"Ingestion summary: {summary['total_errors']} errors")
        if summary['total_errors'] > 0:
            logger.error('Validation/ingestion errors detected, aborting pipeline.')
            return False
        
        # Step 3: Transform data
        logger.info("Step 3: Transforming data for KPI calculation...")
        transformer = DataTransformation()
        kpi_df = transformer.transform_to_kpi_dataset(df)
        
        # Validate transformation
        if not transformer.validate_transformations(df, kpi_df):
            logger.error("Transformation validation failed")
            return False
        
        logger.info(f"Transformation complete. {len(kpi_df)} records processed")
        
        # Step 4: Calculate KPIs
        logger.info("Step 4: Calculating financial KPIs...")
        kpi_engine = KPIEngine(kpi_df)
        
        # Calculate metrics
        par_90, par_90_details = kpi_engine.calculate_par_90()
        rdr_90, rdr_90_details = kpi_engine.calculate_rdr_90()
        
        # Mock collection data for demo
        import pandas as pd
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
        
        logger.info("Pipeline execution completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
