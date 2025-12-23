import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import pandas as pd

from python.kpis.collection_rate import calculate_collection_rate
from python.kpis.par_30 import calculate_par_30
from python.kpis.par_90 import calculate_par_90
from python.kpis.portfolio_health import calculate_portfolio_health
from python.validation import NUMERIC_COLUMNS, validate_dataframe

logger = logging.getLogger(__name__)


class KPIEngine:
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

    def validate_schema(self):
        """Validate that the DataFrame contains required numeric columns for KPI calculation."""
        try:
            validate_dataframe(self.df, required_columns=NUMERIC_COLUMNS)
            self._log(logging.INFO, "Schema validation passed")
        except ValueError as exc:
            message = str(exc)
            self._record_error("schema", message)
            raise

    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        required = ["dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd", "total_receivable_usd"]
        if not self._ensure_columns("PAR30", required):
            return 0.0, {"metric": "PAR30", "status": "error", "value": 0.0}
        val = float(calculate_par_30(self.df))
        if val == 0.0:
            total = float(self.df.get("total_receivable_usd", pd.Series()).sum())
            self._warn_if_zero("PAR30", "total_receivable_usd", total)
        ctx = self._log_metric("PAR30", val)
        return val, ctx

    def calculate_par_90(self) -> Tuple[float, Dict[str, Any]]:
        required = ["dpd_90_plus_usd", "total_receivable_usd"]
        if not self._ensure_columns("PAR90", required):
            return 0.0, {"metric": "PAR90", "status": "error", "value": 0.0}
        val = float(calculate_par_90(self.df))
        if val == 0.0:
            total = float(self.df.get("total_receivable_usd", pd.Series()).sum())
            self._warn_if_zero("PAR90", "total_receivable_usd", total)
        ctx = self._log_metric("PAR90", val)
        return val, ctx

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        required = ["cash_available_usd", "total_eligible_usd"]
        if not self._ensure_columns("CollectionRate", required):
            return 0.0, {"metric": "CollectionRate", "status": "error", "value": 0.0}
        val = float(calculate_collection_rate(self.df))
        if val == 0.0:
            eligible = float(self.df.get("total_eligible_usd", pd.Series()).sum())
            self._warn_if_zero("CollectionRate", "total_eligible_usd", eligible)
        ctx = self._log_metric("CollectionRate", val)
        return val, ctx

    def calculate_portfolio_health(
        self, par_30: float, collection_rate: float
    ) -> Tuple[float, Dict[str, Any]]:
        val = calculate_portfolio_health(par_30, collection_rate)
        ctx = self._log_metric("HealthScore", val)
        return val, ctx

    def get_audit_trail(self) -> pd.DataFrame:
        return pd.DataFrame(self.audit_trail)
