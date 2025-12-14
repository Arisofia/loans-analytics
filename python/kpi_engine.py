import logging
from datetime import datetime
from typing import Dict, Tuple

import pandas as pd

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
        except Exception as exc:
            self._record_audit("par_30", "failed", extra={"error": str(exc)})
            raise

    def calculate_collection_rate(self, collections_data: pd.DataFrame | None = None) -> Tuple[float, Dict[str, float]]:
        required = ["total_eligible_usd"]
        if collections_data is None:
            required.append("cash_available_usd")

        missing = [col for col in required if col not in self.portfolio_data.columns]
        if missing:
            self._record_audit("collection_rate", "failed", extra={"error": f"missing columns: {missing}"})
            raise ValueError(f"Missing required columns: {missing}")

        try:
            df = self.portfolio_data.copy()
            for col in required:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            if collections_data is not None:
                collections_sum = collections_data.sum()
            else:
                collections_sum = df["cash_available_usd"].sum()

            total_eligible = df["total_eligible_usd"].sum()

            if pd.isna(collections_sum) or pd.isna(total_eligible):
                raise ValueError("Collection rate calculation failed: non-numeric values")

            collection_rate_value = float(0.0 if total_eligible == 0 else (collections_sum / total_eligible) * 100.0)
            details = {
                "collections": float(collections_sum),
                "total_eligible": float(total_eligible),
            }
            self._record_audit("collection_rate", "success", collection_rate_value, details)
            return collection_rate_value, details
        except Exception as exc:
            self._record_audit("collection_rate", "failed", extra={"error": str(exc)})
            raise

    def calculate_all_kpis(self) -> Dict[str, Tuple[float, Dict[str, float]]]:
        """Calculate all KPIs and return results with audit trail."""
        results = {}

        try:
            par_30_value, par_30_details = self.calculate_par_30()
            results["par_30"] = (par_30_value, par_30_details)
        except ValueError as e:
            logger.warning(f"PAR30 calculation failed: {e}")

        try:
            collection_rate, collection_details = self.calculate_collection_rate()
            results["collection_rate"] = (collection_rate, collection_details)
        except ValueError as e:
            logger.warning(f"Collection rate calculation failed: {e}")

        self.kpi_results = results
        return results

    def get_summary(self) -> Dict[str, object]:
        """Return KPI summary for reporting."""
        return {
            "run_id": self.run_id,
            "kpi_count": len(self.kpi_results),
            "kpis": self.kpi_results,
            "audit_trail": self.audit_trail,
        }
