import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.kpis.active_clients import \
    calculate_active_clients as calculate_active_clients_logic
from src.kpis.actual_yield import \
    calculate_actual_yield as calculate_actual_yield_logic
from src.kpis.aum import calculate_aum as calculate_aum_logic
from src.kpis.churn_rate import \
    calculate_churn_rate as calculate_churn_rate_logic
from src.kpis.collection_rate import \
    calculate_collection_rate as calculate_collection_rate_logic
from src.kpis.concentration import \
    calculate_concentration_top10 as calculate_concentration_top10_logic
from src.kpis.default_rate import \
    calculate_default_rate as calculate_default_rate_logic
from src.kpis.dti import calculate_dti as calculate_dti_logic
from src.kpis.ltv import calculate_ltv as calculate_ltv_logic
from src.kpis.par_30 import calculate_par_30 as calculate_par_30_logic
from src.kpis.par_90 import calculate_par_90 as calculate_par_90_logic
from src.kpis.portfolio_health import \
    calculate_portfolio_health as calculate_portfolio_health_logic
from src.kpis.portfolio_yield import \
    calculate_portfolio_yield as calculate_portfolio_yield_logic
from src.kpis.recurrence import \
    calculate_recurrence as calculate_recurrence_logic
from src.kpis.weighted_apr import \
    calculate_weighted_apr as calculate_weighted_apr_logic
from src.utils.data_normalization import normalize_columns

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
        "AUM": calculate_aum_logic,
        "WeightedAPR": calculate_weighted_apr_logic,
        "ActualYield": calculate_actual_yield_logic,
        "Recurrence": calculate_recurrence_logic,
        "ConcentrationTop10": calculate_concentration_top10_logic,
        "DefaultRate": calculate_default_rate_logic,
        "ActiveClients": calculate_active_clients_logic,
        "ChurnRate": calculate_churn_rate_logic,
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
        custom_kpis: Optional[Dict[str, Any]] = None,
        normalize: bool = True,
    ):
        self.df = normalize_columns(df) if normalize else df
        self.actor = actor
        self.action = action
        self.run_id = run_id or f"kpi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.audit_trail: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Dict[str, Any]] = {}

        # Use instance-level copies of the KPI function maps
        self.kpi_functions = self.KPI_FUNCTIONS.copy()
        self.on_demand_kpi_functions = self.ON_DEMAND_KPI_FUNCTIONS.copy()

        # Merge custom KPIs if provided
        if custom_kpis:
            self.kpi_functions.update(custom_kpis)

    def _calculate_single(self, name: str, calculator: Any) -> Tuple[float, Dict[str, Any]]:
        """Internal helper for single KPI calculation."""
        try:
            val, ctx = calculator(self.df)
            ctx.setdefault("metric", name)
            return float(val) if val is not None else 0.0, ctx
        except Exception as e:
            self._log_event("kpi_calculation_failed", "error", kpi=name, error=str(e))
            return 0.0, {"metric": name, "error": str(e)}

    def calculate_portfolio_health(
        self, par_30: Optional[float] = None, collection_rate: Optional[float] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate Portfolio Health composite metric."""
        p30 = par_30 if par_30 is not None else self.get_metric("PAR30")
        cr = collection_rate if collection_rate is not None else self.get_metric("CollectionRate")

        if p30 is None or cr is None:
            return 0.0, {"error": "Missing inputs for PortfolioHealth", "metric": "PortfolioHealth"}

        return self._calculate_single(
            "PortfolioHealth", lambda _: calculate_portfolio_health_logic(p30, cr)
        )

    # Facade methods for common KPIs (Backward Compatibility)
    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        return self._calculate_single("PAR30", self.kpi_functions["PAR30"])

    def calculate_par_90(self) -> Tuple[float, Dict[str, Any]]:
        return self._calculate_single("PAR90", self.kpi_functions["PAR90"])

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        return self._calculate_single("CollectionRate", self.kpi_functions["CollectionRate"])

    def calculate_ltv(self) -> Tuple[float, Dict[str, Any]]:
        return self._calculate_single("LTV", self.on_demand_kpi_functions["LTV"])

    def calculate_dti(self) -> Tuple[float, Dict[str, Any]]:
        return self._calculate_single("DTI", self.on_demand_kpi_functions["DTI"])

    def calculate_portfolio_yield(self) -> Tuple[float, Dict[str, Any]]:
        return self._calculate_single(
            "PortfolioYield", self.on_demand_kpi_functions["PortfolioYield"]
        )

    def calculate_all(self, include_composite: bool = True) -> Dict[str, Any]:
        """Calculate all configured KPIs with full audit trail."""
        self._log_event("calculate_all", "started", kpi_count=len(self.kpi_functions))

        # Determine which KPIs to calculate
        if self.df is None or self.df.empty:
            self._log_event("calculate_all", "skipped_empty_dataframe")
            kpis_to_calculate = ["PAR30", "PAR90", "CollectionRate"]
        else:
            kpis_to_calculate = list(self.kpi_functions.keys())

        for kpi_name in kpis_to_calculate:
            calculator = self.kpi_functions.get(kpi_name)
            if not calculator:
                continue

            val, context = self._calculate_single(kpi_name, calculator)
            self.metrics[kpi_name] = {"value": val, **context}
            if "error" not in context:
                self._log_event("kpi_calculated", "success", kpi=kpi_name, value=val)

        # Compute composite PortfolioHealth
        if include_composite:
            par30_val = self.get_metric("PAR30")
            collection_val = self.get_metric("CollectionRate")

            if par30_val is not None and collection_val is not None:
                val, context = self.calculate_portfolio_health(par30_val, collection_val)
                self.metrics["PortfolioHealth"] = {"value": val, **context}
                if "error" not in context:
                    self._log_event("composite_kpi_calculated", "success", kpi="PortfolioHealth")

        self._log_event("calculate_all", "completed", kpi_count=len(self.metrics))
        return self.metrics

    def get_audit_trail(self) -> pd.DataFrame:
        """Return audit trail as DataFrame."""
        return pd.DataFrame(self.audit_trail) if self.audit_trail else pd.DataFrame()

    def get_metric(self, name: str) -> Optional[float]:
        """Helper to get a single metric value by name."""
        if name in self.metrics:
            return self.metrics[name].get("value")

        calculator = self.kpi_functions.get(name) or self.on_demand_kpi_functions.get(name)
        if calculator:
            val, _ = self._calculate_single(name, calculator)
            return val

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
