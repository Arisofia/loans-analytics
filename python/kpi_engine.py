"""KPI Calculation Engine
Computes all Fintech Factory KPIs from base Cascade Debt data
Implements Vibe Solutioning: rebuild from base, validate, trace
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class KPIEngine:
    """Autonomous KPI calculation system with full audit trail"""
    
    def __init__(self, portfolio_data: pd.DataFrame):
        self.portfolio_data = portfolio_data
        self.run_id = f"kpi_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.audit_trail = []
        self.kpi_results = {}
    
    def calculate_par_30(self) -> Tuple[float, Dict]:
        """Portfolio at Risk (30+ days)
        Formula: SUM(dpd_30_60 + dpd_60_90 + dpd_90+) / SUM(total_receivable)
        """
        try:
            dpd_30_plus = 0
            if 'dpd_30_60_usd' in self.portfolio_data.columns:
                dpd_30_plus += self.portfolio_data['dpd_30_60_usd'].sum()
            if 'dpd_60_90_usd' in self.portfolio_data.columns:
                dpd_30_plus += self.portfolio_data['dpd_60_90_usd'].sum()
            
            total_receivable = self.portfolio_data['total_receivable_usd'].sum()
            par_30 = (dpd_30_plus / total_receivable * 100) if total_receivable > 0 else 0
            
            self.audit_trail.append({
                'metric': 'par_30',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'value': par_30,
                'calculation_status': 'success'
            })
            
            logger.info(f"PAR_30 calculated: {par_30:.2f}%")
            return par_30, {'30_plus_balance': dpd_30_plus, 'total_receivable': total_receivable}
        
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
    
    def calculate_collection_rate(self, collections_data: pd.DataFrame = None) -> Tuple[float, Dict]:
        """Effective Collection Rate
        Formula: SUM(eligible_receivables) / SUM(total_receivables)
        """
        try:
            total_receivables = self.portfolio_data['total_receivable_usd'].sum()
            total_eligible = self.portfolio_data.get('total_eligible_usd', pd.Series([0])).sum()
            
            collection_rate = (total_eligible / total_receivables * 100) if total_receivables > 0 else 0
            
            self.audit_trail.append({
                'metric': 'collection_rate',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'value': collection_rate,
                'calculation_status': 'success'
            })
            
            logger.info(f"Collection Rate calculated: {collection_rate:.2f}%")
            return collection_rate, {'eligible': total_eligible, 'total': total_receivables}
        
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
    
    def calculate_portfolio_health(self, par_30: float, collection_rate: float) -> float:
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
                'components': {'par_30': par_30, 'collection_rate': collection_rate},
                'calculation_status': 'success'
            })
            
            logger.info(f"Portfolio Health calculated: {health_score:.2f}/10")
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
