"""Target loading and variance calculation for 2026 portfolio goals."""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

PORTFOLIO_TARGETS_2026 = {
    "Jan": Decimal("8500000"),
    "Feb": Decimal("9000000"),
    "Mar": Decimal("9300000"),
    "Apr": Decimal("9600000"),
    "May": Decimal("9900000"),
    "Jun": Decimal("10200000"),
    "Jul": Decimal("10500000"),
    "Aug": Decimal("10800000"),
    "Sep": Decimal("11100000"),
    "Oct": Decimal("11400000"),
    "Nov": Decimal("11700000"),
    "Dec": Decimal("12000000"),
}


class TargetLoader:
    """Load and manage 2026 portfolio targets."""

    def __init__(self, targets: Optional[Dict[str, Decimal]] = None):
        """Initialize target loader with 2026 goals.
        
        Args:
            targets: Optional custom targets. Defaults to 2026 portfolio growth plan.
        """
        self.targets = targets or PORTFOLIO_TARGETS_2026
        self.month_map = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }

    def get_target(self, month: int | str) -> Optional[Decimal]:
        """Get portfolio target for specified month.
        
        Args:
            month: Month number (1-12) or name (Jan-Dec).
            
        Returns:
            Target portfolio value or None if month not found.
        """
        if isinstance(month, int):
            month = self.month_map.get(month, "")
        
        return self.targets.get(month)

    def calculate_variance(self, actual: Decimal, target: Decimal) -> Dict[str, Any]:
        """Calculate variance between actual and target.
        
        Args:
            actual: Actual portfolio value.
            target: Target portfolio value.
            
        Returns:
            Dict with variance_amount, variance_pct, and status.
        """
        if target == 0:
            return {"variance_amount": Decimal(0), "variance_pct": Decimal(0), "status": "INVALID_TARGET"}
        
        variance_amount = actual - target
        variance_pct = (variance_amount / target * Decimal(100)).quantize(Decimal("0.01"))
        
        # Determine status
        if variance_pct >= Decimal(0):
            status = "EXCEEDED" if variance_pct >= Decimal(5) else "ON_TRACK"
        else:
            status = "AT_RISK" if variance_pct <= Decimal(-5) else "ON_TRACK"
        
        return {
            "variance_amount": variance_amount,
            "variance_pct": variance_pct,
            "status": status,
        }

    def load_from_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Load targets from DataFrame (Google Sheets export).
        
        Args:
            df: DataFrame with columns Month, Portfolio_Target, NPL_Target, Default_Rate_Target.
            
        Returns:
            Loaded targets and metadata.
        """
        expected_cols = {"Month", "Portfolio_Target"}
        if not expected_cols.issubset(df.columns):
            raise ValueError(f"Missing required columns. Expected: {expected_cols}, Got: {set(df.columns)}")
        
        targets = {}
        for _, row in df.iterrows():
            month = str(row["Month"]).strip()
            target = Decimal(str(row["Portfolio_Target"]))
            targets[month] = target
        
        self.targets = targets
        logger.info(f"Loaded {len(targets)} targets from DataFrame")
        
        return {
            "count": len(targets),
            "months": list(targets.keys()),
            "total_end_target": targets.get("Dec"),
            "loaded_at": datetime.now().isoformat(),
        }

    def export_targets_table(self) -> pd.DataFrame:
        """Export targets as DataFrame (for database/display).
        
        Returns:
            DataFrame with Month, Portfolio_Target, Cumulative columns.
        """
        rows = []
        for month_num, month_name in self.month_map.items():
            target = self.targets.get(month_name)
            if target:
                rows.append({
                    "month_number": month_num,
                    "month_name": month_name,
                    "portfolio_target": float(target),
                    "target_in_millions": float(target) / 1_000_000,
                })
        
        return pd.DataFrame(rows)

    def compare_actuals_vs_targets(self, actual_by_month: Dict[str, Decimal]) -> pd.DataFrame:
        """Compare actual portfolio values against targets.
        
        Args:
            actual_by_month: Dict mapping month names to actual portfolio values.
            
        Returns:
            DataFrame with actual, target, variance_pct, and status columns.
        """
        rows = []
        for month_name, target in self.targets.items():
            actual = actual_by_month.get(month_name)
            
            if actual is None:
                status_info = {
                    "variance_amount": None,
                    "variance_pct": None,
                    "status": "NO_DATA",
                }
            else:
                status_info = self.calculate_variance(actual, target)
            
            rows.append({
                "month": month_name,
                "target": float(target),
                "actual": float(actual) if actual else None,
                "variance_amount": float(status_info["variance_amount"]) if status_info["variance_amount"] else None,
                "variance_pct": float(status_info["variance_pct"]) if status_info["variance_pct"] else None,
                "status": status_info["status"],
            })
        
        return pd.DataFrame(rows)


def get_2026_targets() -> Dict[str, Decimal]:
    """Returns hardcoded 2026 portfolio growth targets."""
    return PORTFOLIO_TARGETS_2026.copy()
