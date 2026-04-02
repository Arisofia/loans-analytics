"""Target loading and variance calculation for 2026 portfolio goals.

Source of truth: ``config/business_parameters.yml`` via application settings.
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

import pandas as pd
from backend.loans_analytics.config import settings

logger = logging.getLogger(__name__)

MONTH_ABBREV_TO_NUM = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def _targets_from_settings() -> Dict[str, Decimal]:
    """Load monthly targets from app settings and normalize to Jan-Dec keys."""
    targets_by_ym = getattr(settings, "portfolio_targets_2026", {}) or {}
    by_month_num: Dict[int, Decimal] = {}
    for ym_key, raw_value in targets_by_ym.items():
        try:
            year_str, month_str = str(ym_key).split("-", 1)
            if year_str != "2026":
                continue
            month_num = int(month_str)
            if 1 <= month_num <= 12:
                by_month_num[month_num] = Decimal(str(raw_value))
        except (ValueError, ArithmeticError):
            continue

    if len(by_month_num) != 12:
        logger.warning(
            "portfolio_targets_2026 is incomplete (%d/12). Falling back to conservative defaults.",
            len(by_month_num),
        )
        return {
            "Jan": Decimal("8500000"),
            "Feb": Decimal("8800000"),
            "Mar": Decimal("9100000"),
            "Apr": Decimal("9400000"),
            "May": Decimal("9700000"),
            "Jun": Decimal("10000000"),
            "Jul": Decimal("10300000"),
            "Aug": Decimal("10600000"),
            "Sep": Decimal("10900000"),
            "Oct": Decimal("11200000"),
            "Nov": Decimal("11600000"),
            "Dec": Decimal("12000000"),
        }

    return {
        "Jan": by_month_num[1],
        "Feb": by_month_num[2],
        "Mar": by_month_num[3],
        "Apr": by_month_num[4],
        "May": by_month_num[5],
        "Jun": by_month_num[6],
        "Jul": by_month_num[7],
        "Aug": by_month_num[8],
        "Sep": by_month_num[9],
        "Oct": by_month_num[10],
        "Nov": by_month_num[11],
        "Dec": by_month_num[12],
    }


PORTFOLIO_TARGETS_2026 = _targets_from_settings()


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
            Target portfolio value as Decimal.
            
        Raises:
            ValueError: If month is invalid.
        """
        if isinstance(month, int):
            if not 1 <= month <= 12:
                raise ValueError(f"Month number must be 1-12, got {month}")
            month = self.month_map.get(month, "")
        else:
            month_str = str(month).strip()
            if month_str not in self.targets:
                for target_month in self.targets.keys():
                    if target_month.lower() == month_str.lower():
                        month = target_month
                        break
            else:
                month = month_str
        
        if month not in self.targets:
            raise ValueError(f"Invalid month: {month}")
        
        return self.targets[month]

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
        
        if variance_pct >= Decimal(5):
            status = "EXCEEDED"
        elif variance_pct >= Decimal(-5):
            status = "ON_TRACK"
        else:
            status = "AT_RISK"
        
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
            "status": "success",
            "rows_loaded": len(targets),
            "months_loaded": list(targets.keys()),
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

    def compare_actuals_vs_targets(self, actual_by_month: Dict) -> pd.DataFrame:
        """Compare actual portfolio values against targets.
        
        Args:
            actual_by_month: Dict mapping month names (str) or month numbers (int)
                to actual portfolio values.
            
        Returns:
            DataFrame with actual_portfolio, target, variance_pct, and status columns.
        """
        normalised: Dict[str, Decimal] = {}
        for key, value in actual_by_month.items():
            if isinstance(key, int):
                month_name = self.month_map.get(key)
                if month_name:
                    normalised[month_name] = value
            else:
                normalised[str(key)] = value

        rows = []
        for month_name, target in self.targets.items():
            actual = normalised.get(month_name)
            
            if actual is None:
                status_info = {
                    "variance_amount": None,
                    "variance_pct": None,
                    "status": "NO_DATA",
                }
            else:
                status_info = self.calculate_variance(Decimal(str(actual)), target)
            
            rows.append({
                "month": month_name,
                "target": float(target),
                "actual_portfolio": float(actual) if actual is not None else None,
                "variance_amount": float(status_info["variance_amount"]) if status_info["variance_amount"] else None,
                "variance_pct": float(status_info["variance_pct"]) if status_info["variance_pct"] else None,
                "status": status_info["status"],
            })
        
        return pd.DataFrame(rows)


def get_2026_targets() -> Dict[str, Decimal]:
    """Returns normalized 2026 monthly targets loaded from app settings."""
    return PORTFOLIO_TARGETS_2026.copy()
