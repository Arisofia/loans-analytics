import logging
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from .utils import select_column

logger = logging.getLogger("abaco.looker")

# Constants for column names and strategies
STRATEGY_TODAY = "today"
STRATEGY_MAX_DISBURSE = "max_disburse_date"
STRATEGY_MAX_MATURITY = "max_maturity_date"

DEFAULT_DATE_CANDIDATES = ["reporting_date", "as_of_date", "date", "fecha", "fecha_corte"]
DEFAULT_CASH_CANDIDATES = ["cash_balance_usd", "cash_balance", "cash_usd", "cash"]
DEFAULT_DISBURSE_CANDIDATES = ["disburse_date", "disbursement_date"]
DEFAULT_MATURITY_CANDIDATES = ["maturity_date", "loan_end_date"]

# DPD (Days Past Due) threshold constants aligned with loan tape bucket definitions
DPD_THRESHOLD_7 = 7
DPD_THRESHOLD_30 = 30
DPD_THRESHOLD_60 = 60
DPD_THRESHOLD_90 = 90

class LookerConverter:
    """Specialized converter for Looker snapshots and financial summaries."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("looker", {})

    def load_financials(self, financials_path: Optional[Path]) -> Dict[str, float]:
        if not financials_path:
            return {}
        path = Path(financials_path)
        if path.is_dir():
            candidates = sorted(
                [
                    *path.glob("*.csv"),
                    *path.glob("*.xlsx"),
                    *path.glob("*.xls"),
                ],
                key=lambda p: p.stat().st_mtime,
            )
            if not candidates:
                return {}
            path = candidates[-1]
        if not path.exists():
            return {}

        try:
            if path.suffix.lower() in {".xlsx", ".xls"}:
                financials_df = pd.read_excel(path)
            else:
                financials_df = pd.read_csv(path)
        except Exception as exc:
            logger.error("Failed to read Looker financials: %s", exc)
            return {}

        date_candidates = self.config.get(
            "date_column_candidates",
            DEFAULT_DATE_CANDIDATES,
        )
        cash_candidates = self.config.get(
            "cash_column_candidates",
            DEFAULT_CASH_CANDIDATES,
        )
        date_col = select_column(list(financials_df.columns), date_candidates)
        cash_col = select_column(list(financials_df.columns), cash_candidates)
        if not date_col or not cash_col:
            return {}

        parsed = financials_df[[date_col, cash_col]].copy()
        parsed[date_col] = pd.to_datetime(parsed[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
        parsed[cash_col] = pd.to_numeric(parsed[cash_col], errors="coerce")
        parsed = parsed.dropna(subset=[date_col])
        grouped = parsed.groupby(date_col, dropna=False)[cash_col].last()
        return {str(idx): float(val) for idx, val in grouped.items() if pd.notna(val)}

    def convert_par_balances(
        self, df: pd.DataFrame, cash_by_date: Dict[str, float]
    ) -> pd.DataFrame:
        column_map = {col.lower(): col for col in df.columns}
        reporting_col = column_map.get("reporting_date")
        outstanding_col = column_map.get("outstanding_balance_usd") or column_map.get(
            "outstanding_balance"
        )
        par_7_col = column_map.get("par_7_balance_usd")
        par_30_col = column_map.get("par_30_balance_usd")
        par_60_col = column_map.get("par_60_balance_usd")
        par_90_col = column_map.get("par_90_balance_usd")

        missing = [
            name
            for name, col in {
                "reporting_date": reporting_col,
                "outstanding_balance_usd": outstanding_col,
                "par_7_balance_usd": par_7_col,
                "par_30_balance_usd": par_30_col,
                "par_60_balance_usd": par_60_col,
                "par_90_balance_usd": par_90_col,
            }.items()
            if col is None
        ]
        if missing:
            raise ValueError(f"Missing Looker PAR columns: {', '.join(missing)}")

        measurement_date = pd.to_datetime(df[reporting_col], errors="coerce").dt.strftime(
            "%Y-%m-%d"
        )
        total_receivable = pd.to_numeric(df[outstanding_col], errors="coerce")
        par_7 = pd.to_numeric(df[par_7_col], errors="coerce")
        par_30 = pd.to_numeric(df[par_30_col], errors="coerce")
        par_60 = pd.to_numeric(df[par_60_col], errors="coerce")
        par_90 = pd.to_numeric(df[par_90_col], errors="coerce")

        frame = pd.DataFrame(
            {
                "measurement_date": measurement_date,
                "total_receivable_usd": total_receivable,
                "dpd_90_plus_usd": par_90,
                "dpd_60_90_usd": (par_60 - par_90).clip(lower=0),
                "dpd_30_60_usd": (par_30 - par_60).clip(lower=0),
                "dpd_7_30_usd": (par_7 - par_30).clip(lower=0),
                "dpd_0_7_usd": (total_receivable - par_7).clip(lower=0),
            }
        ).dropna(subset=["measurement_date"])

        grouped = (
            frame.groupby("measurement_date", dropna=False).sum(numeric_only=True).reset_index()
        )
        grouped["total_eligible_usd"] = grouped["total_receivable_usd"]
        grouped["discounted_balance_usd"] = grouped["total_receivable_usd"]
        grouped["cash_available_usd"] = grouped["measurement_date"].map(cash_by_date).fillna(0.0)
        grouped["loan_id"] = grouped["measurement_date"].apply(
            lambda date: f"looker_snapshot_{str(date).replace('-', '')}"
        )
        return grouped

    def convert_dpd_loans(
        self, df: pd.DataFrame, cash_by_date: Dict[str, float]
    ) -> pd.DataFrame:
        column_map = {col.lower(): col for col in df.columns}
        dpd_col = column_map.get("dpd") or column_map.get("days_past_due")
        balance_col = column_map.get("outstanding_balance_usd") or column_map.get(
            "outstanding_balance"
        )
        if not dpd_col or not balance_col:
            raise ValueError("Missing Looker loan columns: dpd, outstanding_balance")

        measurement_col = self.config.get("measurement_date_column")
        strategy = self.config.get("measurement_date_strategy", STRATEGY_TODAY)

        measurement_date = None
        if measurement_col:
            resolved = select_column(list(df.columns), [measurement_col])
            if resolved:
                measurement_date = pd.to_datetime(df[resolved], errors="coerce").dt.strftime(
                    "%Y-%m-%d"
                )
        if measurement_date is None:
            if strategy == STRATEGY_MAX_DISBURSE:
                resolved = select_column(
                    list(df.columns), DEFAULT_DISBURSE_CANDIDATES
                )
            elif strategy == STRATEGY_MAX_MATURITY:
                resolved = select_column(list(df.columns), DEFAULT_MATURITY_CANDIDATES)
            else:
                resolved = None
            if resolved:
                max_date = pd.to_datetime(df[resolved], errors="coerce").max()
                date_value = max_date.date().isoformat() if pd.notna(max_date) else None
            else:
                date_value = None
            if not date_value:
                date_value = datetime.now(timezone.utc).date().isoformat()
            measurement_date = pd.Series([date_value] * len(df), index=df.index)

        balance = pd.to_numeric(df[balance_col], errors="coerce").fillna(0.0)
        dpd = pd.to_numeric(df[dpd_col], errors="coerce").fillna(0.0)

        frame = pd.DataFrame(
            {
                "measurement_date": measurement_date,
                "total_receivable_usd": balance,
                "dpd_90_plus_usd": balance.where(dpd >= DPD_THRESHOLD_90, 0.0),
                "dpd_60_90_usd": balance.where(
                    (dpd >= DPD_THRESHOLD_60) & (dpd < DPD_THRESHOLD_90), 0.0
                ),
                "dpd_30_60_usd": balance.where(
                    (dpd >= DPD_THRESHOLD_30) & (dpd < DPD_THRESHOLD_60), 0.0
                ),
                "dpd_7_30_usd": balance.where(
                    (dpd >= DPD_THRESHOLD_7) & (dpd < DPD_THRESHOLD_30), 0.0
                ),
                "dpd_0_7_usd": balance.where(dpd < DPD_THRESHOLD_7, 0.0),
            }
        ).dropna(subset=["measurement_date"])

        grouped = (
            frame.groupby("measurement_date", dropna=False).sum(numeric_only=True).reset_index()
        )
        grouped["total_eligible_usd"] = grouped["total_receivable_usd"]
        grouped["discounted_balance_usd"] = grouped["total_receivable_usd"]
        grouped["cash_available_usd"] = grouped["measurement_date"].map(cash_by_date).fillna(0.0)
        grouped["loan_id"] = grouped["measurement_date"].apply(
            lambda date: f"looker_snapshot_{str(date).replace('-', '')}"
        )
        return grouped
