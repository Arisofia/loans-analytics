from datetime import datetime
from typing import Optional

import polars as pl


class FactoringService:
    """
    Core business logic for factoring: Dilution, Aging, and Recourse.
    Implemented using high-performance Polars expressions.
    """

    @staticmethod
    def calculate_aging(
        df_invoices: pl.DataFrame, reference_date: Optional[datetime] = None
    ) -> pl.DataFrame:
        """
        Categorize invoices into aging buckets.
        """
        if reference_date is None:
            reference_date = datetime.now()

        ref_date = pl.lit(reference_date).cast(pl.Date)

        return df_invoices.with_columns(
            [
                (ref_date - pl.col("disbursement_date"))
                .dt.total_days()
                .alias("days_since_disbursement")
            ]
        ).with_columns(
            [
                pl.when(pl.col("days_past_due") <= 0)
                .then(pl.lit("Current"))
                .when(pl.col("days_past_due") <= 30)
                .then(pl.lit("0-30"))
                .when(pl.col("days_past_due") <= 60)
                .then(pl.lit("31-60"))
                .when(pl.col("days_past_due") <= 90)
                .then(pl.lit("61-90"))
                .otherwise(pl.lit("90+"))
                .alias("aging_bucket")
            ]
        )

    @staticmethod
    def calculate_dilution(
        df_payments: pl.DataFrame, df_invoices: pl.DataFrame
    ) -> float:
        """
        Calculate Portfolio Dilution: (Non-Cash Reductions) / Gross Sales.
        """
        # Non-Cash Reductions are typically 'true_rebates'
        total_rebates = df_payments.select(pl.col("true_rebates").sum()).to_series()[0]
        gross_sales = df_invoices.select(
            pl.col("disbursement_amount").sum()
        ).to_series()[0]

        if not gross_sales or gross_sales == 0:
            return 0.0

        return float(total_rebates / gross_sales)

    @staticmethod
    def apply_recourse_logic(df_invoices: pl.DataFrame) -> pl.DataFrame:
        """
        Identify invoices eligible for recourse (chargeback) based on aging.
        """
        return df_invoices.with_columns(
            [
                pl.when(pl.col("days_past_due") > 90)
                .then(pl.lit("Eligible for Recourse"))
                .otherwise(pl.lit("Standard"))
                .alias("recourse_status")
            ]
        )
