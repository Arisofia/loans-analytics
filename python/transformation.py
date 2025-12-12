
"""
Module for data transformation utilities and functions.
Data transformation module for KPI calculations from raw Cascade data.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class DataTransformation:
    """Transform ingested Cascade data into KPI datasets."""
    
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or datetime.now(timezone.utc).isoformat()
        self.transformations_count = 0
    
    def calculate_receivables_metrics(self, df: pd.DataFrame) -> pd.Series:
        """Calculate receivables metrics from portfolio data."""
        metrics = {
            'total_receivable': df['total_receivable_usd'].sum(),
            'total_eligible': (
                df['total_eligible_usd'].sum()
                if 'total_eligible_usd' in df.columns else 0
            ),
            'discounted_balance': (
                df['discounted_balance_usd'].sum()
                if 'discounted_balance_usd' in df.columns else 0
            ),
        }
        logger.info(f"Calculated receivables metrics: {metrics}")
        return pd.Series(metrics)
    
    def calculate_dpd_ratios(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate Days Past Due (DPD) ratios."""
        try:
            total = pd.to_numeric(df['total_receivable_usd'], errors='raise').sum()
        except Exception as e:
            logger.error(f"Non-numeric value found in total_receivable_usd: {e}")
            raise ValueError("Non-numeric value found in total_receivable_usd") from e

        dpd_columns = [col for col in df.columns if col.startswith('dpd_')]
        dpd_ratios = {}

        for col in dpd_columns:
            try:
                col_sum = pd.to_numeric(df[col], errors='raise').sum()
            except Exception as e:
                logger.error(f"Non-numeric value found in {col}: {e}")
                raise ValueError(f"Non-numeric value found in {col}") from e
            if col in df.columns and total > 0:
                dpd_ratios[col] = col_sum / total * 100

        logger.info(f"Calculated DPD ratios: {dpd_ratios}")
        return dpd_ratios
    
    def transform_to_kpi_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform portfolio data into KPI format for analytics. Fail if required columns are missing."""
        required_columns = [
            'total_receivable_usd', 'total_eligible_usd', 'discounted_balance_usd',
            'dpd_0_7_usd', 'dpd_7_30_usd', 'dpd_30_60_usd', 'dpd_60_90_usd', 'dpd_90_plus_usd'
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            logger.error(f"Transformation failed: missing required columns: {missing}")
            raise ValueError(f"Transformation failed: missing required columns: {missing}")

        kpi_df = df.copy()
        kpi_df['receivable_amount'] = df['total_receivable_usd']
        kpi_df['eligible_amount'] = df['total_eligible_usd']
        kpi_df['discounted_amount'] = df['discounted_balance_usd']

        # Calculate portfolio metrics
        dpd_ratios = self.calculate_dpd_ratios(df)
        for ratio_name, ratio_value in dpd_ratios.items():
            kpi_df[f'{ratio_name}_pct'] = ratio_value

        kpi_df['_transform_run_id'] = self.run_id
        kpi_df['_transform_timestamp'] = datetime.now(timezone.utc).isoformat()

        self.transformations_count += 1
        logger.info(f'Transformed {len(kpi_df)} records to KPI dataset')
        return kpi_df
    
    def validate_transformations(
        self, original_df: pd.DataFrame, kpi_df: pd.DataFrame
    ) -> bool:
        """Validate transformation integrity."""
        if len(original_df) != len(kpi_df):
            logger.error(
                f'Row count mismatch: {len(original_df)} vs {len(kpi_df)}'
            )
            return False
    
        original_total = original_df['total_receivable_usd'].sum()
        kpi_total = kpi_df['receivable_amount'].sum()

        if abs(original_total - kpi_total) > 0.01:
            logger.error(
                f'Total receivables mismatch: {original_total} vs {kpi_total}'
            )
            return False

        logger.info('Transformation validation passed')
        return True
