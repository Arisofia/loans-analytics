from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Tuple

import pandas as pd

from python.kpis.collection_rate import calculate_collection_rate, calculate_par_90
from python.kpis.par_30 import calculate_par_30 as calculate_par_30_metric

logger = logging.getLogger(__name__)


class KPIEngine:
    """Autonomous KPI calculation system with full audit trail."""

    def __init__(self, portfolio_data: pd.DataFrame):
        self.portfolio_data = portfolio_data
        self.run_id = f"kpi_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.audit_trail = []
        self.kpi_results = {}

    def _record_audit(self, metric: str, status: str, value: float | None = None, extra: Dict[str, object] | None = None) -> None:
        entry: Dict[str, object] = {
            "metric": metric,
            "run_id": self.run_id,
            "timestamp": pd.Timestamp.now(),
            "calculation_status": status,
        }
        if value is not None:
            entry["value"] = value
        if extra:
            entry.update(extra)
        self.audit_trail.append(entry)

    def get_audit_trail(self) -> pd.DataFrame:
        """Return complete audit trail for compliance."""
        return pd.DataFrame(self.audit_trail)

    def calculate_par_30(self) -> Tuple[float, Dict[str, float]]:
        required = ["dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd", "total_receivable_usd"]
        missing = [col for col in required if col not in self.portfolio_data.columns]
        if missing:
            self._record_audit("par_30", "failed", extra={"error": f"missing columns: {missing}"})
            raise ValueError(f"Missing required columns for PAR30: {missing}")

        try:
            df = self.portfolio_data.copy()
            for col in required:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            dpd_30_plus = (
                df["dpd_30_60_usd"].sum()
                + df["dpd_60_90_usd"].sum()
                + df["dpd_90_plus_usd"].sum()
            )
            total_receivable = df["total_receivable_usd"].sum()

            if pd.isna(dpd_30_plus) or pd.isna(total_receivable):
                raise ValueError("PAR30 calculation failed: non-numeric values")

            par_30_value = float(0.0 if total_receivable == 0 else (dpd_30_plus / total_receivable) * 100.0)
            details = {
                "30_plus_balance": float(dpd_30_plus),
                "total_receivable": float(total_receivable),
            }
            self._record_audit("par_30", "success", par_30_value, details)
            return par_30_value, details
        except Exception as exc:  # pragma: no cover - audit logging path
            self._record_audit("par_30", "failed", extra={"error": str(exc)})
            raise

    def calculate_collection_rate(self, collections_data: pd.DataFrame | None = None) -> Tuple[float, Dict[str, float]]:
        required = ["total_eligible_usd"]
        if collections_data is None:
            required.append("cash_available_usd")

        missing = [col for col in required if col not in self.portfolio_data.columns]
        if missing:
            self._record_audit("collection_rate", "failed", extra={"error": f"missing columns: {missing}"})
            raise ValueError(f"Missing required columns for collection_rate: {missing}")

        try:
            eligible = pd.to_numeric(self.portfolio_data["total_eligible_usd"], errors="coerce").fillna(0.0).sum()

            if collections_data is not None and "amount" in collections_data.columns:
                cash_series = pd.to_numeric(collections_data["amount"], errors="coerce").fillna(0.0)
            else:
                cash_series = pd.to_numeric(self.portfolio_data.get("cash_available_usd"), errors="coerce").fillna(0.0)

            cash_total = cash_series.sum()
            rate = float(0.0 if eligible == 0 else (cash_total / eligible) * 100.0)

            details: Dict[str, float] = {
                "cash": float(cash_total),
                "eligible": float(eligible),
                "total": float(eligible),
            }
            if collections_data is not None and "amount" in collections_data.columns:
                details["collections"] = float(cash_total)

            self._record_audit("collection_rate", "success", rate, details)
            return rate, details
        except Exception as exc:  # pragma: no cover - audit logging path
            self._record_audit("collection_rate", "failed", extra={"error": str(exc)})
            raise

    def calculate_portfolio_health(self, par_30: float, collection_rate_value: float) -> float:
        if par_30 is None or collection_rate_value is None:
            self._record_audit("portfolio_health", "failed", extra={"error": "missing input values"})
            raise ValueError("par_30 and collection_rate are required")

        try:
            # Simple heuristic: prefer higher collection rates and lower PAR30.
            raw_score = (collection_rate_value - par_30) / 10.0
            health = float(max(0.0, min(10.0, raw_score)))
            self._record_audit("portfolio_health", "success", health)
            return health
        except Exception as exc:  # pragma: no cover - audit logging path
            self._record_audit("portfolio_health", "failed", extra={"error": str(exc)})
            raise

    def validate_calculations(self) -> Dict[str, bool]:
        """Validate all calculations meet data quality gates."""
        validation_results: Dict[str, bool] = {}

        for record in self.audit_trail:
            if record.get("calculation_status") == "success":
                metric = record["metric"]
                value = record.get("value")

                if metric in ["par_30", "par_90", "collection_rate"]:
                    validation_results[metric] = value is not None and 0 <= value <= 100
                elif metric == "portfolio_health":
                    validation_results[metric] = value is not None and 0 <= value <= 10

        return validation_results
