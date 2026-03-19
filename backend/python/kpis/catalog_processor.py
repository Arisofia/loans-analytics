"""KPI catalog processor for Streamlit dashboards and strategic reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.python.kpis.graph_analytics import build_graph_kpi_report
from backend.python.kpis.lending_kpis import build_lending_kpi_report
from backend.python.kpis.portfolio_analytics import build_portfolio_analytics_report


@dataclass
class KPICatalogProcessor:
    """Compute summary KPIs from core loan, payment, and customer datasets."""

    loans_df: pd.DataFrame
    payments_df: pd.DataFrame
    customers_df: pd.DataFrame
    collateral_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    intermedia_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    schedule_df: Optional[pd.DataFrame] = None

    def __post_init__(self) -> None:
        self.loans_df = self.loans_df if self.loans_df is not None else pd.DataFrame()
        self.payments_df = self.payments_df if self.payments_df is not None else pd.DataFrame()
        self.customers_df = self.customers_df if self.customers_df is not None else pd.DataFrame()
        self.collateral_df = self.collateral_df if self.collateral_df is not None else pd.DataFrame()
        self.intermedia_df = self.intermedia_df if self.intermedia_df is not None else pd.DataFrame()
        self.schedule_df = self.schedule_df if self.schedule_df is not None else pd.DataFrame()

    @staticmethod
    def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
        """Return the first matching column name from candidates."""
        if df.empty:
            return None
        for column in candidates:
            if column in df.columns:
                return column
        return None

    @staticmethod
    def _coerce_datetime(series: pd.Series) -> pd.Series:
        """Convert values to datetime and drop timezone for stable grouping."""
        parsed = pd.to_datetime(series, errors="coerce")
        if getattr(parsed.dtype, "tz", None) is not None:
            parsed = parsed.dt.tz_convert(None)
        return parsed

    def _loan_columns(self) -> dict[str, Optional[str]]:
        """Resolve commonly used loan columns across naming variants."""
        return {
            "loan_id": self._first_existing_column(self.loans_df, ["loan_id", "application_id"]),
            "customer_id": self._first_existing_column(
                self.loans_df,
                ["customer_id", "client_id", "borrower_id", "customer_id_cust"],
            ),
            "segment": self._first_existing_column(
                self.loans_df,
                ["client_segment", "segment", "categoria", "category", "product_type"],
            ),
            "channel": self._first_existing_column(
                self.loans_df,
                ["sales_channel", "channel", "sales_agent"],
            ),
            "date": self._first_existing_column(
                self.loans_df,
                ["origination_date", "disbursement_date", "loan_date", "month"],
            ),
            "outstanding": self._first_existing_column(
                self.loans_df,
                ["outstanding_loan_value", "outstanding_balance", "outstanding"],
            ),
            "principal": self._first_existing_column(
                self.loans_df,
                ["principal_amount", "disbursement_amount", "tpv", "amount"],
            ),
            "apr": self._first_existing_column(
                self.loans_df,
                ["interest_rate_apr", "interest_rate", "apr"],
            ),
            "fee": self._first_existing_column(
                self.loans_df,
                ["origination_fee", "fee_amount", "fee"],
            ),
            "fee_tax": self._first_existing_column(
                self.loans_df,
                ["origination_fee_taxes", "fee_tax", "taxes"],
            ),
            "dpd": self._first_existing_column(
                self.loans_df,
                ["days_past_due", "days_in_default", "dpd", "dpd_days"],
            ),
        }

    def _payment_columns(self) -> dict[str, Optional[str]]:
        """Resolve commonly used payment columns across naming variants."""
        return {
            "date": self._first_existing_column(
                self.payments_df,
                ["payment_date", "month", "date", "paid_at", "posted_at"],
            ),
            "customer_id": self._first_existing_column(
                self.payments_df,
                ["customer_id", "client_id", "borrower_id", "customer_id_cust"],
            ),
            "amount": self._first_existing_column(
                self.payments_df,
                [
                    "recv_revenue_for_month",
                    "payment_amount",
                    "amount",
                    "total_payment",
                    "payment",
                    "amount_paid",
                ],
            ),
            "interest": self._first_existing_column(
                self.payments_df,
                [
                    "recv_interest_for_month",
                    "true_interest_payment",
                    "interest_payment",
                    "interest_paid",
                ],
            ),
            "fee": self._first_existing_column(
                self.payments_df,
                ["recv_fee_for_month", "true_fee_payment", "fee_payment", "fee_paid"],
            ),
            "other": self._first_existing_column(
                self.payments_df,
                ["true_other_payment", "other_payment", "other_income"],
            ),
            "rebates": self._first_existing_column(
                self.payments_df,
                ["true_rebates", "rebates", "rebate_amount"],
            ),
        }

    def _customer_columns(self) -> dict[str, Optional[str]]:
        """Resolve commonly used customer columns across naming variants."""
        return {
            "customer_id": self._first_existing_column(
                self.customers_df,
                ["customer_id", "client_id", "borrower_id"],
            ),
            "created_at": self._first_existing_column(
                self.customers_df,
                ["created_at", "signup_date", "onboarding_date", "first_loan_date"],
            ),
            "marketing_spend": self._first_existing_column(
                self.customers_df,
                ["marketing_spend", "commercial_expense", "acquisition_cost", "cac_spend"],
            ),
        }

    def get_all_kpis(self) -> dict[str, Any]:
        """Return a dictionary of computed KPIs for dashboard consumption."""
        loan_cols = self._loan_columns()
        revenue_df = self.get_monthly_revenue_df()
        segmentation = self.get_segmentation_summary()
        churn_90d = self.get_churn_90d_metrics()
        unit_economics = self.get_unit_economics(revenue_df, churn_90d)
        pricing_analytics = self.get_pricing_analytics()
        revenue_forecast = self.get_revenue_forecast(revenue_df)
        opportunity_prioritization = self.get_opportunity_prioritization()
        governance = self.get_data_governance()

        total_loans = (
            int(self.loans_df[loan_cols["loan_id"]].nunique())
            if loan_cols["loan_id"] is not None
            else 0
        )
        total_customers = (
            int(self.customers_df[self._customer_columns()["customer_id"]].nunique())
            if self._customer_columns()["customer_id"] is not None
            else (
                int(self.loans_df[loan_cols["customer_id"]].nunique())
                if loan_cols["customer_id"] is not None
                else 0
            )
        )

        total_outstanding = (
            float(self.loans_df[loan_cols["outstanding"]].fillna(0).sum())
            if loan_cols["outstanding"] is not None
            else 0.0
        )

        avg_apr = float(pricing_analytics.get("current", {}).get("weighted_apr", 0.0))

        latest_forecast = revenue_forecast[0] if revenue_forecast else {}
        unit_economics_rows = unit_economics if unit_economics else []

        def _latest_non_null_metric(metric_key: str) -> float | None:
            for row in reversed(unit_economics_rows):
                metric_value = row.get(metric_key)
                if metric_value is None:
                    continue
                if isinstance(metric_value, float) and np.isnan(metric_value):
                    continue
                return float(metric_value)
            return None

        latest_cac = _latest_non_null_metric("cac_usd")
        latest_ltv = _latest_non_null_metric("ltv_realized_usd")
        latest_margin = _latest_non_null_metric("gross_margin_pct")

        strategic_confirmations = {
            "cac_confirmed": latest_cac is not None,
            "ltv_confirmed": latest_ltv is not None,
            "margin_confirmed": latest_margin is not None,
            "revenue_forecast_confirmed": bool(revenue_forecast),
            "latest_cac_usd": latest_cac,
            "latest_ltv_usd": latest_ltv,
            "latest_gross_margin_pct": latest_margin,
            "next_month_revenue_forecast_usd": latest_forecast.get("forecast_revenue_usd"),
        }

        executive_strip = {
            "total_loans": total_loans,
            "total_customers": total_customers,
            "total_outstanding_loan_value": total_outstanding,
            "avg_apr": avg_apr,
            "cac_usd": latest_cac,
            "ltv_realized_usd": latest_ltv,
            "gross_margin_pct": latest_margin,
            "revenue_forecast_next_month_usd": latest_forecast.get("forecast_revenue_usd"),
        }

        # NSM + Guardrail KPI groups (wired to business_parameters.yml)
        nsm_customer_types = self.get_customer_types()
        dpd_buckets        = self.get_dpd_buckets()
        concentration      = self.get_concentration()
        rotation           = self.get_portfolio_rotation()
        weighted_apr       = self.get_weighted_apr()
        weighted_fee_rate  = self.get_weighted_fee_rate()
        graph_analytics    = self.get_graph_analytics()
        portfolio_analytics = self.get_portfolio_analytics()
        lending_kpis = self.get_lending_kpis()

        return {
            # Legacy groups (unchanged)
            "executive_strip": executive_strip,
            "segmentation_summary": segmentation,
            "churn_90d_metrics": churn_90d,
            "unit_economics": unit_economics,
            "pricing_analytics": pricing_analytics,
            "revenue_forecast_6m": revenue_forecast,
            "opportunity_prioritization": opportunity_prioritization,
            "data_governance": governance,
            "strategic_confirmations": strategic_confirmations,
            # NSM + Guardrail groups (v3.1)
            "nsm_customer_types": nsm_customer_types,
            "dpd_buckets": dpd_buckets,
            "concentration": concentration,
            "portfolio_rotation": rotation,
            "weighted_apr": weighted_apr,
            "weighted_fee_rate": weighted_fee_rate,
            # Monthly pricing (alias to pricing_analytics for dual-engine parity)
            "monthly_pricing": pricing_analytics,
            # Graph Analytics & Fintech Thesis (2026)
            "graph_analytics": graph_analytics,
            "portfolio_analytics": portfolio_analytics,
            "lending_kpis": lending_kpis,
        }

    def get_monthly_revenue_df(self) -> pd.DataFrame:
        """Build a monthly revenue metrics frame for dashboard charts."""
        payment_cols = self._payment_columns()

        if not self.payments_df.empty and payment_cols["date"] is not None:
            monthly = self.payments_df.copy()
            monthly[payment_cols["date"]] = self._coerce_datetime(monthly[payment_cols["date"]])
            monthly = monthly.dropna(subset=[payment_cols["date"]])

            if monthly.empty:
                return pd.DataFrame()

            monthly["month"] = monthly[payment_cols["date"]].dt.to_period("M").dt.to_timestamp()

            for source_col, target_col in [
                ("interest", "recv_interest_for_month"),
                ("fee", "recv_fee_for_month"),
                ("other", "recv_other_for_month"),
                ("rebates", "recv_rebates_for_month"),
            ]:
                col_name = payment_cols[source_col]
                if col_name is not None:
                    monthly[target_col] = pd.to_numeric(monthly[col_name], errors="coerce").fillna(
                        0
                    )
                else:
                    monthly[target_col] = 0.0

            if payment_cols["amount"] is not None:
                monthly["recv_revenue_for_month"] = pd.to_numeric(
                    monthly[payment_cols["amount"]],
                    errors="coerce",
                ).fillna(0)
            else:
                monthly["recv_revenue_for_month"] = (
                    monthly["recv_interest_for_month"]
                    + monthly["recv_fee_for_month"]
                    + monthly["recv_other_for_month"]
                    - monthly["recv_rebates_for_month"]
                )

            summary = (
                monthly.groupby("month", as_index=False)[
                    [
                        "recv_revenue_for_month",
                        "recv_interest_for_month",
                        "recv_fee_for_month",
                    ]
                ]
                .sum()
                .sort_values("month")
            )
        else:
            summary = self._fallback_revenue_from_loans()

        if summary.empty:
            return pd.DataFrame(
                columns=[
                    "month",
                    "recv_revenue_for_month",
                    "recv_interest_for_month",
                    "recv_fee_for_month",
                    "sched_revenue",
                ]
            )

        if "recv_revenue_for_month" not in summary.columns:
            summary["recv_revenue_for_month"] = (
                pd.to_numeric(summary.get("recv_interest_for_month", 0), errors="coerce").fillna(0)
                + pd.to_numeric(summary.get("recv_fee_for_month", 0), errors="coerce").fillna(0)
            )

        summary["sched_revenue"] = summary["recv_revenue_for_month"]
        return summary

    def _fallback_revenue_from_loans(self) -> pd.DataFrame:
        """Estimate monthly revenue from loan-level data when payment data is missing."""
        loan_cols = self._loan_columns()
        if self.loans_df.empty or loan_cols["date"] is None:
            return pd.DataFrame()

        fallback = self.loans_df.copy()
        fallback[loan_cols["date"]] = self._coerce_datetime(fallback[loan_cols["date"]])
        fallback = fallback.dropna(subset=[loan_cols["date"]])
        if fallback.empty:
            return pd.DataFrame()

        principal_col = loan_cols["principal"]
        apr_col = loan_cols["apr"]
        fee_col = loan_cols["fee"]
        fee_tax_col = loan_cols["fee_tax"]

        principal = (
            pd.to_numeric(fallback[principal_col], errors="coerce").fillna(0)
            if principal_col is not None
            else pd.Series(0.0, index=fallback.index)
        )
        apr = (
            pd.to_numeric(fallback[apr_col], errors="coerce").fillna(0)
            if apr_col is not None
            else pd.Series(0.0, index=fallback.index)
        )
        fees = (
            pd.to_numeric(fallback[fee_col], errors="coerce").fillna(0)
            if fee_col is not None
            else pd.Series(0.0, index=fallback.index)
        )
        if fee_tax_col is not None:
            fees = fees + pd.to_numeric(fallback[fee_tax_col], errors="coerce").fillna(0)

        fallback["month"] = fallback[loan_cols["date"]].dt.to_period("M").dt.to_timestamp()
        fallback["recv_interest_for_month"] = principal * apr / 12
        fallback["recv_fee_for_month"] = fees
        fallback["recv_revenue_for_month"] = (
            fallback["recv_interest_for_month"] + fallback["recv_fee_for_month"]
        )

        return (
            fallback.groupby("month", as_index=False)[
                [
                    "recv_revenue_for_month",
                    "recv_interest_for_month",
                    "recv_fee_for_month",
                ]
            ]
            .sum()
            .sort_values("month")
        )

    def get_segmentation_summary(self) -> list[dict[str, Any]]:
        """Create segment-level volume and risk summary used by dashboards."""
        loan_cols = self._loan_columns()
        if self.loans_df.empty or loan_cols["segment"] is None:
            return []

        segment_df = self.loans_df.copy()
        segment_df[loan_cols["segment"]] = segment_df[loan_cols["segment"]].fillna("Unassigned")

        outstanding = (
            pd.to_numeric(segment_df[loan_cols["outstanding"]], errors="coerce").fillna(0)
            if loan_cols["outstanding"] is not None
            else pd.Series(0.0, index=segment_df.index)
        )
        segment_df["_outstanding"] = outstanding

        if loan_cols["dpd"] is not None:
            dpd = pd.to_numeric(segment_df[loan_cols["dpd"]], errors="coerce").fillna(0)
            segment_df["_delinquent"] = (dpd >= 30).astype(int)
        else:
            segment_df["_delinquent"] = 0

        if loan_cols["customer_id"] is not None:
            customer_counts = (
                segment_df.groupby(loan_cols["segment"])[loan_cols["customer_id"]]
                .nunique()
                .rename("Clients")
            )
        else:
            customer_counts = segment_df.groupby(loan_cols["segment"]).size().rename("Clients")

        grouped = segment_df.groupby(loan_cols["segment"], as_index=False).agg(
            Portfolio_Value=("_outstanding", "sum"),
            Loans=("_outstanding", "size"),
            Delinquency_Rate=("_delinquent", "mean"),
        )

        grouped = grouped.merge(
            customer_counts.reset_index().rename(columns={loan_cols["segment"]: "segment"}),
            left_on=loan_cols["segment"],
            right_on="segment",
            how="left",
        )
        grouped = grouped.drop(columns=["segment"])

        grouped["Avg_Loan"] = grouped["Portfolio_Value"] / grouped["Loans"].replace(0, np.nan)
        grouped["Delinquency_Rate"] = grouped["Delinquency_Rate"].fillna(0)
        grouped["Clients"] = grouped["Clients"].fillna(0).astype(int)
        grouped["client_segment"] = grouped[loan_cols["segment"]].astype(str)

        result = grouped[
            [
                "client_segment",
                "Clients",
                "Portfolio_Value",
                "Avg_Loan",
                "Delinquency_Rate",
            ]
        ].sort_values("Portfolio_Value", ascending=False)

        return result.to_dict("records")

    def _build_activity_frame(self) -> pd.DataFrame:
        """Build a customer activity frame from payments or loan originations."""
        payment_cols = self._payment_columns()
        if (
            not self.payments_df.empty
            and payment_cols["date"] is not None
            and payment_cols["customer_id"] is not None
        ):
            activity = self.payments_df[[payment_cols["date"], payment_cols["customer_id"]]].copy()
            activity.columns = ["event_date", "customer_id"]
            activity["event_date"] = self._coerce_datetime(activity["event_date"])
            return activity.dropna(subset=["event_date", "customer_id"])

        loan_cols = self._loan_columns()
        if (
            not self.loans_df.empty
            and loan_cols["date"] is not None
            and loan_cols["customer_id"] is not None
        ):
            activity = self.loans_df[[loan_cols["date"], loan_cols["customer_id"]]].copy()
            activity.columns = ["event_date", "customer_id"]
            activity["event_date"] = self._coerce_datetime(activity["event_date"])
            return activity.dropna(subset=["event_date", "customer_id"])

        return pd.DataFrame(columns=["event_date", "customer_id"])

    def get_churn_90d_metrics(self) -> list[dict[str, Any]]:
        """Compute monthly 90-day churn using active-vs-known customer windows."""
        activity = self._build_activity_frame()
        if activity.empty:
            return []

        activity = activity.sort_values("event_date")
        first_month = activity["event_date"].min().to_period("M").to_timestamp()
        last_month = activity["event_date"].max().to_period("M").to_timestamp()
        months = pd.date_range(first_month, last_month, freq="MS")

        records: list[dict[str, Any]] = []
        for month_start in months:
            month_end = month_start + pd.offsets.MonthEnd(0)
            known = activity.loc[activity["event_date"] <= month_end, "customer_id"].nunique()
            active_start = month_end - pd.Timedelta(days=89)
            active = activity.loc[
                (activity["event_date"] >= active_start) & (activity["event_date"] <= month_end),
                "customer_id",
            ].nunique()
            inactive = max(known - active, 0)
            churn_pct = (inactive / known) if known else 0.0
            records.append(
                {
                    "month": month_start,
                    "active_90d": int(active),
                    "inactive_90d": int(inactive),
                    "churn90d_pct": float(churn_pct),
                }
            )

        return records

    def get_unit_economics(
        self,
        revenue_df: Optional[pd.DataFrame] = None,
        churn_90d: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """Build monthly CAC/LTV/margin series for strategic unit-economics analysis."""
        revenue_df = revenue_df if revenue_df is not None else self.get_monthly_revenue_df()
        if revenue_df.empty:
            return []

        working = revenue_df.copy()
        working["month"] = pd.to_datetime(working["month"], errors="coerce")
        working = working.dropna(subset=["month"]).sort_values("month")

        activity = self._build_activity_frame()
        if activity.empty:
            working["new_clients"] = 0
            working["known_customers"] = 0
        else:
            first_seen = (
                activity.groupby("customer_id")["event_date"]
                .min()
                .dt.to_period("M")
                .dt.to_timestamp()
            )
            new_clients = first_seen.value_counts().sort_index()
            working["new_clients"] = working["month"].map(new_clients).fillna(0).astype(int)

            known_series = []
            for month in working["month"]:
                known_count = int((first_seen <= month).sum())
                known_series.append(known_count)
            working["known_customers"] = known_series

        customer_cols = self._customer_columns()
        marketing_spend_df = pd.DataFrame(
            {
                "month": pd.Series(dtype="datetime64[ns]"),
                "marketing_spend_usd": pd.Series(dtype="float64"),
            }
        )
        if (
            not self.customers_df.empty
            and customer_cols["created_at"] is not None
            and customer_cols["marketing_spend"] is not None
        ):
            marketing = self.customers_df[
                [customer_cols["created_at"], customer_cols["marketing_spend"]]
            ].copy()
            marketing.columns = ["event_date", "marketing_spend_usd"]
            marketing["event_date"] = self._coerce_datetime(marketing["event_date"])
            marketing["month"] = marketing["event_date"].dt.to_period("M").dt.to_timestamp()
            marketing["marketing_spend_usd"] = pd.to_numeric(
                marketing["marketing_spend_usd"],
                errors="coerce",
            ).fillna(0)
            marketing_spend_df = marketing.groupby("month", as_index=False)[
                "marketing_spend_usd"
            ].sum()

        working = working.merge(marketing_spend_df, on="month", how="left")
        working["marketing_spend_usd"] = pd.to_numeric(
            working["marketing_spend_usd"],
            errors="coerce",
        ).astype("float64")
        working["marketing_spend_usd"] = working["marketing_spend_usd"].fillna(0.0)
        working["cac_is_proxy"] = working["marketing_spend_usd"] <= 0

        proxy_spend = (working["recv_revenue_for_month"] * 0.2).astype("float64").fillna(0.0)
        working.loc[working["cac_is_proxy"], "marketing_spend_usd"] = proxy_spend

        working["cac_usd"] = np.where(
            working["new_clients"] > 0,
            working["marketing_spend_usd"] / working["new_clients"],
            np.nan,
        )

        working["cumulative_revenue_usd"] = working["recv_revenue_for_month"].cumsum()
        customer_base = working["known_customers"].replace(0, np.nan)
        working["ltv_realized_usd"] = working["cumulative_revenue_usd"] / customer_base

        working["ltv_cac_ratio"] = working["ltv_realized_usd"] / working["cac_usd"]

        churn_map = pd.DataFrame(churn_90d or [])
        if not churn_map.empty:
            churn_map["month"] = pd.to_datetime(churn_map["month"], errors="coerce")
            working = working.merge(
                churn_map[["month", "churn90d_pct"]],
                on="month",
                how="left",
            )
        working["churn90d_pct"] = working.get("churn90d_pct", 0).fillna(0)

        risk_cost = working["recv_revenue_for_month"] * working["churn90d_pct"].clip(0, 0.5)
        gross_margin = (
            working["recv_revenue_for_month"] - working["marketing_spend_usd"] - risk_cost
        )
        base_revenue = working["recv_revenue_for_month"].replace(0, np.nan)
        working["gross_margin_pct"] = (gross_margin / base_revenue).fillna(0).clip(-1, 1)

        return (
            working[
                [
                    "month",
                    "new_clients",
                    "known_customers",
                    "marketing_spend_usd",
                    "cac_usd",
                    "ltv_realized_usd",
                    "ltv_cac_ratio",
                    "gross_margin_pct",
                    "churn90d_pct",
                    "cac_is_proxy",
                ]
            ]
            .replace([np.inf, -np.inf], np.nan)
            .to_dict("records")
        )

    def get_pricing_analytics(self) -> dict[str, Any]:
        """Compute pricing stack analytics: APR, fees, and effective rate."""
        loan_cols = self._loan_columns()
        if self.loans_df.empty:
            return {"current": {}, "monthly": []}

        weight_col = loan_cols["outstanding"] or loan_cols["principal"]
        apr_col = loan_cols["apr"]
        principal_col = loan_cols["principal"]
        fee_col = loan_cols["fee"]
        fee_tax_col = loan_cols["fee_tax"]

        if weight_col is None or apr_col is None:
            return {"current": {}, "monthly": []}

        pricing = self.loans_df.copy()
        pricing["_weight"] = pd.to_numeric(pricing[weight_col], errors="coerce").fillna(0)
        pricing["_apr"] = pd.to_numeric(pricing[apr_col], errors="coerce").fillna(0)

        principal = (
            pd.to_numeric(pricing[principal_col], errors="coerce").fillna(0)
            if principal_col is not None
            else pricing["_weight"]
        )

        fee_total = (
            pd.to_numeric(pricing[fee_col], errors="coerce").fillna(0)
            if fee_col is not None
            else pd.Series(0.0, index=pricing.index)
        )
        if fee_tax_col is not None:
            fee_total = fee_total + pd.to_numeric(pricing[fee_tax_col], errors="coerce").fillna(0)

        pricing["_fee_rate"] = np.where(principal > 0, fee_total / principal, 0.0)
        total_weight = float(pricing["_weight"].sum())
        if total_weight <= 0:
            total_weight = 1.0

        weighted_apr = float((pricing["_apr"] * pricing["_weight"]).sum() / total_weight)
        weighted_fee_rate = float((pricing["_fee_rate"] * pricing["_weight"]).sum() / total_weight)
        weighted_effective_rate = float(weighted_apr + weighted_fee_rate)

        monthly_rows: list[dict[str, Any]] = []
        if loan_cols["date"] is not None:
            pricing["_date"] = self._coerce_datetime(pricing[loan_cols["date"]])
            pricing = pricing.dropna(subset=["_date"])
            if not pricing.empty:
                pricing["month"] = pricing["_date"].dt.to_period("M").dt.to_timestamp()

                def _weighted(values: pd.Series, weights: pd.Series) -> float:
                    denom = float(weights.sum())
                    if denom <= 0:
                        return 0.0
                    return float((values * weights).sum() / denom)

                for month, grp in pricing.groupby("month"):
                    monthly_rows.append(
                        {
                            "month": month,
                            "weighted_apr": _weighted(grp["_apr"], grp["_weight"]),
                            "weighted_fee_rate": _weighted(grp["_fee_rate"], grp["_weight"]),
                            "weighted_effective_rate": _weighted(
                                grp["_apr"] + grp["_fee_rate"],
                                grp["_weight"],
                            ),
                        }
                    )

        return {
            "current": {
                "weighted_apr": weighted_apr,
                "weighted_fee_rate": weighted_fee_rate,
                "weighted_effective_rate": weighted_effective_rate,
            },
            "monthly": monthly_rows,
        }

    # ── NSM + GUARDRAIL KPIs ─────────────────────────────────────────────────
    # Added to match kpi_definitions.yaml v3.1 and business_parameters.yml
    # These are the "dual-engine Python" counterparts to the SQL views in
    # db/migrations/20260101_analytics_kpi_views.sql

    def get_monthly_pricing(self) -> dict:
        """Weighted APR, fee rate, other income rate, effective rate by month.
        SQL parity: analytics.kpi_monthly_pricing
        """
        return self.get_pricing_analytics()

    def get_dpd_buckets(self, thresholds: list[int] | None = None) -> dict:
        """DPD bucket breakdown: % saldo at 7/15/30/60/90/180+ DPD.
        SQL parity: analytics.kpi_monthly_risk
        """
        if thresholds is None:
            thresholds = [7, 15, 30, 60, 90, 180]

        loan_cols = self._loan_columns()
        dpd_col = loan_cols.get("dpd")
        bal_col = loan_cols.get("outstanding")

        if dpd_col is None or bal_col is None:
            return {
                "dpd_0_7": 0.0,
                "dpd_8_15": 0.0,
                "dpd_16_30": 0.0,
                "dpd_31_60": 0.0,
                "dpd_61_90": 0.0,
                "dpd_90_plus": 0.0,
                "dpd_7_plus_pct": 0.0,
                "dpd_15_plus_pct": 0.0,
                "dpd_30_plus_pct": 0.0,
                "dpd_60_plus_pct": 0.0,
                "dpd_90_plus_pct": 0.0,
                "dpd_180_plus_pct": 0.0,
                "total_outstanding_usd": 0.0,
            }

        dpd = pd.to_numeric(self.loans_df[dpd_col], errors="coerce").fillna(0)
        bal = pd.to_numeric(self.loans_df[bal_col], errors="coerce").fillna(0)
        total = bal.sum()
        if total == 0:
            return {
                "dpd_0_7": 0.0,
                "dpd_8_15": 0.0,
                "dpd_16_30": 0.0,
                "dpd_31_60": 0.0,
                "dpd_61_90": 0.0,
                "dpd_90_plus": 0.0,
                "dpd_7_plus_pct": 0.0,
                "dpd_15_plus_pct": 0.0,
                "dpd_30_plus_pct": 0.0,
                "dpd_60_plus_pct": 0.0,
                "dpd_90_plus_pct": 0.0,
                "dpd_180_plus_pct": 0.0,
                "total_outstanding_usd": 0.0,
            }

        result = {
            "dpd_0_7": float(bal[(dpd >= 0) & (dpd <= 7)].sum() / total * 100),
            "dpd_8_15": float(bal[(dpd >= 8) & (dpd <= 15)].sum() / total * 100),
            "dpd_16_30": float(bal[(dpd >= 16) & (dpd <= 30)].sum() / total * 100),
            "dpd_31_60": float(bal[(dpd >= 31) & (dpd <= 60)].sum() / total * 100),
            "dpd_61_90": float(bal[(dpd >= 61) & (dpd <= 90)].sum() / total * 100),
            "dpd_90_plus": float(bal[dpd > 90].sum() / total * 100),
        }
        for t in thresholds:
            mask = dpd >= t
            result[f"dpd_{t}_plus_pct"] = float(bal[mask].sum() / total * 100)
            result[f"dpd_{t}_plus_usd"] = float(bal[mask].sum())

        result["total_outstanding_usd"] = float(total)
        return result

    def get_weighted_apr(self) -> float:
        """Portfolio-weighted APR (monthly rate × 12 / disbursement amount weight).
        SQL parity: analytics.kpi_weighted_apr
        """
        loan_cols = self._loan_columns()
        apr_col = loan_cols.get("apr") or self._find_col(
            ["interest_rate_apr", "interest_rate", "tasa_interes", "TasaInteres"]
        )
        disb_col = loan_cols.get("principal") or self._find_col(
            ["disbursement_amount", "loan_amount", "MontoDesembolsado"]
        )
        if apr_col is None or disb_col is None:
            return 0.0

        apr = pd.to_numeric(self.loans_df[apr_col], errors="coerce").fillna(0)
        disb = pd.to_numeric(self.loans_df[disb_col], errors="coerce").fillna(0)
        denom = disb.sum()
        if denom == 0:
            return 0.0
        return float((apr * disb).sum() / denom)

    def get_weighted_fee_rate(self) -> float:
        """Portfolio-weighted origination fee rate.
        SQL parity: analytics.kpi_weighted_fee_rate
        """
        loan_cols = self._loan_columns()
        fee_col = self._find_col(
            ["origination_fee", "fee_amount", "AsesoriaDigital", "asesoria_digital"]
        )
        disb_col = loan_cols.get("principal") or self._find_col(
            ["disbursement_amount", "loan_amount", "MontoDesembolsado"]
        )
        if fee_col is None or disb_col is None:
            return 0.0

        fee = pd.to_numeric(self.loans_df[fee_col], errors="coerce").fillna(0)
        disb = pd.to_numeric(self.loans_df[disb_col], errors="coerce").fillna(0)
        denom = disb.sum()
        if denom == 0:
            return 0.0
        return float(fee.sum() / denom)

    def get_concentration(self, top_n: list[int] | None = None) -> dict:
        """Top-N loan/debtor concentration as % of outstanding balance.
        SQL parity: analytics.kpi_concentration
        Guardrails: top-1 ≤4%, top-10 ≤30% (business_parameters.yml)
        """
        if top_n is None:
            top_n = [1, 3, 5, 10]

        loan_cols = self._loan_columns()
        bal_col = loan_cols.get("outstanding")
        debtor_col = self._find_col(
            ["debtor_id", "Emisor", "emisor", "payer_id", "pagador"]
        ) or self._find_col(["customer_id", "borrower_id", "CodCliente"])

        if bal_col is None:
            return {}

        bal = pd.to_numeric(self.loans_df[bal_col], errors="coerce").fillna(0)
        total = bal.sum()
        if total == 0:
            return {"total_outstanding_usd": 0.0}

        result: dict = {"total_outstanding_usd": float(total)}

        # Loan-level concentration (always available)
        sorted_bal = bal.sort_values(ascending=False)
        for n in top_n:
            pct = float(sorted_bal.head(n).sum() / total * 100)
            result[f"top_{n}_loan_pct"] = round(pct, 2)

        # Debtor-level concentration (when debtor column available)
        if debtor_col is not None:
            debtor_bal = (
                self.loans_df.assign(_bal=bal)
                .groupby(debtor_col)["_bal"]
                .sum()
                .sort_values(ascending=False)
            )
            for n in top_n:
                pct = float(debtor_bal.head(n).sum() / total * 100)
                result[f"top_{n}_debtor_pct"] = round(pct, 2)
            result["top_1_debtor_name"] = str(debtor_bal.index[0]) if len(debtor_bal) > 0 else ""
            result["top_1_debtor_usd"] = float(debtor_bal.iloc[0]) if len(debtor_bal) > 0 else 0.0

        result["top_1_pct"] = result.get("top_1_debtor_pct", result.get("top_1_loan_pct", 0.0))
        result["top_10_pct"] = result.get("top_10_debtor_pct", result.get("top_10_loan_pct", 0.0))
        shares = (self.loans_df.assign(_bal=bal).groupby(debtor_col)["_bal"].sum() / total) if debtor_col is not None else (bal / total)
        result["hhi"] = float((shares.pow(2).sum()) * 10000)

        return result

    def get_portfolio_rotation(self, months: int = 12) -> dict:
        """Cash-weighted portfolio rotation over trailing N months.
        Formula: SUM(disbursements in window) / AVG(outstanding in window)
        Guardrail: ≥4.5x (business_parameters.yml → financial.min_rotation)
        SQL parity: capital_efficiency_kpis in kpi_definitions.yaml
        """
        loan_cols = self._loan_columns()
        disb_col = loan_cols.get("date") or self._find_col(
            ["disbursement_date", "FechaDesembolso", "disburse_date"]
        )
        amount_col = loan_cols.get("principal") or self._find_col(
            ["disbursement_amount", "loan_amount", "MontoDesembolsado"]
        )
        bal_col = loan_cols.get("outstanding")
        term_col = self._find_col(["term", "term_days", "Term", "plazo"])

        if disb_col is None or amount_col is None:
            return {}

        disb_dates = pd.to_datetime(self.loans_df[disb_col], errors="coerce")
        cutoff = disb_dates.max()
        window_start = cutoff - pd.DateOffset(months=months)

        mask = disb_dates >= window_start
        disb_12m = pd.to_numeric(self.loans_df.loc[mask, amount_col], errors="coerce").fillna(0).sum()

        aum = (
            pd.to_numeric(self.loans_df[bal_col], errors="coerce").fillna(0).sum()
            if bal_col else disb_12m / max(months, 1)
        )

        rotation = float(disb_12m / aum) if aum > 0 else 0.0

        result: dict[str, float | int | None] = {
            "rotation_x": round(rotation, 2),
            "disbursements_period_usd": float(disb_12m),
            "aum_usd": float(aum),
            "window_months": months,
        }

        if term_col is not None:
            median_term = pd.to_numeric(self.loans_df[term_col], errors="coerce").median()
            median_term_value = float(median_term) if pd.notna(median_term) else None
            result["avg_term_days"] = median_term_value
            result["theoretical_rotation_x"] = (
                round(365 / median_term_value, 1) if median_term_value and median_term_value > 0 else None
            )

        return result

    def get_customer_types(self, window_months: int = 3, recurrent_periods: int = 2,
                           reactivation_gap_days: int = 90) -> dict:
        """New / Recurrent / Reactivated client segmentation.
        SQL parity: analytics.kpi_customer_types
        NSM supporting indicator.
        """
        loan_cols = self._loan_columns()
        disb_col = loan_cols.get("date") or self._find_col(
            ["disbursement_date", "FechaDesembolso"]
        )
        cust_col = loan_cols.get("customer_id") or self._find_col(
            ["customer_id", "CodCliente", "borrower_id"]
        )
        amount_col = loan_cols.get("principal") or self._find_col(
            ["tpv", "TPV", "disbursement_amount", "MontoDesembolsado"]
        )

        if disb_col is None or cust_col is None:
            return {}

        dates = pd.to_datetime(self.loans_df[disb_col], errors="coerce")
        cutoff = dates.max()
        window_start = cutoff - pd.DateOffset(months=window_months)

        df = self.loans_df.copy()
        df["_date"] = dates
        df["_month"] = dates.dt.to_period("M")

        first_op = df.groupby(cust_col)["_date"].min()
        last_op_before = (
            df[df["_date"] < window_start].groupby(cust_col)["_date"].max()
        )

        recent_clients = set(df[df["_date"] >= window_start][cust_col].dropna().unique())
        new_clients = {c for c in recent_clients if first_op.get(c, cutoff) >= window_start}
        react_clients = {
            c for c in recent_clients - new_clients
            if c in last_op_before.index
            and (window_start - last_op_before[c]).days >= reactivation_gap_days
        }
        recurrent_clients = recent_clients - new_clients - react_clients

        # NSM: recurrent TPV (12m)
        trailing_12m = cutoff - pd.DateOffset(months=12)
        if amount_col:
            tpv_col = amount_col
            df["_tpv"] = pd.to_numeric(df[tpv_col], errors="coerce").fillna(0)
            client_months = (
                df[df["_date"] >= trailing_12m]
                .groupby([cust_col, "_month"])["_tpv"].sum()
                .reset_index()
            )
            active_periods = (
                client_months[client_months["_tpv"] > 0]
                .groupby(cust_col)["_month"].nunique()
            )
            recurrent_12m = set(active_periods[active_periods >= recurrent_periods].index)
            nsm_tpv = float(df[
                (df["_date"] >= trailing_12m) & (df[cust_col].isin(recurrent_12m))
            ]["_tpv"].sum())
            total_tpv = float(df[df["_date"] >= trailing_12m]["_tpv"].sum())
        else:
            nsm_tpv = total_tpv = 0.0
            recurrent_12m = set()

        return {
            "window_months": window_months,
            "new_count": len(new_clients),
            "recurrent_count": len(recurrent_clients),
            "reactivated_count": len(react_clients),
            "total_active_period": len(recent_clients),
            # NSM
            "recurrent_tpv_12m_usd": round(nsm_tpv, 2),
            "total_tpv_12m_usd": round(total_tpv, 2),
            "recurrent_tpv_12m_pct": round(nsm_tpv / total_tpv * 100, 1) if total_tpv > 0 else 0.0,
            "recurrent_clients_12m": len(recurrent_12m),
            "recurrent_rate_12m_pct": round(
                len(recurrent_12m) / max(len(first_op), 1) * 100, 1
            ),
        }

    def _find_col(self, candidates: list[str]) -> str | None:
        """Find first matching column name in loans_df."""
        for c in candidates:
            if c in self.loans_df.columns:
                return c
        return None


    def get_revenue_forecast(
        self,
        revenue_df: Optional[pd.DataFrame] = None,
        horizon_months: int = 6,
    ) -> list[dict[str, Any]]:
        """Generate a simple linear revenue forecast with residual-based bounds."""
        revenue_df = revenue_df if revenue_df is not None else self.get_monthly_revenue_df()
        if revenue_df.empty or len(revenue_df) < 2:
            return []

        model_df = revenue_df.copy().sort_values("month")
        model_df["month"] = pd.to_datetime(model_df["month"], errors="coerce")
        model_df = model_df.dropna(subset=["month", "recv_revenue_for_month"])
        if len(model_df) < 2:
            return []

        y_values = (
            pd.to_numeric(model_df["recv_revenue_for_month"], errors="coerce").fillna(0).values
        )
        x_values = np.arange(len(y_values), dtype=float)

        x_mean = float(x_values.mean())
        y_mean = float(y_values.mean())
        denom = float(((x_values - x_mean) ** 2).sum())
        slope = float((((x_values - x_mean) * (y_values - y_mean)).sum() / denom) if denom else 0.0)
        intercept = y_mean - slope * x_mean

        fitted = intercept + slope * x_values
        residual_std = float(np.std(y_values - fitted))
        margin = 1.96 * residual_std

        last_month = model_df["month"].max()
        forecast_rows: list[dict[str, Any]] = []
        for step in range(1, horizon_months + 1):
            x_future = len(y_values) + step - 1
            prediction = max(0.0, intercept + slope * x_future)
            forecast_rows.append(
                {
                    "month": last_month + pd.DateOffset(months=step),
                    "forecast_revenue_usd": float(prediction),
                    "lower_bound_usd": float(max(0.0, prediction - margin)),
                    "upper_bound_usd": float(prediction + margin),
                    "model": "linear_trend",
                }
            )

        return forecast_rows

    def get_opportunity_prioritization(self) -> list[dict[str, Any]]:
        """Prioritize growth opportunities by balancing revenue and risk at segment level."""
        segmentation = self.get_segmentation_summary()
        if not segmentation:
            return []

        scored = pd.DataFrame(segmentation)
        scored["Portfolio_Value"] = pd.to_numeric(
            scored["Portfolio_Value"], errors="coerce"
        ).fillna(0)
        scored["Delinquency_Rate"] = pd.to_numeric(
            scored["Delinquency_Rate"],
            errors="coerce",
        ).fillna(0)

        portfolio_max = float(scored["Portfolio_Value"].max()) if not scored.empty else 1.0
        if portfolio_max <= 0:
            portfolio_max = 1.0

        scored["revenue_potential_score"] = scored["Portfolio_Value"] / portfolio_max
        scored["risk_score"] = scored["Delinquency_Rate"].clip(0, 1)
        scored["priority_score"] = (
            scored["revenue_potential_score"] * 0.7 + (1 - scored["risk_score"]) * 0.3
        ) * 100

        prioritized = scored.sort_values("priority_score", ascending=False)
        return prioritized[
            [
                "client_segment",
                "Portfolio_Value",
                "Delinquency_Rate",
                "priority_score",
            ]
        ].to_dict("records")

    def get_data_governance(self) -> dict[str, Any]:
        """Compute data quality and governance summary for executive reporting."""
        loan_cols = self._loan_columns()
        payment_cols = self._payment_columns()

        completeness_checks = {}
        required_fields = {
            "loan_id": loan_cols["loan_id"],
            "customer_id": loan_cols["customer_id"],
            "outstanding": loan_cols["outstanding"],
            "apr": loan_cols["apr"],
            "origination_date": loan_cols["date"],
            "payment_date": payment_cols["date"],
        }
        for key, col_name in required_fields.items():
            if col_name is None:
                completeness_checks[key] = 0.0
                continue
            source_df = self.payments_df if key == "payment_date" else self.loans_df
            ratio = float(source_df[col_name].notna().mean()) if not source_df.empty else 0.0
            completeness_checks[key] = ratio

        duplicate_rate = 0.0
        if loan_cols["loan_id"] is not None and not self.loans_df.empty:
            duplicate_rate = float(self.loans_df[loan_cols["loan_id"]].duplicated().mean())

        freshness_days = None
        date_candidates: list[pd.Series] = []
        if loan_cols["date"] is not None and not self.loans_df.empty:
            date_candidates.append(self._coerce_datetime(self.loans_df[loan_cols["date"]]))
        if payment_cols["date"] is not None and not self.payments_df.empty:
            date_candidates.append(self._coerce_datetime(self.payments_df[payment_cols["date"]]))

        if date_candidates:
            merged_dates = pd.concat(date_candidates).dropna()
            if not merged_dates.empty:
                freshness_days = int(
                    (pd.Timestamp.utcnow().tz_localize(None) - merged_dates.max()).days
                )

        completeness_mean = float(np.mean(list(completeness_checks.values())))
        freshness_penalty = 0.0 if freshness_days is None else min(max(freshness_days, 0) / 180, 1)
        quality_score = max(
            0.0,
            1 - (0.5 * (1 - completeness_mean) + 0.3 * duplicate_rate + 0.2 * freshness_penalty),
        )

        return {
            "quality_score": quality_score,
            "completeness": completeness_checks,
            "duplicate_rate": duplicate_rate,
            "freshness_days": freshness_days,
            "governance_status": (
                "green" if quality_score >= 0.8 else "amber" if quality_score >= 0.6 else "red"
            ),
        }

    def get_graph_analytics(self) -> dict[str, Any]:
        """Compute graph-based analytics and advanced fintech KPIs."""
        if self.intermedia_df.empty:
            # Fallback to a minimal intermedia if not provided,
            # or return empty if essential columns are missing
            return {"status": "unavailable", "reason": "intermedia_df is empty"}

        return build_graph_kpi_report(
            intermedia_df=self.intermedia_df,
            loans_df=self.loans_df,
            payments_df=self.payments_df
        )

    def get_portfolio_analytics(self) -> dict[str, Any]:
        """Run all 6 portfolio analytics modules (cohort, behavior, CE, etc.)"""
        return build_portfolio_analytics_report(
            loans_df=self.loans_df,
            payments_df=self.payments_df,
            schedule_df=self.schedule_df,
            customer_df=self.customers_df,
            collateral_df=self.collateral_df,
        )

    def get_lending_kpis(self) -> dict[str, Any]:
        """Compute lending KPI modules that are not covered by core strategic outputs."""
        return build_lending_kpi_report(
            loans_df=self.loans_df,
            payments_df=self.payments_df,
            schedule_df=self.schedule_df,
            customer_df=self.customers_df,
        )

    def get_quarterly_scorecard(self) -> pd.DataFrame:
        """Create a quarterly scorecard from available payment data."""
        if self.payments_df.empty:
            return pd.DataFrame()

        payment_cols = self._payment_columns()
        if payment_cols["date"] is None:
            return pd.DataFrame()

        date_col = payment_cols["date"]
        amount_col = payment_cols["amount"]
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
