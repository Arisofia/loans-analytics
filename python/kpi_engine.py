import pandas as pd
from typing import Tuple, Dict, Any
from python.kpis.par_30 import calculate_par_30
from python.kpis.par_90 import calculate_par_90
from python.kpis.collection_rate import calculate_collection_rate
from python.kpis.portfolio_health import calculate_portfolio_health

class KPIEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.audit_trail: list[dict[str, object]] = []

    def _log_metric(self, metric: str, value: float, method: str = "standard") -> Dict[str, Any]:
        ctx = {"metric": metric, "method": method}
        self.audit_trail.append({**ctx, "value": value})
        return ctx

    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        val = calculate_par_30(self.df)
        ctx = self._log_metric("PAR30", val)
        return val, ctx

    def calculate_par_90(self) -> Tuple[float, Dict[str, Any]]:
        val = calculate_par_90(self.df)
        ctx = self._log_metric("PAR90", val)
        return val, ctx

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        val = calculate_collection_rate(self.df)
        ctx = self._log_metric("CollectionRate", val)
        return val, ctx

    def calculate_portfolio_health(self, par_30: float, collection_rate: float) -> float:
        val = calculate_portfolio_health(par_30, collection_rate)
        self._log_metric("HealthScore", val)
        return val

    def get_audit_trail(self) -> pd.DataFrame:
        return pd.DataFrame(self.audit_trail)