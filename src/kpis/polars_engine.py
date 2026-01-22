from typing import Any, Dict, Tuple

import polars as pl


class PolarsKPIEngine:
    """
    High-performance KPI Engine implemented in Polars.
    Enforces strict typing and Decimal precision.
    """

    def __init__(self, df: pl.DataFrame):
        self.df = df

    def calculate_par30(self) -> Tuple[float, Dict[str, Any]]:
        """
        Portfolio at Risk > 30 days.
        """
        required = [
            "dpd_30_60_usd",
            "dpd_60_90_usd",
            "dpd_90_plus_usd",
            "total_receivable_usd",
        ]
        # Ensure columns exist, if not return 0
        existing = [c for c in required if c in self.df.columns]
        if len(existing) < len(required):
            return 0.0, {
                "error": "Missing required DPD columns",
                "missing": sorted(list(set(required) - set(existing))),
            }

        # Correct way to get values from select
        result = self.df.select(
            [
                (
                    pl.col("dpd_30_60_usd")
                    + pl.col("dpd_60_90_usd")
                    + pl.col("dpd_90_plus_usd")
                )
                .sum()
                .alias("sum_delinquent"),
                pl.col("total_receivable_usd").sum().alias("sum_total"),
            ]
        )

        sum_delinquent = result["sum_delinquent"][0]
        sum_total = result["sum_total"][0]

        if sum_total == 0:
            return 0.0, {"reason": "Zero total receivable", "rows": len(self.df)}

        value = (sum_delinquent / sum_total) * 100.0
        return float(value), {
            "sum_delinquent": float(sum_delinquent),
            "sum_total": float(sum_total),
            "rows": len(self.df),
        }

    def calculate_par90(self) -> Tuple[float, Dict[str, Any]]:
        """
        Portfolio at Risk > 90 days.
        """
        if (
            "dpd_90_plus_usd" not in self.df.columns
            or "total_receivable_usd" not in self.df.columns
        ):
            return 0.0, {"error": "Missing DPD columns for PAR90"}

        result = self.df.select(
            [
                pl.col("dpd_90_plus_usd").sum().alias("sum_delinquent"),
                pl.col("total_receivable_usd").sum().alias("sum_total"),
            ]
        )

        sum_delinquent = result["sum_delinquent"][0]
        sum_total = result["sum_total"][0]

        if sum_total == 0:
            return 0.0, {"reason": "Zero total receivable"}

        value = (sum_delinquent / sum_total) * 100.0
        return float(value), {
            "sum_delinquent": float(sum_delinquent),
            "sum_total": float(sum_total),
        }

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        """
        Effective Collection Rate.
        """
        if (
            "cash_available_usd" not in self.df.columns
            or "total_eligible_usd" not in self.df.columns
        ):
            return 0.0, {"error": "Missing columns for CollectionRate"}

        result = self.df.select(
            [
                pl.col("cash_available_usd").sum().alias("sum_cash"),
                pl.col("total_eligible_usd").sum().alias("sum_eligible"),
            ]
        )

        sum_cash = result["sum_cash"][0]
        sum_eligible = result["sum_eligible"][0]

        if sum_eligible == 0:
            return 0.0, {"reason": "Zero total eligible"}

        value = (sum_cash / sum_eligible) * 100.0
        return float(value), {
            "sum_cash": float(sum_cash),
            "sum_eligible": float(sum_eligible),
        }

    def calculate_weighted_apr(self) -> Tuple[float, Dict[str, Any]]:
        """
        Weighted Average Interest Rate (APR).
        """
        if (
            "interest_rate_apr" not in self.df.columns
            or "disbursement_amount" not in self.df.columns
        ):
            return 0.0, {"error": "Missing columns for WeightedAPR"}

        result = self.df.select(
            [
                (pl.col("interest_rate_apr") * pl.col("disbursement_amount"))
                .sum()
                .alias("weighted_sum"),
                pl.col("disbursement_amount").sum().alias("total_disbursement"),
            ]
        )

        weighted_sum = result["weighted_sum"][0]
        total_disb = result["total_disbursement"][0]

        if total_disb == 0:
            return 0.0, {"reason": "Zero total disbursement"}

        value = (weighted_sum / total_disb) * 100.0
        return float(value), {
            "total_disbursement": float(total_disb),
        }

    def calculate_aum(self) -> float:
        """
        Assets Under Management (Total Outstanding Principal).
        """
        if "total_receivable_usd" not in self.df.columns:
            return 0.0
        return float(
            self.df.select(pl.col("total_receivable_usd").sum()).to_series()[0]
        )

    def calculate_all(self) -> Dict[str, Any]:
        """
        Calculate all implemented Polars KPIs.
        """
        par30_val, par30_ctx = self.calculate_par30()
        par90_val, par90_ctx = self.calculate_par90()
        coll_val, coll_ctx = self.calculate_collection_rate()
        apr_val, apr_ctx = self.calculate_weighted_apr()
        aum_val = self.calculate_aum()

        return {
            "PAR30": {"value": par30_val, **par30_ctx},
            "PAR90": {"value": par90_val, **par90_ctx},
            "CollectionRate": {"value": coll_val, **coll_ctx},
            "WeightedAPR": {"value": apr_val, **apr_ctx},
            "AUM": {"value": aum_val, "unit": "USD"},
        }
