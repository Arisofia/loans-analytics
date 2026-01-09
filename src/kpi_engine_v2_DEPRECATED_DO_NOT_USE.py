import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.kpis.collection_rate import \
    calculate_collection_rate as calculate_collection_rate_logic
from src.kpis.dti import calculate_dti as calculate_dti_logic
from src.kpis.ltv import calculate_ltv as calculate_ltv_logic
from src.kpis.par_30 import calculate_par_30 as calculate_par_30_logic
from src.kpis.par_90 import calculate_par_90 as calculate_par_90_logic
from src.kpis.portfolio_health import \
    calculate_portfolio_health as calculate_portfolio_health_logic
from src.kpis.portfolio_yield import \
    calculate_portfolio_yield as calculate_portfolio_yield_logic

logger = logging.getLogger(__name__)


class KPIEngineV2:
    """
    Orchestrate KPI calculations with consistent (value, context) interface.
    Provides audit trail, error handling, and full traceability.
    """

    KPI_FUNCTIONS = {
        "PAR30": calculate_par_30_logic,
        "PAR90": calculate_par_90_logic,
        "CollectionRate": calculate_collection_rate_logic,
    }

    ON_DEMAND_KPI_FUNCTIONS = {
        "LTV": calculate_ltv_logic,
        "DTI": calculate_dti_logic,
        "PortfolioYield": calculate_portfolio_yield_logic,
    }

    def __init__(
        self,
        df: pd.DataFrame,
        actor: str = "system",
        action: str = "kpi",
        run_id: Optional[str] = None,
    ):
        self.df = df
        self.actor = actor
        self.action = action
        self.run_id = run_id or f"kpi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.audit_trail: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Dict[str, Any]] = {}

    def calculate_all(self, include_composite: bool = True) -> Dict[str, Any]:
        """Calculate all configured KPIs with full audit trail."""
        self._log_event("calculate_all", "started", kpi_count=len(self.KPI_FUNCTIONS))

        try:
            for kpi_name, calculator in self.KPI_FUNCTIONS.items():
                try:
                    value, context = calculator(self.df)
                    context.setdefault("metric", kpi_name)
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
                    health_val, health_ctx = calculate_portfolio_health_logic(
                        par30_val, collection_val
                    )
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

    def calculate_portfolio_health(
        self, par_30: Optional[float] = None, collection_rate: Optional[float] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate Portfolio Health composite metric."""
        p30 = par_30 if par_30 is not None else self.get_metric("PAR30")
        cr = collection_rate if collection_rate is not None else self.get_metric("CollectionRate")

        if p30 is None or cr is None:
            return 0.0, {"error": "Missing inputs for PortfolioHealth", "metric": "PortfolioHealth"}

        val, ctx = calculate_portfolio_health_logic(p30, cr)
        ctx.setdefault("metric", "PortfolioHealth")
        return val, ctx

    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate PAR30."""
        val, ctx = calculate_par_30_logic(self.df)
        ctx.setdefault("metric", "PAR30")
        return val, ctx

    def calculate_par_90(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate PAR90."""
        val, ctx = calculate_par_90_logic(self.df)
        ctx.setdefault("metric", "PAR90")
        return val, ctx

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate Collection Rate."""
        val, ctx = calculate_collection_rate_logic(self.df)
        ctx.setdefault("metric", "CollectionRate")
        return val, ctx

    def calculate_ltv(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate LTV."""
        return calculate_ltv_logic(self.df)

    def calculate_dti(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate DTI."""
        return calculate_dti_logic(self.df)

    def calculate_portfolio_yield(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate Portfolio Yield."""
        return calculate_portfolio_yield_logic(self.df)

    def get_audit_trail(self) -> pd.DataFrame:
        """Return audit trail as DataFrame."""
        if not self.audit_trail:
            return pd.DataFrame()
        return pd.DataFrame(self.audit_trail)

    def get_metric(self, name: str) -> Optional[float]:
        """Helper to get a single metric value by name."""
        if name in self.metrics:
            return self.metrics[name].get("value")

        calculator = self.KPI_FUNCTIONS.get(name) or self.ON_DEMAND_KPI_FUNCTIONS.get(name)
        if calculator is not None:
            val, _ = calculator(self.df)
            return float(val) if val is not None else None

        raise ValueError(f"KPI '{name}' not supported by engine")

    def _log_event(self, event: str, status: str, **details: Any) -> None:
        entry = {
            "run_id": self.run_id,
            "event": event,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.actor,
            "action": self.action,
            **details,
        }
        self.audit_trail.append(entry)
        logger.info("[KPI:%s] %s | %s", event, status, details)
