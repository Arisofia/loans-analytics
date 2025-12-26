import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from python.kpis.collection_rate import calculate_collection_rate
from python.kpis.par_30 import calculate_par_30
from python.kpis.par_90 import calculate_par_90
from python.kpis.portfolio_health import calculate_portfolio_health
from python.validation import validate_dataframe

logger = logging.getLogger(__name__)


class KPIEngineV2:
    """
    Orchestrate KPI calculations with consistent (value, context) interface.
    Provides audit trail, error handling, and full traceability.
    """

    KPI_FUNCTIONS = {
        "PAR30": calculate_par_30,
        "PAR90": calculate_par_90,
        "CollectionRate": calculate_collection_rate,
    }

    def __init__(self, df: pd.DataFrame, actor: str = "system", action: str = "kpi"):
        self.df = df
        self.actor = actor
        self.action = action
        self.audit_trail: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Dict[str, Any]] = {}

    def calculate_all(self, include_composite: bool = True) -> Dict[str, Any]:
        """Calculate all configured KPIs with full audit trail."""
        self._log_event("calculate_all", "started", kpi_count=len(self.KPI_FUNCTIONS))

        try:
            for kpi_name, calculator in self.KPI_FUNCTIONS.items():
                try:
                    value, context = calculator(self.df)
                    self.metrics[kpi_name] = {
                        "value": float(value),
                        **context,
                    }
                    self._log_event("kpi_calculated", "success", kpi=kpi_name, value=value)
                except Exception as e:
                    self._log_event("kpi_calculation_failed", "error", kpi=kpi_name, error=str(e))
                    self.metrics[kpi_name] = {"value": None, "error": str(e)}

            if include_composite and "PAR30" in self.metrics and "CollectionRate" in self.metrics:
                try:
                    par30_val = self.metrics["PAR30"]["value"]
                    collection_val = self.metrics["CollectionRate"]["value"]
                    health_val, health_ctx = calculate_portfolio_health(par30_val, collection_val)
                    self.metrics["PortfolioHealth"] = {
                        "value": float(health_val),
                        **health_ctx,
                    }
                    self._log_event("composite_kpi_calculated", "success", kpi="PortfolioHealth")
                except Exception as e:
                    self._log_event("composite_kpi_failed", "error", error=str(e))

            self._log_event("calculate_all", "completed", kpi_count=len(self.metrics))
            return self.metrics

        except Exception as e:
            self._log_event("calculate_all", "failed", error=str(e))
            raise

    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate PAR30."""
        return calculate_par_30(self.df)

    def calculate_par_90(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate PAR90."""
        return calculate_par_90(self.df)

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate Collection Rate."""
        return calculate_collection_rate(self.df)

    def get_audit_trail(self) -> pd.DataFrame:
        """Return audit trail as DataFrame."""
        if not self.audit_trail:
            return pd.DataFrame()
        return pd.DataFrame(self.audit_trail)

    def _log_event(self, event: str, status: str, **details: Any) -> None:
        entry = {
            "event": event,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.actor,
            "action": self.action,
            **details,
        }
        self.audit_trail.append(entry)
        logger.info(f"[KPI:{event}] {status} | {details}")
