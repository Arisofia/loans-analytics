"""Lightweight KPI catalog processor for Streamlit dashboards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class KPICatalogProcessor:
    """Compute summary KPIs from core loan, payment, and customer datasets."""

    loans_df: pd.DataFrame
    payments_df: pd.DataFrame
    customers_df: pd.DataFrame
    schedule_df: Optional[pd.DataFrame] = None

    def __post_init__(self) -> None:
        self.loans_df = self.loans_df if self.loans_df is not None else pd.DataFrame()
        self.payments_df = self.payments_df if self.payments_df is not None else pd.DataFrame()
        self.customers_df = self.customers_df if self.customers_df is not None else pd.DataFrame()
        self.schedule_df = self.schedule_df if self.schedule_df is not None else pd.DataFrame()

    def get_all_kpis(self) -> dict:
        """Return a dictionary of computed KPIs for dashboard consumption."""
        total_loans = (
            int(self.loans_df["loan_id"].nunique()) if "loan_id" in self.loans_df.columns else 0
        )
        total_customers = (
            int(self.customers_df["customer_id"].nunique())
            if "customer_id" in self.customers_df.columns
            else (
                int(self.customers_df["client_id"].nunique())
                if "client_id" in self.customers_df.columns
                else 0
            )
        )
        total_outstanding = (
            float(self.loans_df["outstanding_loan_value"].sum())
            if "outstanding_loan_value" in self.loans_df.columns
            else 0.0
        )
        avg_apr = 0.0
        if {
            "interest_rate_apr",
            "outstanding_loan_value",
        }.issubset(self.loans_df.columns):
            total_balance = self.loans_df["outstanding_loan_value"].sum()
            if total_balance:
                avg_apr = float(
                    (
                        self.loans_df["interest_rate_apr"] * self.loans_df["outstanding_loan_value"]
                    ).sum()
                    / total_balance
                )
        executive_strip = {
            "total_loans": total_loans,
            "total_customers": total_customers,
            "total_outstanding_loan_value": total_outstanding,
            "avg_apr": avg_apr,
        }
        return {"executive_strip": executive_strip}

    def get_quarterly_scorecard(self) -> pd.DataFrame:
        """Create a quarterly scorecard from available payment data."""
        if self.payments_df.empty:
            return pd.DataFrame()
        date_col = next(
            (
                col
                for col in ("payment_date", "month", "date", "paid_at", "posted_at")
                if col in self.payments_df.columns
            ),
            None,
        )
        if date_col is None:
            return pd.DataFrame()
        amount_col = next(
            (
                col
                for col in (
                    "payment_amount",
                    "amount",
                    "total_payment",
                    "payment",
                    "amount_paid",
                )
                if col in self.payments_df.columns
            ),
            None,
        )
        if amount_col is None:
            return pd.DataFrame()
        scored = self.payments_df.copy()
        scored[date_col] = pd.to_datetime(scored[date_col], errors="coerce")
        scored = scored.dropna(subset=[date_col])
        if scored.empty:
            return pd.DataFrame()
        quarterly = (
            scored.groupby(pd.Grouper(key=date_col, freq="Q"))[amount_col]
            .sum()
            .reset_index()
            .rename(columns={date_col: "quarter_end", amount_col: "total_payments"})
        )
        quarterly["quarter"] = quarterly["quarter_end"].dt.to_period("Q").astype(str)
        return quarterly[["quarter", "total_payments"]]

    def get_monthly_revenue_df(self) -> pd.DataFrame:
        """Build a monthly revenue metrics frame for dashboard charts."""
        if self.payments_df.empty:
            return pd.DataFrame()
        date_col = next(
            (
                col
                for col in ("payment_date", "month", "date", "paid_at", "posted_at")
                if col in self.payments_df.columns
            ),
            None,
        )
        if date_col is None:
            return pd.DataFrame()
        amount_col = next(
            (
                col
                for col in (
                    "payment_amount",
                    "amount",
                    "total_payment",
                    "payment",
                    "amount_paid",
                )
                if col in self.payments_df.columns
            ),
            None,
        )
        if amount_col is None:
            return pd.DataFrame()
        monthly = self.payments_df.copy()
        monthly[date_col] = pd.to_datetime(monthly[date_col], errors="coerce")
        monthly = monthly.dropna(subset=[date_col])
        if monthly.empty:
            return pd.DataFrame()
        monthly["month"] = monthly[date_col].dt.to_period("M").dt.to_timestamp()
        summary = (
            monthly.groupby("month")[amount_col]
            .sum()
            .reset_index()
            .rename(columns={amount_col: "recv_revenue_for_month"})
        )
        return summary
