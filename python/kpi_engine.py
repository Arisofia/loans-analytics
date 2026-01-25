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
    
    def __init__(self, cascade_data: pd.DataFrame):
        self.cascade_data = cascade_data
        self.run_id = f"kpi_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.audit_trail = []
        self.kpi_results = {}
        
    def calculate_par_90(self) -> Tuple[float, Dict]:
        """Portfolio at Risk (90+ days delinquent)
        Formula: SUM(loans.balance WHERE days_past_due >= 90) / SUM(loans.balance)
        """
        try:
            loans_90_plus = self.cascade_data[self.cascade_data['days_past_due'] >= 90]['balance'].sum()
            total_balance = self.cascade_data['balance'].sum()
            
            par_90 = (loans_90_plus / total_balance * 100) if total_balance > 0 else 0
            
            self.audit_trail.append({
                'metric': 'par_90',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'value': par_90,
                'data_version': self.cascade_data['data_version'].iloc[0] if 'data_version' in self.cascade_data else 'unknown',
                'calculation_status': 'success'
            })
            
            logger.info(f"PAR_90 calculated: {par_90:.2f}%")
            return par_90, {'90_day_balance': loans_90_plus, 'total_balance': total_balance}
            
        except Exception as e:
            logger.error(f"PAR_90 calculation failed: {str(e)}")
            self.audit_trail.append({
                'metric': 'par_90',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'error': str(e),
                'calculation_status': 'failed'
            })
            raise
    
    def calculate_rdr_90(self) -> Tuple[float, Dict]:
        """Recovered Default Rate (90+ day recoveries)
        Formula: SUM(recovered_90_day_balances) / SUM(peak_90_day_balances)
        """
        try:
            recovered = self.cascade_data[
                (self.cascade_data['days_past_due_peak'] >= 90) & 
                (self.cascade_data['days_past_due_current'] < 90)
            ]['balance'].sum()
            
            peak_90 = self.cascade_data[self.cascade_data['days_past_due_peak'] >= 90]['balance'].sum()
            
            rdr_90 = (recovered / peak_90 * 100) if peak_90 > 0 else 0
            
            self.audit_trail.append({
                'metric': 'rdr_90',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'value': rdr_90,
                'data_version': self.cascade_data['data_version'].iloc[0] if 'data_version' in self.cascade_data else 'unknown',
                'calculation_status': 'success'
            })
            
            logger.info(f"RDR_90 calculated: {rdr_90:.2f}%")
            return rdr_90, {'recovered': recovered, 'peak_90': peak_90}
            
        except Exception as e:
            logger.error(f"RDR_90 calculation failed: {str(e)}")
            self.audit_trail.append({
                'metric': 'rdr_90',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'error': str(e),
                'calculation_status': 'failed'
            })
            raise
    
    def calculate_collection_rate(self, collections_data: pd.DataFrame) -> Tuple[float, Dict]:
        """Effective Collection Rate
        Formula: SUM(collections) / SUM(receivables_outstanding)
        """
        try:
            total_collections = collections_data['amount'].sum()
            total_receivables = self.cascade_data['balance'].sum()
            
            collection_rate = (total_collections / total_receivables * 100) if total_receivables > 0 else 0
            
            self.audit_trail.append({
                'metric': 'collection_rate',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'value': collection_rate,
                'data_version': self.cascade_data['data_version'].iloc[0] if 'data_version' in self.cascade_data else 'unknown',
                'calculation_status': 'success'
            })
            
            logger.info(f"Collection Rate calculated: {collection_rate:.2f}%")
            return collection_rate, {'collections': total_collections, 'receivables': total_receivables}
            
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
    
    def calculate_portfolio_health(self, par_90: float, rdr_90: float, collection_rate: float) -> float:
        """Portfolio Health Score (0-10 scale)
        Formula: (10 - PAR_90) * (RDR_90/100) * (CollectionRate * 10)
        """
        try:
            health_score = (10 - (par_90 / 10)) * (rdr_90 / 100) * (collection_rate / 10)
            health_score = max(0, min(10, health_score))  # Clamp to 0-10
            
            self.audit_trail.append({
                'metric': 'portfolio_health',
                'run_id': self.run_id,
                'timestamp': datetime.now(),
                'value': health_score,
                'components': {'par_90': par_90, 'rdr_90': rdr_90, 'collection_rate': collection_rate},
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
                if metric in ['par_90', 'rdr_90', 'collection_rate']:
                    validation_results[metric] = 0 <= value <= 100
                elif metric == 'portfolio_health':
                    validation_results[metric] = 0 <= value <= 10
        
        return validation_results
