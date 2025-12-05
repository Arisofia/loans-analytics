"""Data transformation module for KPI calculations from raw Cascade data."""
import logging
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

logger = logging.getLogger(__name__)

class DataTransformation:
    """Transform ingested Cascade data into KPI datasets."""

    def __init__(self, run_id: str = None):
        self.run_id = run_id or datetime.utcnow().isoformat()
        self.transformations_count = 0

    def calculate_par90(self, df: pd.DataFrame) -> pd.Series:
        """Calculate PAR 90 (loans past due 90+ days) metric."""
        par90 = (df['status'] == 'Past Due 90+').astype(int)
        logger.info(f'Calculated PAR90: {par90.sum()} accounts')
        return par90

    def calculate_rdr90(self, df: pd.DataFrame) -> pd.Series:
        """Calculate RDR 90 (risk diversification ratio at 90 days)."""
        par90_balance = df[df['status'] == 'Past Due 90+']['principal_balance'].sum()
        total_balance = df['principal_balance'].sum()
        rdr90 = (par90_balance / total_balance * 100) if total_balance > 0 else 0
        logger.info(f'Calculated RDR90: {rdr90:.2f}%')
        return rdr90

    def calculate_collection_rate(self, df: pd.DataFrame) -> float:
        """Calculate monthly collection rate percentage."""
        collected = df[df['status'] == 'Collected']['principal_balance'].sum()
        expected = df['principal_balance'].sum()
        rate = (collected / expected * 100) if expected > 0 else 0
        logger.info(f'Calculated collection rate: {rate:.2f}%')
        return rate

    def calculate_portfolio_health(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive portfolio health metrics."""
        return {
            'total_portfolio': float(df['principal_balance'].sum()),
            'active_loans': len(df[df['status'] == 'Active']),
            'defaulted_loans': len(df[df['status'] == 'Defaulted']),
            'collected_amount': float(df[df['status'] == 'Collected']['principal_balance'].sum()),
            'avg_loan_amount': float(df['principal_balance'].mean()),
            'par90_count': int(self.calculate_par90(df).sum()),
            'rdr90_ratio': float(self.calculate_rdr90(df)),
            'collection_rate': float(self.calculate_collection_rate(df)),
            '_run_id': self.run_id,
            '_timestamp': datetime.utcnow().isoformat(),
        }

    def transform_to_kpi_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform loan data into KPI format for analytics."""
        kpi_df = df.copy()
        kpi_df['par90_flag'] = self.calculate_par90(df)
        kpi_df['collection_bucket'] = pd.cut(kpi_df['principal_balance'],
                                             bins=[0, 1000, 5000, 10000, float('inf')],
                                             labels=['<1k', '1-5k', '5-10k', '>10k'])
        kpi_df['_transform_run_id'] = self.run_id
        kpi_df['_transform_timestamp'] = datetime.utcnow().isoformat()
        
        self.transformations_count += 1
        logger.info(f'Transformed {len(kpi_df)} records to KPI dataset')
        return kpi_df

    def validate_transformations(self, original_df: pd.DataFrame, kpi_df: pd.DataFrame) -> bool:
        """Validate transformation integrity."""
        if len(original_df) != len(kpi_df):
            logger.error(f'Row count mismatch: {len(original_df)} vs {len(kpi_df)}')
            return False
        
        original_balance = original_df['principal_balance'].sum()
        kpi_balance = kpi_df['principal_balance'].sum()
        if abs(original_balance - kpi_balance) > 0.01:
            logger.error(f'Balance mismatch: {original_balance} vs {kpi_balance}')
            return False
        
        logger.info('Transformation validation passed')
        return True
