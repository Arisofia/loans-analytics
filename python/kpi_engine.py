
import logging
from datetime import datetime
from typing import Dict, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def _require_columns(df: pd.DataFrame, required: Tuple[str, ...]):
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for KPI calculation: {', '.join(missing)}")


def calculate_par_90(df: pd.DataFrame) -> float:
    """Calculate Portfolio at Risk 90 (PAR90) as a percentage."""
    _require_columns(df, ("dpd_90_plus_usd", "total_receivable_usd"))
    total_receivable = df["total_receivable_usd"].sum()
    if total_receivable == 0:
        return 0.0
    par_90 = df["dpd_90_plus_usd"].sum() / total_receivable * 100
    return par_90


def calculate_collection_rate(df: pd.DataFrame) -> float:
    """Calculate collection rate based on eligible vs total receivables."""
    _require_columns(df, ("total_receivable_usd", "total_eligible_usd"))
    total_receivable = df["total_receivable_usd"].sum()
    if total_receivable == 0:
        return 0.0
    total_eligible = df["total_eligible_usd"].sum()
    return total_eligible / total_receivable * 100


class KPIEngine:
    """Autonomous KPI calculation system with full audit trail."""

    def __init__(self, portfolio_data: pd.DataFrame):
        self.portfolio_data = portfolio_data
        self.run_id = (
            f"kpi_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.audit_trail = []
        self.kpi_results = {}

    def calculate_par_30(self) -> Tuple[float, Dict]:
        """Portfolio at Risk (30+ days)
        Formula: SUM(dpd_30_60 + dpd_60_90 + dpd_90+) / SUM(total_receivable)
        Strictly require all columns, log and raise if missing or invalid.
        """
        try:
            required = ['dpd_30_60_usd', 'dpd_60_90_usd', 'dpd_90_plus_usd', 'total_receivable_usd']
            missing = [col for col in required if col not in self.portfolio_data.columns]
            if missing:
                msg = f"PAR_30 calculation failed: missing columns: {missing}"
                logger.error(msg)
                self.audit_trail.append({
                    'metric': 'par_30',
                    'run_id': self.run_id,
                    'timestamp': datetime.now(),
                    'error': msg,
                    'calculation_status': 'failed',
                    'missing_columns': missing
                })
                raise ValueError(msg)

            dpd_30_plus = (
                self.portfolio_data['dpd_30_60_usd'].sum() +
                self.portfolio_data['dpd_60_90_usd'].sum() +
                self.portfolio_data['dpd_90_plus_usd'].sum()
            )
            total_receivable = self.portfolio_data['total_receivable_usd'].sum()
            if not pd.api.types.is_numeric_dtype(self.portfolio_data['total_receivable_usd']):
                msg = "PAR_30 calculation failed: total_receivable_usd is not numeric"
                logger.error(msg)
                self.audit_trail.append({
                    'metric': 'par_30',
                    'run_id': self.run_id,
                    'timestamp': datetime.now(),
                    'error': msg,
                    'calculation_status': 'failed'
                })
                raise ValueError(msg)
            par_30 = (
                dpd_30_plus / total_receivable * 100
                if total_receivable > 0
                else 0
            )

            self.audit_trail.append({
                'metric': 'par_30',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'value': par_30,
                'calculation_status': 'success'
            })

            logger.info(f"PAR_30 calculated: {par_30:.2f}%")
            return (
                par_30,
                {
                    '30_plus_balance': dpd_30_plus,
                    'total_receivable': total_receivable
                }
            )

        except Exception as e:
            logger.error(f"PAR_30 calculation failed: {str(e)}")
            self.audit_trail.append({
                'metric': 'par_30',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'error': str(e),
                'calculation_status': 'failed'
            })
            raise

    def calculate_collection_rate(
        self, collections_data: pd.DataFrame = None
    ) -> Tuple[float, Dict]:
        """Effective Collection Rate
        Formula: SUM(eligible_receivables) / SUM(total_receivables)
        Strictly require all columns, log and raise if missing or invalid.
        """
        try:
            required = ['total_receivable_usd', 'total_eligible_usd']
            missing = [col for col in required if col not in self.portfolio_data.columns]
            if missing:
                msg = f"Collection Rate calculation failed: missing columns: {missing}"
                logger.error(msg)
                self.audit_trail.append({
                    'metric': 'collection_rate',
                    'run_id': self.run_id,
                    'timestamp': datetime.now(),
                    'error': msg,
                    'calculation_status': 'failed',
                    'missing_columns': missing
                })
                raise ValueError(msg)

            total_receivables = self.portfolio_data['total_receivable_usd'].sum()
            total_eligible = self.portfolio_data['total_eligible_usd'].sum()
            if not pd.api.types.is_numeric_dtype(self.portfolio_data['total_receivable_usd']):
                msg = "Collection Rate calculation failed: total_receivable_usd is not numeric"
                logger.error(msg)
                self.audit_trail.append({
                    'metric': 'collection_rate',
                    'run_id': self.run_id,
                    'timestamp': datetime.now(),
                    'error': msg,
                    'calculation_status': 'failed'
                })
                raise ValueError(msg)
            collections_total = (
                collections_data['amount'].sum()
                if (
                    isinstance(collections_data, pd.DataFrame)
                    and 'amount' in collections_data.columns
                )
                else 0
            )

            collection_rate = (
                total_eligible / total_receivables * 100
                if total_receivables > 0
                else 0
            )

            self.audit_trail.append({
                'metric': 'collection_rate',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'value': collection_rate,
                'calculation_status': 'success',
            })

            logger.info(f"Collection Rate calculated: {collection_rate:.2f}%")
            return (
                collection_rate,
                {
                    'eligible': total_eligible,
                    'total': total_receivables,
                    'collections': collections_total,
                },
            )

        except Exception as e:
            logger.error(f"Collection Rate calculation failed: {str(e)}")
            self.audit_trail.append({
                'metric': 'collection_rate',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'error': str(e),
                'calculation_status': 'failed'
            })
            raise

    def calculate_portfolio_health(
        self, par_30: float, collection_rate: float
    ) -> float:
        """Portfolio Health Score (0-10 scale)
        Formula: (10 - PAR_30/10) * (CollectionRate * 10)
        """
        try:
            health_score = (10 - (par_30 / 10)) * (collection_rate / 10)
            health_score = max(0, min(10, health_score))

            self.audit_trail.append({
                'metric': 'portfolio_health',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'value': health_score,
                'components': {
                    'par_30': par_30,
                    'collection_rate': collection_rate,
                },
                'calculation_status': 'success',
            })

            logger.info(
                f"Portfolio Health calculated: {health_score:.2f}/10"
            )
            return health_score

        except Exception as e:
            logger.error(f"Portfolio Health calculation failed: {str(e)}")
            self.audit_trail.append({
                'metric': 'portfolio_health',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'error': str(e),
                'calculation_status': 'failed'
            })
            raise
    
    def get_audit_trail(self) -> pd.DataFrame:
        """Return complete audit trail for compliance"""
        return pd.DataFrame(self.audit_trail)
    
    def validate_calculations(self) -> Dict[str, bool]:
        """Validate all calculations meet data quality gates"""
        validation_results = {}
    
        for record in self.audit_trail:
            if record.get('calculation_status') == 'success':
                metric = record['metric']
                value = record.get('value', None)
    
                # Check for reasonable bounds
                if metric in ['par_30', 'collection_rate']:
                    validation_results[metric] = 0 <= value <= 100
                elif metric == 'portfolio_health':
                    validation_results[metric] = 0 <= value <= 10
    
        return validation_results
