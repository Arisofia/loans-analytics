import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Callable

import pandas as pd

from python.kpis.collection_rate import calculate_collection_rate
from python.kpis.par_30 import calculate_par_30
from python.kpis.par_90 import calculate_par_90
from python.kpis.portfolio_health import calculate_portfolio_health
from python.validation import NUMERIC_COLUMNS, validate_dataframe

logger = logging.getLogger(__name__)


class MetricDefinition:
    """Define a KPI metric configuration."""
    
    def __init__(
        self,
        name: str,
        calculator: Callable,
        required_columns: List[str],
        denominator_field: str = None
    ):
        self.name = name
        self.calculator = calculator
        self.required_columns = required_columns
        self.denominator_field = denominator_field


class KPIEngine:
    """Orchestrate KPI calculations with audit trail and error handling."""
    
    METRICS = {
        'PAR30': MetricDefinition(
            'PAR30',
            calculate_par_30,
            ['dpd_30_60_usd', 'dpd_60_90_usd', 'dpd_90_plus_usd', 'total_receivable_usd'],
            'total_receivable_usd'
        ),
        'PAR90': MetricDefinition(
            'PAR90',
            calculate_par_90,
            ['dpd_90_plus_usd', 'total_receivable_usd'],
            'total_receivable_usd'
        ),
        'CollectionRate': MetricDefinition(
            'CollectionRate',
            calculate_collection_rate,
            ['cash_available_usd', 'total_eligible_usd'],
            'total_eligible_usd'
        ),
    }

    def __init__(self, df: pd.DataFrame, actor: str = "system", action: str = "kpi"):
        self.df = df
        self.audit_trail: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.actor = actor
        self.action = action

    def _log(self, level: int, message: str, **details: Any) -> None:
        payload = {"actor": self.actor, "action": self.action, **details}
        logger.log(level, f"[kpi] {message} | {payload}")

    def _record_error(self, metric: str, message: str, **details: Any) -> None:
        payload = {
            "metric": metric,
            "error": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.actor,
            "action": self.action,
            **details,
        }
        self.errors.append(payload)
        self._log(logging.ERROR, message, metric=metric, **details)

    def _record_warning(self, metric: str, message: str, **details: Any) -> None:
        payload = {
            "metric": metric,
            "warning": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.actor,
            "action": self.action,
            **details,
        }
        self.warnings.append(payload)
        self._log(logging.WARNING, message, metric=metric, **details)

    def _log_metric(
        self, metric: str, value: float, method: str = "standard", status: str = "ok", **ctx: Any
    ) -> Dict[str, Any]:
        entry = {
            "metric": metric,
            "method": method,
            "status": status,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.actor,
            "action": self.action,
            **ctx,
        }
        self.audit_trail.append(entry)
        self._log(
            logging.INFO if status == "ok" else logging.WARNING,
            f"{metric} computed",
            status=status,
            value=value,
            method=method,
        )
        return entry

    def _ensure_columns(self, metric: str, required_cols: List[str]) -> bool:
        missing = [c for c in required_cols if c not in self.df.columns]
        if missing:
            msg = f"Missing required columns for {metric}: {missing}"
            self._record_error(metric, msg, missing=missing)
            self._log_metric(metric, 0.0, status="error", missing=missing)
            return False
        return True

    def _warn_if_zero(self, metric: str, denominator_name: str, denominator_value: float) -> None:
        if denominator_value == 0:
            self._record_warning(
                metric, f"{denominator_name} is zero; returning 0", denominator=denominator_name
            )

    def calculate_metric(self, metric_key: str) -> Tuple[float, Dict[str, Any]]:
        """Calculate a KPI metric using its definition."""
        if metric_key not in self.METRICS:
            raise ValueError(f"Unknown metric: {metric_key}")
        
        metric_def = self.METRICS[metric_key]
        
        if not self._ensure_columns(metric_def.name, metric_def.required_columns):
            return 0.0, {"metric": metric_def.name, "status": "error", "value": 0.0}
        
        val = float(metric_def.calculator(self.df))
        
        if val == 0.0 and metric_def.denominator_field:
            denom_value = float(self.df.get(metric_def.denominator_field, pd.Series()).sum())
            self._warn_if_zero(metric_def.name, metric_def.denominator_field, denom_value)
        
        ctx = self._log_metric(metric_def.name, val)
        return val, ctx

    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate PAR30 metric."""
        return self.calculate_metric('PAR30')

    def calculate_par_90(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate PAR90 metric."""
        return self.calculate_metric('PAR90')

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate Collection Rate metric."""
        return self.calculate_metric('CollectionRate')

    def calculate_portfolio_health(
        self, par_30: float, collection_rate: float
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate portfolio health score."""
        val = calculate_portfolio_health(par_30, collection_rate)
        ctx = self._log_metric("HealthScore", val)
        return val, ctx

    def validate_schema(self):
        """Validate that the DataFrame contains required numeric columns for KPI calculation."""
        try:
            validate_dataframe(self.df, required_columns=NUMERIC_COLUMNS)
            self._log(logging.INFO, "Schema validation passed")
        except ValueError as exc:
            message = str(exc)
            self._record_error("schema", message)
            raise

    def get_audit_trail(self) -> pd.DataFrame:
        """Return audit trail as DataFrame."""
        return pd.DataFrame(self.audit_trail)
