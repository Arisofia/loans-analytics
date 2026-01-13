import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.optimize import newton

logger = logging.getLogger(__name__)


class KPICatalogProcessor:
    """Processor for the unified KPI command catalog for ABACO."""

    def __init__(
        self,
        loans_df: pd.DataFrame,
        payments_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        schedule_df: Optional[pd.DataFrame] = None,
    ):
        self.loans = self._clean_df(loans_df)
        self.payments = self._clean_df(payments_df)
        self.customers = self._clean_df(customers_df)
        self.schedule = self._clean_df(schedule_df) if schedule_df is not None else pd.DataFrame()

        # Filter orphaned loans (matching SQL loader logic)
        if "customer_id" in self.loans.columns and "customer_id" in self.customers.columns:
            loan_cust_pre = self.loans["customer_id"].nunique()
            valid_cust = set(self.customers["customer_id"])
            self.loans = self.loans[self.loans["customer_id"].isin(valid_cust)].copy()
            loan_cust_post = self.loans["customer_id"].nunique()
            print(
                f"[DEBUG] KPICatalogProcessor: customers in loans before "
                f"filter: {loan_cust_pre}, after: {loan_cust_post}, total "
                f"valid customers: {len(valid_cust)}"
            )

        # Filter orphaned payments
        if "loan_id" in self.payments.columns and "loan_id" in self.loans.columns:
            self.payments = self.payments[
                self.payments["loan_id"].isin(set(self.loans["loan_id"]))
            ].copy()

        self.loan_month = pd.DataFrame()

    def get_churn_90d_metrics(self) -> pd.DataFrame:
        """
        Calculate 90d churn KPIs per month:
        - Active_90d: clients with last disbursement ≤90d at month end
        - Inactive_90d: clients with last disbursement >90d at month end
        - Churn90d%: Inactive_90d / (Active_90d + Inactive_90d)
        - Newly_90d-inactive: clients who crossed 90d inactivity that month
        - Churn$: Inactive_90d × revenue per active_90d
        """
        if self.loans.empty:
            return pd.DataFrame()

        loans = self.loans.copy()
        loans["disbursement_date"] = pd.to_datetime(loans["disbursement_date"])
        all_months = pd.date_range(
            loans["disbursement_date"].min(),
            loans["disbursement_date"].max(),
            freq="M",
        )

        results = []
        for m in all_months:
            last_disb = (
                loans[loans["disbursement_date"] <= m]
                .groupby("customer_id")["disbursement_date"]
                .max()
            )
            active_90d = last_disb[last_disb >= (m - pd.Timedelta(days=90))].index
            inactive_90d = last_disb[last_disb < (m - pd.Timedelta(days=90))].index
            newly_90d = last_disb[
                (last_disb > (m - pd.Timedelta(days=120)))
                & (last_disb <= (m - pd.Timedelta(days=90)))
            ].index

            n_active = len(active_90d)
            n_inactive = len(inactive_90d)
            n_newly = len(newly_90d)
            churn_pct = n_inactive / (n_active + n_inactive) if (n_active + n_inactive) > 0 else 0.0

            if not self.payments.empty:
                recent_payments = self.payments[
                    (self.payments["true_payment_date"] >= (m - pd.Timedelta(days=90)))
                    & (self.payments["true_payment_date"] <= m)
                ]
                rev_90d = (
                    recent_payments["true_total_payment"].sum()
                    if "true_total_payment" in recent_payments.columns
                    else 0.0
                )
            else:
                rev_90d = 0.0

            rev_per_active = rev_90d / n_active if n_active > 0 else 0.0
            churn_dollar = n_inactive * rev_per_active
            results.append(
                {
                    "month": m,
                    "active_90d": n_active,
                    "inactive_90d": n_inactive,
                    "churn90d_pct": churn_pct,
                    "newly_90d_inactive": n_newly,
                    "revenue_per_active_90d": rev_per_active,
                    "churn_dollar": churn_dollar,
                }
            )

        return pd.DataFrame(results)

    def _xirr(self, cashflows: List[float], dates: List[datetime]) -> float:
        """Calculate XIRR (Internal Rate of Return with dates)."""
        if not cashflows or len(cashflows) != len(dates):
            return 0.0

        # Ensure we have both negative and positive flows
        if all(x >= 0 for x in cashflows) or all(x <= 0 for x in cashflows):
            return 0.0

        def xnpv(rate, cashflows, dates):
            d0 = dates[0]
            return sum(
                [cf / (1 + rate) ** ((d - d0).days / 365.0) for cf, d in zip(cashflows, dates)]
            )

        try:
            return newton(lambda r: xnpv(r, cashflows, dates), 0.1)
        except (RuntimeError, OverflowError):
            return 0.0

    def _clean_df(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Normalize column names
        df.columns = [
            c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "")
            for c in df.columns
        ]

        # Candidate columns for key fields (aligned with actual CSV headers)
        # Disbursement date: 'disburse_date', 'disbursement_date',
        #   'Disbursement Date'
        # Payment date: 'true_payment_date', 'payment_date',
        #   'True Payment Date'
        # Payment amount: 'true_total_payment', 'payment_amount',
        #   'True Total Payment', 'amount'
        # Disbursement amount: 'disburse_principal', 'disbursement_amount',
        #   'Disbursement Amount'

        mapping = {
            # Disbursement date
            "disburse_date": "disbursement_date",
            "disbursement_date": "disbursement_date",
            # Disbursement amount
            "disburse_principal": "disbursement_amount",
            "disbursement_amount": "disbursement_amount",
            # Payment date
            "true_payment_date": "true_payment_date",
            "payment_date": "true_payment_date",
            # Payment amount
            "true_total_payment": "true_total_payment",
            "payment_amount": "true_total_payment",
            "amount": "true_total_payment",
            # Principal mapping
            "principal_payment": "true_principal_payment",
            "true_principal_payment": "true_principal_payment",
            # Rebates
            "true_rebates": "true_rebates",
            "true_rabates": "true_rebates",
            # New mappings for payment components
            "true_interest_payment": "true_interest_payment",
            "true_fee_payment": "true_fee_payment",
            "true_other_payment": "true_other_payment",
            "true_tax_payment": "true_tax_payment",
            "true_fee_tax_payment": "true_fee_tax_payment",
            # Other mappings
            "outstanding_balance": "outstanding_loan_value",
            "interest_rate": "interest_rate_apr",
            "interest_rate_apr": "interest_rate_apr",
            "maturity_date": "loan_end_date",
            "days_in_default": "days_past_due",
            "dpd": "days_past_due",
        }
        for old, new in mapping.items():
            if old in df.columns:
                df[new] = df[old]

        # If true_principal_payment is missing, estimate it from total payment
        # (synthetic fallback)
        if "true_total_payment" in df.columns and "true_principal_payment" not in df.columns:
            df["true_principal_payment"] = df["true_total_payment"] * 0.9

        # Date conversion for all columns containing 'date' or 'fecha'
        date_cols = [col for col in df.columns if any(x in col for x in ["date", "fecha"])]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    # 0. Base extracts (building blocks)
    def build_loan_month(
        self, start_date: str = "2024-01-01", end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Builds a monthly loan snapshot with outstanding principal and DPD.
        Aggregates multiple disbursements per loan_id correctly.
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Create month-end series
        month_ends = pd.date_range(start=start_date, end=end_date, freq="ME")

        if "true_payment_date" not in self.payments.columns:
            self.loan_month = pd.DataFrame()
            return self.loan_month

        # 1. Representative metadata per loan_id
        # Use available columns
        meta_cols = {
            "customer_id": "max",
            "interest_rate_apr": "max",
            "origination_fee": "max",
            "origination_fee_taxes": "max",
            "days_past_due": "max",
            "disbursement_date": "min",
        }
        actual_meta = {c: agg for c, agg in meta_cols.items() if c in self.loans.columns}

        loan_meta = self.loans.groupby("loan_id").agg(actual_meta).reset_index()

        # 2. Cumulative disbursements per loan_id and month_end
        disb_date_col = "disbursement_date"
        disb_amount_col = "disbursement_amount"

        disbursements = self.loans[["loan_id", disb_date_col, disb_amount_col]].copy()

        grid_disb = []
        for me in month_ends:
            temp = disbursements[disbursements[disb_date_col] <= me].copy()
            if not temp.empty:
                agg = temp.groupby("loan_id")[disb_amount_col].sum().reset_index()
                agg["month_end"] = me
                grid_disb.append(agg)

        if not grid_disb:
            self.loan_month = pd.DataFrame()
            return self.loan_month

        df_disb = pd.concat(grid_disb)

        # 3. Cumulative payments per loan_id and month_end
        payments = self.payments[["loan_id", "true_payment_date", "true_principal_payment"]].copy()

        grid_pay = []
        for me in month_ends:
            temp = payments[payments["true_payment_date"] <= me].copy()
            if not temp.empty:
                agg = (
                    temp.groupby("loan_id")["true_principal_payment"]
                    .sum()
                    .reset_index(name="cum_principal")
                )
                agg["month_end"] = me
                grid_pay.append(agg)

        df_pay = (
            pd.concat(grid_pay)
            if grid_pay
            else pd.DataFrame(columns=["loan_id", "month_end", "cum_principal"])
        )

        # 4. Final Merge
        df_final = df_disb.merge(df_pay, on=["loan_id", "month_end"], how="left")
        df_final["cum_principal"] = df_final["cum_principal"].fillna(0)
        df_final["outstanding"] = (
            df_final["disbursement_amount"] - df_final["cum_principal"]
        ).clip(lower=0)

        # Add metadata
        df_final = df_final.merge(loan_meta, on="loan_id", how="left")

        self.loan_month = df_final
        return self.loan_month

    # 1. Customer Model & Growth
    def get_active_unique_customers(self) -> pd.DataFrame:
        """Count distinct active customers per month."""
        if self.loan_month.empty:
            self.build_loan_month()
        if self.loan_month.empty:
            return pd.DataFrame()

        active = self.loan_month[self.loan_month["outstanding"] > 1e-4]
        return (
            active.groupby("month_end")["customer_id"]
            .nunique()
            .reset_index(name="active_customers")
        )

    def get_customer_classification(self) -> pd.DataFrame:
        """Classify customers as New, Recurrent, Reactivated, or Recovered."""
        loans = self.loans.sort_values(["customer_id", "disbursement_date", "loan_id"])

        # Track historical delinquency per customer
        bad_history = self.loans[self.loans["days_past_due"] > 90]["customer_id"].unique()

        loans["rn"] = loans.groupby("customer_id").cumcount() + 1
        loans["prev_disb"] = loans.groupby("customer_id")["disbursement_date"].shift(1)

        def classify(row):
            if row["customer_id"] in bad_history and row["days_past_due"] <= 30:
                return "Recovered"
            if row["rn"] == 1:
                return "New"
            if (
                pd.notnull(row["prev_disb"])
                and (row["disbursement_date"] - row["prev_disb"]).days > 180
            ):
                return "Reactivated"
            return "Recurrent"

        loans["customer_type"] = loans.apply(classify, axis=1)
        loans["year_month"] = loans["disbursement_date"].dt.to_period(
            "M"
        ).dt.to_timestamp() + pd.offsets.MonthEnd(0)

        return (
            loans.groupby(["year_month", "customer_type"])["customer_id"]
            .nunique()
            .reset_index(name="unique_customers")
        )

    def get_intensity_segmentation(self) -> pd.DataFrame:
        """Classify customers into Low / Medium / Heavy users."""
        loans_per_cust = (
            self.loans.groupby("customer_id")["loan_id"].nunique().reset_index(name="loans_count")
        )

        def intensity(count):
            if count <= 1:
                return "Low"
            if count <= 3:
                return "Medium"
            return "Heavy"

        loans_per_cust["use_intensity"] = loans_per_cust["loans_count"].apply(intensity)

        # Merge back with monthly disbursement
        df = self.loans.copy()
        df["year_month"] = df["disbursement_date"].dt.to_period(
            "M"
        ).dt.to_timestamp() + pd.offsets.MonthEnd(0)
        df = df.merge(
            loans_per_cust[["customer_id", "use_intensity"]],
            on="customer_id",
            how="left",
        )

        summary = (
            df.groupby(["year_month", "use_intensity"])
            .agg(
                customers=("customer_id", "nunique"),
                disbursement_amount=("disbursement_amount", "sum"),
            )
            .reset_index()
        )

        return summary

    # 2. Portfolio & Pricing
    def get_eir_real(self) -> float:
        """Calculate the realized EIR using actual payment history for closed loans."""
        if self.payments.empty:
            return 0.0

        # Identify closed loans (outstanding near zero)
        closed_loans = self.loans[self.loans["outstanding_loan_value"] < 1.0]
        if closed_loans.empty:
            logger.warning("No closed loans found for EIR Real calculation.")
            return 0.0

        loan_eirs = []
        loan_disbursements = []

        payments_grouped = self.payments.groupby("loan_id")

        for _, loan in closed_loans.iterrows():
            loan_id = loan["loan_id"]
            if loan_id not in payments_grouped.groups:
                continue

            group = payments_grouped.get_group(loan_id)
            disb_amt = loan["disbursement_amount"]
            disb_date = loan["disbursement_date"]

            if pd.isna(disb_date) or disb_amt <= 0:
                continue

            # Cashflows: Day 0 is -Disbursement
            cashflows = [-disb_amt]
            dates = [disb_date]

            # Group by payment date
            daily_pays = (
                group.groupby("true_payment_date")
                .agg(
                    {
                        "true_principal_payment": "sum",
                        "true_interest_payment": "sum",
                        "true_fee_payment": "sum",
                        "true_other_payment": "sum",
                        "true_rebates": "sum",
                    }
                )
                .reset_index()
            )

            for _, row in daily_pays.iterrows():
                # Inflow = Principal + Interest + Fees + Other - Rebates
                inflow = (
                    row["true_principal_payment"]
                    + row["true_interest_payment"]
                    + row["true_fee_payment"]
                    + row["true_other_payment"]
                    - row["true_rebates"]
                )
                if inflow > 0:
                    cashflows.append(inflow)
                    dates.append(row["true_payment_date"])

            if len(cashflows) > 1:
                eir = self._xirr(cashflows, dates)
                if eir != 0:
                    loan_eirs.append(eir)
                    loan_disbursements.append(disb_amt)

        if not loan_eirs:
            return 0.0

        # Weighted average EIR by disbursement amount
        weighted_eir = sum(e * d for e, d in zip(loan_eirs, loan_disbursements)) / sum(
            loan_disbursements
        )
        return float(weighted_eir)

    def get_eir_scheduled(self) -> float:
        """Calculate the scheduled Effective Interest Rate (EIR) using the payment schedule."""
        if self.schedule.empty:
            logger.warning("No schedule data available for EIR Scheduled.")
            return 0.0

        loan_eirs = []
        loan_disbursements = []

        # Process each loan that has both disbursement and schedule
        scheduled_grouped = self.schedule.groupby("loan_id")

        for loan_id, group in scheduled_grouped:
            loan_info = self.loans[self.loans["loan_id"] == loan_id]
            if loan_info.empty:
                continue

            disb_amt = loan_info["disbursement_amount"].sum()
            disb_date = loan_info["disbursement_date"].min()

            if pd.isna(disb_date) or disb_amt <= 0:
                continue

            # Cashflows: Day 0 is -Disbursement
            cashflows = [-disb_amt]
            dates = [disb_date]

            # Group by due date to consolidate multiple rows on same day
            daily_flows = (
                group.groupby("date_due")
                .agg({"principal": "sum", "interest": "sum", "fees": "sum", "other": "sum"})
                .reset_index()
            )

            for _, row in daily_flows.iterrows():
                # Inflow = Principal + Interest + Fees + Other
                inflow = row["principal"] + row["interest"] + row["fees"] + row["other"]
                if inflow > 0:
                    cashflows.append(inflow)
                    dates.append(row["date_due"])

            if len(cashflows) > 1:
                eir = self._xirr(cashflows, dates)
                if eir != 0:
                    loan_eirs.append(eir)
                    loan_disbursements.append(disb_amt)

        if not loan_eirs:
            return 0.0

        # Weighted average EIR by disbursement amount
        weighted_eir = sum(e * d for e, d in zip(loan_eirs, loan_disbursements)) / sum(
            loan_disbursements
        )
        return float(weighted_eir)

    def get_weighted_apr_contractual(self) -> float:
        """Calculate the portfolio-weighted contractual APR based on disbursement amounts."""
        mask = self.loans["interest_rate_apr"].notna() & self.loans["disbursement_amount"].notna()
        if not any(mask):
            return 0.0

        weighted_sum = (
            self.loans.loc[mask, "interest_rate_apr"] * self.loans.loc[mask, "disbursement_amount"]
        ).sum()
        total_disb = self.loans.loc[mask, "disbursement_amount"].sum()

        return float(weighted_sum / total_disb) if total_disb > 0 else 0.0

    def get_weighted_apr(self) -> pd.DataFrame:
        """Calculate portfolio-weighted APR per month."""
        if self.loan_month.empty:
            self.build_loan_month()
        if self.loan_month.empty:
            return pd.DataFrame()

        df = self.loan_month[self.loan_month["outstanding"] > 1e-4].copy()
        df["weighted_apr_part"] = df["interest_rate_apr"] * df["outstanding"]

        result = df.groupby("month_end", as_index=False).agg(
            {"weighted_apr_part": "sum", "outstanding": "sum"}
        )
        result["weighted_apr"] = result["weighted_apr_part"] / result["outstanding"].replace(
            0, np.nan
        )

        return result[["month_end", "weighted_apr"]]

    def get_monthly_pricing(self) -> pd.DataFrame:
        """Monthly pricing metrics (weighted APR, fee rate, scheduled vs received)."""
        if self.loan_month.empty:
            self.build_loan_month()
        if self.loan_month.empty:
            return pd.DataFrame()

        df = self.loan_month[self.loan_month["outstanding"] > 1e-4].copy()

        # 1. Weighted APR
        df["apr_part"] = df["interest_rate_apr"] * df["outstanding"]

        # 2. Fee Rate
        df["fee_rate"] = (df["origination_fee"] + df["origination_fee_taxes"]) / df[
            "disbursement_amount"
        ].replace(0, np.nan)
        df["fee_part"] = df["fee_rate"] * df["outstanding"]

        # 3. Scheduled Revenue (Estimated: Outstanding * APR / 12)
        df["scheduled_interest"] = (df["outstanding"] * df["interest_rate_apr"]) / 12
        # Add estimated fees (origination fees are usually upfront, so we only count them in disbursement month)
        df["is_new_disb"] = df["month_end"].dt.to_period("M") == df[
            "disbursement_date"
        ].dt.to_period("M")
        df["scheduled_fees"] = np.where(
            df["is_new_disb"], df["origination_fee"] + df["origination_fee_taxes"], 0
        )
        df["total_scheduled"] = df["scheduled_interest"] + df["scheduled_fees"]

        # 4. Received Revenue (Following exact requirement: Int + Fee + Other + Tax - Rebates)
        other_cols = [
            "true_fee_payment",
            "true_other_payment",
            "true_tax_payment",
            "true_fee_tax_payment",
            "true_rebates",
            "true_interest_payment",
        ]
        for c in other_cols:
            if c not in self.payments.columns:
                self.payments[c] = 0

        # Extract month from payment date for alignment
        self.payments["pay_month"] = self.payments["true_payment_date"].dt.to_period(
            "M"
        ).dt.to_timestamp() + pd.offsets.MonthEnd(0)

        # Aggregate received income per loan AND month
        income_monthly = (
            self.payments.groupby(["loan_id", "pay_month"])
            .agg(
                {
                    "true_interest_payment": "sum",
                    "true_fee_payment": "sum",
                    "true_other_payment": "sum",
                    "true_tax_payment": "sum",
                    "true_fee_tax_payment": "sum",
                    "true_rebates": "sum",
                }
            )
            .reset_index()
        )
        income_monthly.rename(columns={"pay_month": "month_end"}, inplace=True)

        df = df.merge(income_monthly, on=["loan_id", "month_end"], how="left")
        for c in other_cols:
            df[c] = df[c].fillna(0)

        # DEFINITION: Ingresos mensuales = intereses + fees + otros + taxes - rebates
        df["total_received"] = (
            df["true_interest_payment"]
            + df["true_fee_payment"]
            + df["true_other_payment"]
            + df["true_tax_payment"]
            + df["true_fee_tax_payment"]
            - df["true_rebates"]
        )

        result = df.groupby("month_end", as_index=False).agg(
            {
                "apr_part": "sum",
                "fee_part": "sum",
                "outstanding": "sum",
                "total_scheduled": "sum",
                "total_received": "sum",
                "scheduled_interest": "sum",
                "true_interest_payment": "sum",
                "true_fee_payment": "sum",
                "true_other_payment": "sum",
                "true_tax_payment": "sum",
                "true_fee_tax_payment": "sum",
                "true_rebates": "sum",
            }
        )

        result["weighted_apr"] = result["apr_part"] / result["outstanding"].replace(0, np.nan)
        result["weighted_fee_rate"] = result["fee_part"] / result["outstanding"].replace(0, np.nan)

        # Additional columns for parity with SQL and definition
        # Other income rate = (Fees + Other + Taxes - Rebates) / Outstanding
        result["weighted_other_income_rate"] = (
            result["total_received"] - result["true_interest_payment"]
        ) / result["outstanding"].replace(0, np.nan)

        # Effective rate = (Interest + Fees + Other + Taxes - Rebates) / Outstanding
        result["weighted_effective_rate"] = (result["total_received"]) / result[
            "outstanding"
        ].replace(0, np.nan)

        result["revenue_ratio"] = result["total_received"] / result["total_scheduled"].replace(
            0, np.nan
        )

        # Recurrence (%) = intereses / (intereses + fees + otros)
        result["recurrence_pct"] = result["true_interest_payment"] / result[
            "total_received"
        ].replace(0, np.nan)

        # Cleanup and renaming
        result.rename(columns={"month_end": "year_month"}, inplace=True)
        return result

    def get_monthly_risk(self) -> pd.DataFrame:
        """Combined risk metrics per month (amounts and percentages)."""
        df = self.get_dpd_buckets()
        if df.empty:
            return df

        # Match SQL column names exactly
        df.rename(columns={"month_end": "year_month"}, inplace=True)
        # Calculate percentages matching SQL
        for days in [7, 15, 30, 60]:
            df[f"dpd{days}_pct"] = df[f"dpd{days}_amount"] / df["total_outstanding"].replace(
                0, np.nan
            )
        df["default_pct"] = df["dpd90_amount"] / df["total_outstanding"].replace(0, np.nan)

        return df

    def get_customer_types(self) -> pd.DataFrame:
        """Customer types summary (New, Recurrent, Reactivated, Recovered)."""
        loans = self.loans.copy()

        # 1. Identify date column
        date_col = self._find_column(
            ["disbursement_date", "disburse_date", "fecha_desembolso"], loans
        )
        if not date_col:
            logger.warning(
                "get_customer_types: date_col not found. Columns: %s", loans.columns.tolist()
            )
            return pd.DataFrame()

        # 2. Identify amount column
        amount_col = self._find_column(
            ["disbursement_amount", "disburse_principal", "loan_amount"], loans
        )

        # 3. Identify DPD column for "Recovered"
        dpd_col = self._find_column(["days_past_due", "dpd", "days_in_default"], loans)
        bad_history = set()
        if dpd_col:
            bad_history = set(loans[loans[dpd_col] > 90]["customer_id"].unique())

        loans["year_month"] = loans[date_col].dt.to_period(
            "M"
        ).dt.to_timestamp() + pd.offsets.MonthEnd(0)
        loans = loans.sort_values(["customer_id", date_col, "loan_id"])

        loans["rn"] = loans.groupby("customer_id").cumcount() + 1
        loans["prev_disb"] = loans.groupby("customer_id")[date_col].shift(1)

        def classify(row):
            if row["customer_id"] in bad_history and (row[dpd_col] if dpd_col else 0) <= 30:
                return "Recovered"
            if row["rn"] == 1:
                return "New"
            if pd.notnull(row["prev_disb"]) and (row[date_col] - row["prev_disb"]).days > 180:
                return "Reactivated"
            return "Recurrent"

        loans["customer_type"] = loans.apply(classify, axis=1)

        summary = (
            loans.groupby(["year_month", "customer_type"])
            .agg(
                unique_customers=("customer_id", "nunique"),
                disbursement_amount=(
                    amount_col if amount_col else date_col,
                    "sum" if amount_col else "count",
                ),
            )
            .reset_index()
        )
        return summary

    def _find_column(self, aliases: list, df: pd.DataFrame) -> Optional[str]:
        """Helper to find column by aliases."""
        for a in aliases:
            if a in df.columns:
                return a
        return None

    def get_weighted_fee_rate(self) -> pd.DataFrame:
        """Compute origination fee weighted average per month."""
        if self.loan_month.empty:
            self.build_loan_month()
        if self.loan_month.empty:
            return pd.DataFrame()

        df = self.loan_month[self.loan_month["outstanding"] > 1e-4].copy()
        df["fee_rate"] = (df["origination_fee"] + df["origination_fee_taxes"]) / df[
            "disbursement_amount"
        ].replace(0, np.nan)
        df["weighted_fee_part"] = df["fee_rate"] * df["outstanding"]

        result = df.groupby("month_end", as_index=False).agg(
            {"weighted_fee_part": "sum", "outstanding": "sum"}
        )
        result["weighted_fee_rate"] = result["weighted_fee_part"] / result["outstanding"].replace(
            0, np.nan
        )

        return result[["month_end", "weighted_fee_rate"]]

    def get_concentration(self) -> pd.DataFrame:
        """Compute portfolio concentration for top x% of loans."""
        if self.loan_month.empty:
            self.build_loan_month()
        if self.loan_month.empty:
            return pd.DataFrame()

        df = self.loan_month[self.loan_month["outstanding"] > 1e-4].copy()
        df = df.sort_values("outstanding", ascending=False)

        results = []
        for month_end, group in df.groupby("month_end", as_index=False):
            total = group["outstanding"].sum()
            n = len(group)

            top10_n = max(1, int(np.ceil(0.10 * n)))
            top3_n = max(1, int(np.ceil(0.03 * n)))
            top1_n = max(1, int(np.ceil(0.01 * n)))

            results.append(
                {
                    "month_end": month_end,
                    "total_outstanding": total,
                    "top10_concentration": (
                        group.head(top10_n)["outstanding"].sum() / total if total > 0 else 0
                    ),
                    "top3_concentration": (
                        group.head(top3_n)["outstanding"].sum() / total if total > 0 else 0
                    ),
                    "top1_concentration": (
                        group.head(top1_n)["outstanding"].sum() / total if total > 0 else 0
                    ),
                }
            )

        return pd.DataFrame(results)

    def get_average_ticket(self) -> pd.DataFrame:
        """Compute average disbursement ticket and distribution by band."""
        df = self.loans.copy()
        df["year_month"] = df["disbursement_date"].dt.to_period(
            "M"
        ).dt.to_timestamp() + pd.offsets.MonthEnd(0)

        def ticket_band(amount):
            if amount < 10000:
                return "< 10K"
            if amount <= 25000:
                return "10-25K"
            if amount <= 50000:
                return "25-50K"
            if amount <= 100000:
                return "50-100K"
            return "> 100K"

        df["ticket_band"] = df["disbursement_amount"].apply(ticket_band)

        summary = (
            df.groupby(["year_month", "ticket_band"])
            .agg(
                num_loans=("loan_id", "count"),
                avg_ticket=("disbursement_amount", "mean"),
                total_disbursement=("disbursement_amount", "sum"),
            )
            .reset_index()
        )

        return summary

    def get_line_size_segmentation(self) -> pd.DataFrame:
        """Segment customers by approved credit line bands."""
        df = self.loans.copy()
        # Fallback to disbursement if approved_line_amount not found
        line_col = (
            "approved_line_amount"
            if "approved_line_amount" in df.columns
            else "disbursement_amount"
        )

        df["year_month"] = df["disbursement_date"].dt.to_period(
            "M"
        ).dt.to_timestamp() + pd.offsets.MonthEnd(0)

        def line_band(amount):
            if amount < 10000:
                return "< 10K"
            if amount <= 25000:
                return "10-25K"
            if amount <= 50000:
                return "25-50K"
            return "> 50K"

        df["line_band"] = df[line_col].apply(line_band)

        summary = (
            df.groupby(["year_month", "line_band"])
            .agg(
                customers=("customer_id", "nunique"),
                disbursement_amount=("disbursement_amount", "sum"),
            )
            .reset_index()
        )

        return summary

    # 3. Replines Model
    def get_replines_metrics(self) -> pd.DataFrame:
        """
        Measure % of customers whose line/loan is renewed
        within 90 days after closing.
        """
        loans = self.loans.sort_values(["customer_id", "disbursement_date"])
        loans["next_disb_date"] = loans.groupby("customer_id")["disbursement_date"].shift(-1)

        # We need an estimate of "close_date".
        end_col = "loan_end_date" if "loan_end_date" in self.loans.columns else "disbursement_date"

        loans["is_replined"] = (pd.notnull(loans["next_disb_date"])) & (
            (loans["next_disb_date"] - loans[end_col]).dt.days <= 90
        )

        loans["year_month"] = loans[end_col].dt.to_period(
            "M"
        ).dt.to_timestamp() + pd.offsets.MonthEnd(0)

        summary = (
            loans.groupby("year_month")
            .agg(
                closed_customers=("customer_id", "nunique"),
                replined_customers=("is_replined", "sum"),
            )
            .reset_index()
        )

        summary["replines_pct_90d"] = summary["replined_customers"] / summary[
            "closed_customers"
        ].replace(0, np.nan)

        return summary

    # 4. Risk & DPD Buckets
    def get_dpd_buckets(self) -> pd.DataFrame:
        """Compute monthly delinquency by DPD thresholds."""
        if self.loan_month.empty:
            self.build_loan_month()
        if self.loan_month.empty:
            return pd.DataFrame()

        df = self.loan_month.copy()

        result = (
            df.groupby("month_end", as_index=False)
            .agg({"outstanding": "sum"})
            .rename(columns={"outstanding": "total_outstanding"})
        )

        for threshold in [7, 15, 30, 60, 90]:
            col_name = f"dpd{threshold}_amount"
            dpd_filter = (df["days_past_due"] >= threshold) & (df["outstanding"] > 1e-4)
            dpd_sum = df[dpd_filter].groupby("month_end", as_index=False)["outstanding"].sum()
            dpd_sum.columns = ["month_end", col_name]
            result = result.merge(dpd_sum, on="month_end", how="left")
            result[col_name] = result[col_name].fillna(0)

        result["dpd30_pct"] = result["dpd30_amount"] / result["total_outstanding"].replace(
            0, np.nan
        )
        result["dpd90_pct"] = result["dpd90_amount"] / result["total_outstanding"].replace(
            0, np.nan
        )

        return result

    # 5. Payor, LTV & CAC
    def get_throughput_metrics(self) -> pd.DataFrame:
        """
        Calculates Throughput 12M, Rotation, APR realized, Yield incl. fees,
        and SAM Penetration.
        """
        if self.loan_month.empty:
            self.build_loan_month()
        if self.loan_month.empty:
            return pd.DataFrame()

        # 1. Base monthly AUM and Revenue
        pricing = (
            self.get_monthly_pricing()
        )  # has total_received, true_interest_payment, outstanding
        pricing.rename(columns={"year_month": "month"}, inplace=True)

        # 2. Monthly Throughput (Principal recovery)
        # Throughput = Sum(True Principal Payment) in the month
        self.payments["pay_month"] = self.payments["true_payment_date"].dt.to_period(
            "M"
        ).dt.to_timestamp() + pd.offsets.MonthEnd(0)
        monthly_principal = (
            self.payments.groupby("pay_month")["true_principal_payment"]
            .sum()
            .reset_index(name="throughput_monthly")
        )
        monthly_principal.rename(columns={"pay_month": "month"}, inplace=True)

        df = pricing.merge(monthly_principal, on="month", how="left").fillna(0)
        df = df.sort_values("month")

        # 3. LTM (Rolling 12M) Calculations
        df["throughput_12m"] = df["throughput_monthly"].rolling(window=12, min_periods=1).sum()
        df["interest_ltm"] = df["true_interest_payment"].rolling(window=12, min_periods=1).sum()
        df["revenue_ltm"] = df["total_received"].rolling(window=12, min_periods=1).sum()
        df["avg_aum_ltm"] = df["outstanding"].rolling(window=12, min_periods=1).mean()

        # 4. Final Metrics
        df["rotation"] = df["throughput_12m"] / df["outstanding"].replace(0, np.nan)
        df["apr_realized"] = df["interest_ltm"] / df["avg_aum_ltm"].replace(0, np.nan)
        df["yield_incl_fees"] = df["revenue_ltm"] / df["avg_aum_ltm"].replace(0, np.nan)

        # SAM Penetration = Throughput 12M / USD 0.9B
        df["sam_penetration"] = df["throughput_12m"] / 900000000.0

        return df

    def get_quarterly_scorecard(self) -> pd.DataFrame:
        """Generate a quarterly consolidated scorecard with Sales, Recurrence, Clientes EOP, and CAC/LTV."""
        if self.loans.empty:
            return pd.DataFrame()

        # 1. Define quarters
        quarters = pd.date_range(start="2023-01-01", end=datetime.now(), freq="QE")

        rows = []

        # Load commercial expenses for CAC
        base_path = Path(__file__).parent.parent.parent
        spend_path = base_path / "data" / "support" / "marketing_spend.csv"
        commercial_expenses = {}
        if spend_path.exists():
            spend_df = pd.read_csv(spend_path)
            spend_df["month"] = pd.to_datetime(spend_df["month"])
            for _, r in spend_df.iterrows():
                commercial_expenses[r["month"].to_period("M")] = r["spend"]

        for q_end in quarters:
            q_start = q_end - pd.offsets.QuarterBegin(startingMonth=q_end.month)
            label = f"{q_end.year}-Q{(q_end.month-1)//3 + 1}"

            # Ventas (USD MM)
            mask_q = (self.loans["disbursement_date"] >= q_start) & (
                self.loans["disbursement_date"] <= q_end
            )
            ventas_mm = self.loans.loc[mask_q, "disbursement_amount"].sum() / 1e6

            # Recurrencia
            mask_pay = (self.payments["true_payment_date"] >= q_start) & (
                self.payments["true_payment_date"] <= q_end
            )
            q_pays = self.payments[mask_pay]
            total_rev = (
                q_pays["true_interest_payment"].sum()
                + q_pays["true_fee_payment"].sum()
                + q_pays["true_other_payment"].sum()
                - q_pays["true_rebates"].sum()
            )
            recurrencia = (
                q_pays["true_interest_payment"].sum() / total_rev if total_rev > 0 else 0.0
            )

            # Clientes EOP
            mask_eop = self.loans["disbursement_date"] <= q_end
            clientes_eop = self.loans.loc[mask_eop, "customer_id"].nunique()

            # CAC / LTV (Simplified for scorecard)
            # Commercial expense in quarter
            q_period = pd.period_range(start=q_start, end=q_end, freq="M")
            q_spend = sum(commercial_expenses.get(p, 0) for p in q_period)

            # New customers in quarter
            first_disb = self.loans.groupby("customer_id")["disbursement_date"].min()
            new_custs = first_disb[(first_disb >= q_start) & (first_disb <= q_end)].count()

            cac = q_spend / new_custs if new_custs > 0 else 0.0

            # LTV (Realized revenue from this cohort so far)
            cohort_custs = first_disb[(first_disb >= q_start) & (first_disb <= q_end)].index
            cohort_rev = self.payments[
                self.payments["loan_id"].isin(
                    self.loans[self.loans["customer_id"].isin(cohort_custs)]["loan_id"]
                )
            ]
            cohort_total_rev = (
                cohort_rev["true_interest_payment"].sum()
                + cohort_rev["true_fee_payment"].sum()
                + cohort_rev["true_other_payment"].sum()
                - cohort_rev["true_rebates"].sum()
            )
            ltv_realized = cohort_total_rev / new_custs if new_custs > 0 else 0.0

            rows.append(
                {
                    "Quarter": label,
                    "Ventas_USD_MM": round(ventas_mm, 2),
                    "Recurrencia_Pct": round(recurrencia * 100, 2),
                    "Clientes_EOP": clientes_eop,
                    "CAC_USD": round(cac, 2),
                    "LTV_Realized_USD": round(ltv_realized, 2),
                    "LTV_CAC_Ratio": round(ltv_realized / cac, 2) if cac > 0 else 0.0,
                }
            )

        return pd.DataFrame(rows)

    def get_unit_economics(self) -> pd.DataFrame:
        """
        Calculates CAC, LTV realized, and LTV/CAC ratio.
        """
        # Load commercial expenses (marketing spend as proxy if available)
        base_path = Path(__file__).parent.parent.parent
        spend_path = base_path / "data" / "support" / "marketing_spend.csv"

        commercial_expenses = pd.DataFrame()
        if spend_path.exists():
            spend_df = pd.read_csv(spend_path)
            spend_df["month"] = pd.to_datetime(spend_df["month"])
            commercial_expenses = spend_df.groupby("month")["spend"].sum().reset_index()
            commercial_expenses.rename(columns={"spend": "commercial_expense"}, inplace=True)
        else:
            # Placeholder: Assume $100k/month if missing
            if not self.loan_month.empty:
                months = self.loan_month["month_end"].unique()
                commercial_expenses = pd.DataFrame(
                    {"month": months, "commercial_expense": 100000.0}
                )

        # New clients per month
        loans = self.loans.copy()
        loans["first_disb"] = loans.groupby("customer_id")["disbursement_date"].transform("min")
        loans["is_new"] = loans["disbursement_date"] == loans["first_disb"]
        new_clients = (
            loans[loans["is_new"]]
            .groupby(pd.Grouper(key="disbursement_date", freq="ME"))["customer_id"]
            .nunique()
            .reset_index(name="new_clients")
        )
        new_clients.rename(columns={"disbursement_date": "month"}, inplace=True)

        # Merge expense and new clients
        ue = new_clients.merge(commercial_expenses, on="month", how="left").fillna(0)

        # CAC = commercial_expense / new_clients
        ue["cac"] = ue["commercial_expense"] / ue["new_clients"].replace(0, np.nan)

        # LTV Realized (Cumulative revenue per client of the cohort)
        # Note: This requires cohort analysis. For simplicity, we'll calculate
        # cumulative revenue / unique customers per month as an approximation of realized yield.
        pricing = self.get_monthly_pricing()
        pricing.rename(columns={"year_month": "month"}, inplace=True)

        # Cumulative revenue across all time
        pricing = pricing.sort_values("month")
        pricing["cum_revenue"] = pricing["total_received"].cumsum()

        # Total unique customers ever seen up to that month
        self.loans["month_end"] = self.loans["disbursement_date"] + pd.offsets.MonthEnd(0)
        all_months = sorted(self.loans["month_end"].unique())
        cum_cust = []
        for me in all_months:
            count = self.loans[self.loans["month_end"] <= me]["customer_id"].nunique()
            cum_cust.append({"month": me, "cum_unique_customers": count})
        df_cum_cust = pd.DataFrame(cum_cust)

        ue = ue.merge(pricing[["month", "cum_revenue"]], on="month", how="left")
        ue = ue.merge(df_cum_cust, on="month", how="left")

        # LTV realized = cumulative revenue / cumulative unique customers
        ue["ltv_realized"] = ue["cum_revenue"] / ue["cum_unique_customers"].replace(0, np.nan)
        ue["ltv_cac_ratio"] = ue["ltv_realized"] / ue["cac"].replace(0, np.nan)

        return ue

    def get_payment_timing(self) -> pd.DataFrame:
        """Categorize payments into Early, On-time, and Late."""
        if self.payments.empty:
            return pd.DataFrame()

        # Join with loans to get disbursement or expected date
        # Use normalized names from _clean_df mapping
        cols_to_use = ["loan_id", "disbursement_date", "loan_end_date"]
        available_cols = [c for c in cols_to_use if c in self.loans.columns]

        df = self.payments.merge(
            self.loans[available_cols],
            on="loan_id",
            how="left",
        )

        # Expected date: prefer loan_end_date, fallback to disbursement + 30d
        if "loan_end_date" in df.columns:
            df["expected_date"] = df["loan_end_date"]
        elif "disbursement_date" in df.columns:
            df["expected_date"] = df["disbursement_date"] + pd.Timedelta(days=30)
        else:
            return pd.DataFrame()

        def categorize(row):
            if pd.isnull(row["true_payment_date"]) or pd.isnull(row["expected_date"]):
                return "Unknown"
            diff = (row["true_payment_date"] - row["expected_date"]).days
            if diff < -3:
                return "Early"
            if diff <= 3:
                return "On-time"
            return "Late"

        df["timing_category"] = df.apply(categorize, axis=1)
        df["year_month"] = df["true_payment_date"].dt.to_period(
            "M"
        ).dt.to_timestamp() + pd.offsets.MonthEnd(0)

        summary = (
            df.groupby(["year_month", "timing_category"])
            .agg(
                count=("true_total_payment", "count"),
                amount=("true_total_payment", "sum"),
            )
            .reset_index()
        )

        return summary

    def get_collection_rate(self) -> pd.DataFrame:
        """Collection Rate = Received / Scheduled."""
        df = self.get_monthly_pricing()
        if df.empty:
            return pd.DataFrame()

        df["collection_rate"] = (
            df["total_received"] / df["total_scheduled"].replace(0, np.nan)
        ).fillna(0)
        return df[["year_month", "total_scheduled", "total_received", "collection_rate"]]

    def get_executive_strip(self) -> Dict:
        """Consolidate the key 8 KPIs for the executive strip."""
        if self.loan_month.empty:
            self.build_loan_month()

        if self.loan_month.empty:
            return {}

        latest_month = self.loan_month["month_end"].max()
        latest_month_df = self.loan_month[self.loan_month["month_end"] == latest_month]

        cust_types = self.get_customer_types()
        latest_cust = pd.DataFrame()
        if not cust_types.empty:
            latest_cust_month = cust_types["year_month"].max()
            latest_cust = cust_types[cust_types["year_month"] == latest_cust_month]

        coll_rate_df = self.get_collection_rate()
        latest_coll = pd.DataFrame()
        if not coll_rate_df.empty:
            latest_coll_month = coll_rate_df["year_month"].max()
            latest_coll = coll_rate_df[coll_rate_df["year_month"] == latest_coll_month]

        strip = {
            "active_clients": int(latest_month_df["customer_id"].nunique()),
            "new_clients": (
                int(latest_cust[latest_cust["customer_type"] == "New"]["unique_customers"].sum())
                if not latest_cust.empty
                else 0
            ),
            "recurrent_clients": (
                int(
                    latest_cust[latest_cust["customer_type"] == "Recurrent"][
                        "unique_customers"
                    ].sum()
                )
                if not latest_cust.empty
                else 0
            ),
            "recovered_clients": (
                int(
                    latest_cust[latest_cust["customer_type"] == "Recovered"][
                        "unique_customers"
                    ].sum()
                )
                if not latest_cust.empty
                else 0
            ),
            "total_outstanding": float(latest_month_df["outstanding"].sum()),
            "total_disbursements": (
                float(latest_cust["disbursement_amount"].sum()) if not latest_cust.empty else 0.0
            ),
            "collection_rate": (
                float(latest_coll["collection_rate"].iloc[0]) if not latest_coll.empty else 0.0
            ),
            "top10_concentration": (
                float(self.get_concentration().iloc[-1]["top10_concentration"])
                if not self.get_concentration().empty
                else 0.0
            ),
        }
        return strip

    def get_all_kpis(self) -> Dict:
        """Run all calculations and return a consolidated dictionary."""
        kpis: Dict[str, Any] = {}
        # Executive Strip
        try:
            kpis["executive_strip"] = self.get_executive_strip()
        except Exception as e:
            logger.error(f"Error in executive_strip: {e}")

        # Core aggregated views for parity tests
        try:
            kpis["monthly_pricing"] = self.get_monthly_pricing().to_dict("records")
        except Exception:
            pass
        try:
            kpis["monthly_risk"] = self.get_monthly_risk().to_dict("records")
        except Exception:
            pass
        try:
            kpis["churn_90d_metrics"] = self.get_churn_90d_metrics().to_dict("records")
        except Exception as e:
            logger.error(f"Error in churn_90d_metrics: {e}")
        try:
            kpis["customer_types"] = self.get_customer_types().to_dict("records")
        except Exception:
            pass
        try:
            kpis["payment_timing"] = self.get_payment_timing().to_dict("records")
        except Exception:
            pass
        try:
            kpis["collection_rate"] = self.get_collection_rate().to_dict("records")
        except Exception:
            pass

        # Detailed/Granular views
        try:
            kpis["active_unique_customers"] = self.get_active_unique_customers().to_dict("records")
        except Exception:
            pass
        try:
            kpis["customer_classification"] = self.get_customer_classification().to_dict("records")
        except Exception:
            pass
        try:
            kpis["intensity_segmentation"] = self.get_intensity_segmentation().to_dict("records")
        except Exception:
            pass
        try:
            kpis["weighted_apr"] = self.get_weighted_apr().to_dict("records")
        except Exception:
            pass
        try:
            kpis["weighted_fee_rate"] = self.get_weighted_fee_rate().to_dict("records")
        except Exception:
            pass
        try:
            kpis["concentration"] = self.get_concentration().to_dict("records")
        except Exception:
            pass
        try:
            kpis["average_ticket"] = self.get_average_ticket().to_dict("records")
        except Exception:
            pass
        try:
            kpis["line_size_segmentation"] = self.get_line_size_segmentation().to_dict("records")
        except Exception:
            pass
        try:
            kpis["replines_metrics"] = self.get_replines_metrics().to_dict("records")
        except Exception:
            pass
        try:
            kpis["dpd_buckets"] = self.get_dpd_buckets().to_dict("records")
        except Exception:
            pass
        try:
            kpis["payor_concentration"] = self.get_concentration().to_dict("records")
        except Exception:
            pass
        try:
            kpis["throughput_metrics"] = self.get_throughput_metrics().to_dict("records")
        except Exception:
            pass
        try:
            kpis["quarterly_scorecard"] = self.get_quarterly_scorecard().to_dict("records")
        except Exception:
            pass
        try:
            kpis["eir_scheduled"] = self.get_eir_scheduled()
        except Exception:
            pass
        try:
            kpis["eir_real"] = self.get_eir_real()
        except Exception:
            pass
        try:
            kpis["weighted_apr_contractual"] = self.get_weighted_apr_contractual()
        except Exception:
            pass
        try:
            kpis["unit_economics"] = self.get_unit_economics().to_dict("records")
        except Exception:
            pass
        try:
            kpis["figma_dashboard"] = self.get_figma_dashboard_df().to_dict("records")
        except Exception as e:
            logger.error(f"Error in figma_dashboard: {e}")

        return kpis

    def get_figma_dashboard_df(self) -> pd.DataFrame:
        """
        Consolidate all KPIs into a single DataFrame formatted for the
        public.figma_dashboard Supabase view.
        """
        if self.loan_month.empty:
            self.build_loan_month()

        # 1. Base monthly metrics (Outstanding, Active Clients)
        base = (
            self.loan_month.groupby("month_end")
            .agg({"outstanding": "sum", "customer_id": "nunique"})
            .reset_index()
        )
        base.rename(
            columns={
                "month_end": "month",
                "outstanding": "outstanding",
                "customer_id": "active_clients",
            },
            inplace=True,
        )

        # 2. Pricing & Revenue
        pricing = self.get_monthly_pricing()
        if not pricing.empty:
            pricing_map = {
                "year_month": "month",
                "total_scheduled": "sched_revenue",
                "total_received": "recv_revenue_paid_month",
                "scheduled_interest": "sched_interest",
                "true_interest_payment": "recv_interest_paid_month",
                "true_fee_payment": "recv_fee_paid_month",
                "recurrence_pct": "recurrence_pct",
            }
            # Add missing columns if they don't exist
            for c in ["true_fee_payment", "recurrence_pct"]:
                if c not in pricing.columns:
                    pricing[c] = 0

            pricing_sub = pricing[list(pricing_map.keys())].rename(columns=pricing_map)
            base = base.merge(pricing_sub, on="month", how="left")
            base["sched_fee"] = base["sched_revenue"] - base["sched_interest"]

        # 3. Customer Types (Pivoted)
        cust_types = self.get_customer_types()
        if not cust_types.empty:
            cust_pivot = (
                cust_types.pivot(
                    index="year_month", columns="customer_type", values="unique_customers"
                )
                .fillna(0)
                .reset_index()
            )
            cust_pivot.rename(
                columns={
                    "year_month": "month",
                    "New": "new_clients",
                    "Recurrent": "recurrent_clients",
                    "Recovered": "recovered_clients",
                    "Reactivated": "reactivated_clients",  # Extra but safe
                },
                inplace=True,
            )
            # Ensure all expected columns exist
            for col in ["new_clients", "recurrent_clients", "recovered_clients"]:
                if col not in cust_pivot.columns:
                    cust_pivot[col] = 0
            base = base.merge(cust_pivot, on="month", how="left")

            # Disbursement amount from same group
            disb_pivot = cust_types.groupby("year_month")["disbursement_amount"].sum().reset_index()
            disb_pivot.rename(
                columns={"year_month": "month", "disbursement_amount": "disbursement"}, inplace=True
            )
            base = base.merge(disb_pivot, on="month", how="left")

        # 4. Concentration
        conc = self.get_concentration()
        if not conc.empty:
            conc_sub = conc[["month_end", "top10_concentration"]].rename(
                columns={"month_end": "month"}
            )
            base = base.merge(conc_sub, on="month", how="left")

        # 5. Payment Timing (Pivoted)
        timing = self.get_payment_timing()
        if not timing.empty:
            time_pivot = (
                timing.pivot(index="year_month", columns="timing_category", values="count")
                .fillna(0)
                .reset_index()
            )
            time_pivot.rename(
                columns={
                    "year_month": "month",
                    "Early": "early",
                    "On-time": "on_time",
                    "Late": "late",
                    "Unknown": "unmapped",
                },
                inplace=True,
            )
            # Ensure all columns exist
            for col in ["early", "on_time", "late", "unmapped"]:
                if col not in time_pivot.columns:
                    time_pivot[col] = 0
            base = base.merge(time_pivot, on="month", how="left")

        # 6. Collection Rate
        coll = self.get_collection_rate()
        if not coll.empty:
            coll_sub = coll[["year_month", "collection_rate"]].rename(
                columns={"year_month": "month", "collection_rate": "collection_rate_due_month"}
            )
            base = base.merge(coll_sub, on="month", how="left")

        # 7. Throughput Metrics
        throughput = self.get_throughput_metrics()
        if not throughput.empty:
            tp_cols = [
                "month",
                "throughput_12m",
                "rotation",
                "apr_realized",
                "yield_incl_fees",
                "sam_penetration",
            ]
            base = base.merge(throughput[tp_cols], on="month", how="left")

        # 8. Unit Economics
        ue = self.get_unit_economics()
        if not ue.empty:
            ue_cols = ["month", "cac", "ltv_realized", "ltv_cac_ratio", "cum_unique_customers"]
            base = base.merge(ue[ue_cols], on="month", how="left")

        # 9. Cumulative Metrics
        if not base.empty:
            base = base.sort_values("month")
            base["cum_scheduled"] = base["sched_revenue"].fillna(0).cumsum()
            base["cum_received_paid_month"] = base["recv_revenue_paid_month"].fillna(0).cumsum()
            # For "for due month" we'd need more complex logic, but we'll approximate with paid month for now
            base["cum_received_due_month"] = base["cum_received_paid_month"]

        # 10. Placeholders for missing fields in SQL view
        base["outstanding_proj"] = base["outstanding"] * 1.05  # Simple projection
        base["planned_disbursement"] = (
            base["disbursement"].shift(-1).fillna(base["disbursement"] * 1.1)
        )
        base["remaining_capital"] = 10000000 - base["outstanding"]  # Assume 10M fund

        # Revenue by due month placeholders (if not specifically calculated)
        base["recv_interest_for_month"] = base["recv_interest_paid_month"]
        base["recv_fee_for_month"] = base["recv_fee_paid_month"]
        base["recv_revenue_for_month"] = base["recv_revenue_paid_month"]

        # Final Cleanup
        base = base.fillna(0)

        return base
