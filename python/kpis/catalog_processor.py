"""KPI catalog processor for Streamlit dashboards and strategic reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
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

        latest_unit = unit_economics[-1] if unit_economics else {}
        latest_forecast = revenue_forecast[0] if revenue_forecast else {}

        strategic_confirmations = {
            "cac_confirmed": latest_unit.get("cac_usd") is not None,
            "ltv_confirmed": latest_unit.get("ltv_realized_usd") is not None,
            "margin_confirmed": latest_unit.get("gross_margin_pct") is not None,
            "revenue_forecast_confirmed": bool(revenue_forecast),
            "latest_cac_usd": latest_unit.get("cac_usd"),
            "latest_ltv_usd": latest_unit.get("ltv_realized_usd"),
            "latest_gross_margin_pct": latest_unit.get("gross_margin_pct"),
            "next_month_revenue_forecast_usd": latest_forecast.get("forecast_revenue_usd"),
        }

        executive_strip = {
            "total_loans": total_loans,
            "total_customers": total_customers,
            "total_outstanding_loan_value": total_outstanding,
            "avg_apr": avg_apr,
            "cac_usd": latest_unit.get("cac_usd"),
            "ltv_realized_usd": latest_unit.get("ltv_realized_usd"),
            "gross_margin_pct": latest_unit.get("gross_margin_pct"),
            "revenue_forecast_next_month_usd": latest_forecast.get("forecast_revenue_usd"),
        }

        return {
            "executive_strip": executive_strip,
            "segmentation_summary": segmentation,
            "churn_90d_metrics": churn_90d,
            "unit_economics": unit_economics,
            "pricing_analytics": pricing_analytics,
            "revenue_forecast_6m": revenue_forecast,
            "opportunity_prioritization": opportunity_prioritization,
            "data_governance": governance,
            "strategic_confirmations": strategic_confirmations,
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
                    monthly[target_col] = pd.to_numeric(monthly[col_name], errors="coerce").fillna(0)
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
                segment_df.groupby(loan_cols["segment"])[loan_cols["customer_id"]].nunique().rename("Clients")
            )
        else:
            customer_counts = (
                segment_df.groupby(loan_cols["segment"]).size().rename("Clients")
            )

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
                (activity["event_date"] >= active_start)
                & (activity["event_date"] <= month_end),
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
                activity.groupby("customer_id")["event_date"].min().dt.to_period("M").dt.to_timestamp()
            )
            new_clients = first_seen.value_counts().sort_index()
            working["new_clients"] = working["month"].map(new_clients).fillna(0).astype(int)

            known_series = []
            for month in working["month"]:
                known_count = int((first_seen <= month).sum())
                known_series.append(known_count)
            working["known_customers"] = known_series

        customer_cols = self._customer_columns()
        marketing_spend_df = pd.DataFrame(columns=["month", "marketing_spend_usd"])
        if (
            not self.customers_df.empty
            and customer_cols["created_at"] is not None
            and customer_cols["marketing_spend"] is not None
        ):
            marketing = self.customers_df[[customer_cols["created_at"], customer_cols["marketing_spend"]]].copy()
            marketing.columns = ["event_date", "marketing_spend_usd"]
            marketing["event_date"] = self._coerce_datetime(marketing["event_date"])
            marketing["month"] = marketing["event_date"].dt.to_period("M").dt.to_timestamp()
            marketing["marketing_spend_usd"] = pd.to_numeric(
                marketing["marketing_spend_usd"],
                errors="coerce",
            ).fillna(0)
            marketing_spend_df = (
                marketing.groupby("month", as_index=False)["marketing_spend_usd"].sum()
            )

        working = working.merge(marketing_spend_df, on="month", how="left")
        working["marketing_spend_usd"] = working["marketing_spend_usd"].fillna(0)
        working["cac_is_proxy"] = working["marketing_spend_usd"] <= 0

        proxy_spend = (working["recv_revenue_for_month"] * 0.2).fillna(0)
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

        y_values = pd.to_numeric(model_df["recv_revenue_for_month"], errors="coerce").fillna(0).values
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
        scored["Portfolio_Value"] = pd.to_numeric(scored["Portfolio_Value"], errors="coerce").fillna(0)
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
            scored["revenue_potential_score"] * 0.7
            + (1 - scored["risk_score"]) * 0.3
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
                freshness_days = int((pd.Timestamp.utcnow().tz_localize(None) - merged_dates.max()).days)

        completeness_mean = float(np.mean(list(completeness_checks.values())))
        freshness_penalty = 0.0 if freshness_days is None else min(max(freshness_days, 0) / 180, 1)
        quality_score = max(0.0, 1 - (0.5 * (1 - completeness_mean) + 0.3 * duplicate_rate + 0.2 * freshness_penalty))

        return {
            "quality_score": quality_score,
            "completeness": completeness_checks,
            "duplicate_rate": duplicate_rate,
            "freshness_days": freshness_days,
            "governance_status": "green" if quality_score >= 0.8 else "amber" if quality_score >= 0.6 else "red",
        }

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
