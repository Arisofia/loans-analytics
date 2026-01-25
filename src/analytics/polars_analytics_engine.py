from typing import Dict

import polars as pl

from python.config import settings
from python.schemas import LOAN_SCHEMA


class PolarsAnalyticsEngine:
    """
    High-performance Polars-native analytics engine.
    Uses Lazy execution and strictly vectorized expressions.
    """

    def __init__(self, data: pl.DataFrame):
        # Enforce schema on entry
        self.df = data.cast(LOAN_SCHEMA)
        self._lazy_plan = self.df.lazy()

    @classmethod
    def from_csv(cls, path: str) -> "PolarsAnalyticsEngine":
        """Scan CSV with strict schema enforcement (Lazy)."""
        lf = pl.scan_csv(path, schema=LOAN_SCHEMA)
        return cls(lf.collect())

    def compute_ratios(self) -> pl.LazyFrame:
        """
        Refactored Expressions: Replace apply with vectorized logic.
        Explicitly handles nulls and avoids division by zero.
        """
        return self._lazy_plan.with_columns(
            [
                # LTV Ratio: (Loan / Appraised) * 100
                pl.when(pl.col("appraised_value") > 0)
                .then((pl.col("loan_amount") / pl.col("appraised_value")) * 100)
                .otherwise(None)
                .alias("ltv_ratio"),
                # DTI Ratio: (Monthly Debt / (Annual Income / 12)) * 100
                pl.when(pl.col("borrower_income") > 0)
                .then((pl.col("monthly_debt") / (pl.col("borrower_income") / 12)) * 100)
                .otherwise(None)
                .alias("dti_ratio"),
            ]
        )

    def compute_kpis(self) -> Dict[str, float]:
        """Execute the lazy plan and aggregate results."""
        # 1. Define aggregation expressions
        delinquent_statuses = list(settings.analytics.delinquent_statuses)

        agg_plan = self.compute_ratios().select(
            [
                # Delinquency Rate: % of loans in delinquent status
                (pl.col("loan_status").is_in(delinquent_statuses).sum() / pl.len() * 100).alias(
                    "delinquency_rate"
                ),
                # Portfolio Yield: Weighted average interest rate
                (
                    (pl.col("interest_rate") * pl.col("principal_balance")).sum()
                    / pl.col("principal_balance").sum()
                    * 100
                ).alias("portfolio_yield"),
                # Average Ratios (ignoring nulls automatically)
                pl.col("ltv_ratio").mean().alias("avg_ltv"),
                pl.col("dti_ratio").mean().alias("avg_dti"),
            ]
        )

        # 2. Collect and return as dict
        result = agg_plan.collect().to_dicts()[0]

        # Ensure all metrics are floats and handle missing values
        return {k: float(v) if v is not None else 0.0 for k, v in result.items()}

    def get_risk_alerts(self) -> pl.DataFrame:
        """Identify high-risk loans using lazy filtering."""
        ltv_threshold = 90.0
        dti_threshold = 40.0

        return (
            self.compute_ratios()
            .filter((pl.col("ltv_ratio") > ltv_threshold) | (pl.col("dti_ratio") > dti_threshold))
            .collect()
        )
