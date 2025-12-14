import pandas as pd
from typing import Tuple, Dict, Any
from python.kpis.par_30 import calculate_par_30
from python.kpis.par_90 import calculate_par_90
from python.kpis.collection_rate import calculate_collection_rate
from python.kpis.portfolio_health import calculate_portfolio_health

class KPIEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.audit_trail = []

    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        val = calculate_par_30(self.df)
        ctx = {"metric": "PAR30", "method": "standard"}
        self.audit_trail.append({**ctx, "value": val})
        return val, ctx

    def calculate_par_90(self) -> Tuple[float, Dict[str, Any]]:
        val = calculate_par_90(self.df)
        ctx = {"metric": "PAR90", "method": "standard"}
        self.audit_trail.append({**ctx, "value": val})
        return val, ctx

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        val = calculate_collection_rate(self.df)
        ctx = {"metric": "CollectionRate", "method": "standard"}
        self.audit_trail.append({**ctx, "value": val})
        return val, ctx

    def calculate_portfolio_health(self, par_30: float, collection_rate: float) -> float:
        val = calculate_portfolio_health(par_30, collection_rate)
        self.audit_trail.append({"metric": "HealthScore", "value": val})
        return val

    def get_audit_trail(self) -> pd.DataFrame:
        return pd.DataFrame(self.audit_trail)