"""Complete KPI Calculator for ABACO Loans - All Financial Metrics."""

import logging
# Built-ins para Pylance/Flake8
from builtins import Exception, all, any, len, list, max
from datetime import datetime
from typing import Dict, Optional

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABACOKPICalculator:
    """Comprehensive KPI calculator for ABACO loan portfolio."""

    def __init__(
        self,
        loans_df: pd.DataFrame,
        payments_df: pd.DataFrame,
        customers_df: pd.DataFrame,
    ):
        """Initialize with loan, payment, and customer data."""
        self.loans = self._clean_dataframe(loans_df)
        self.payments = self._clean_dataframe(payments_df)
        self.customers = self._clean_dataframe(customers_df)
        logger.info(
            "Initialized with %d loans, %d payments",
            len(self.loans),
            len(self.payments),
        )

    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean column names and convert dates."""
        df = df.copy()
        df.columns = [
            c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "")
            for c in df.columns
        ]

        # Auto-detect and convert date columns
        for col in df.columns:
            if any(x in col for x in ["date", "fecha"]):
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Synthetic loan_end_date if missing but term exists
        if "disbursement_date" in df.columns and "term" in df.columns:
            if "loan_end_date" not in df.columns and "maturity_date" not in df.columns:
                try:
                    unit = df["term_unit"].iloc[0].lower() if "term_unit" in df.columns else "days"
                    if "day" in unit:
                        df["loan_end_date"] = df["disbursement_date"] + pd.to_timedelta(
                            df["term"], unit="D"
                        )
                    elif "month" in unit:
                        df["loan_end_date"] = df["disbursement_date"] + pd.to_timedelta(
                            df["term"] * 30, unit="D"
                        )
                except Exception:
                    pass

        return df

    # === PORTFOLIO FUNDAMENTALS ===

    def get_active_clients(self) -> int:
        """Count unique active customers."""
        return self.loans["customer_id"].nunique()

    def get_total_aum(self) -> float:
        """Total Assets Under Management (Outstanding Balance)."""
        aliases = [
            "outstanding_loan_value",
            "outstanding_balance",
            "current_balance",
            "saldo",
        ]
        balance_col = self._find_column(aliases)
        if balance_col and balance_col in self.loans.columns:
            return pd.to_numeric(self.loans[balance_col], errors="coerce").sum()
        return 0.0

    def get_aum_by_customer_type(self) -> pd.DataFrame:
        """AUM breakdown by customer type."""
        balance_col = self._find_column(["outstanding_loan_value", "outstanding_balance"])

        merged = self.loans.merge(
            self.customers[["customer_id", "customer_type"]],
            on="customer_id",
            how="left",
        )

        if balance_col and balance_col in merged.columns:
            return merged.groupby("customer_type", dropna=False)[balance_col].sum().reset_index()
        return pd.DataFrame()

    # === REPLINES & PRODUCT MOMENTUM ===

    def get_replines_percentage(self) -> float:
        """
        Replines % = (Disbursements CM) / (Matured Loans CM) * 100
        CM = Current Month. Measures re-lending of matured portfolio.
        """
        disb_col = self._find_column(["disbursement_date", "disburse_date"])
        end_col = self._find_column(["loan_end_date", "maturity_date"])
        amount_col = self._find_column(["loan_amount", "disburse_principal", "disbursement_amount"])

        if not all([disb_col, end_col, amount_col]):
            logger.warning("Cannot calculate replines: missing date or amount columns")
            return 0.0

        try:
            # Use the latest month in the dataset
            all_disb_months = self.loans[disb_col].dt.to_period("M")
            if all_disb_months.empty:
                return 0.0

            latest_month = all_disb_months.max()

            # Disbursements in current month
            disb_df = self.loans[self.loans[disb_col].dt.to_period("M") == latest_month]
            total_disb = pd.to_numeric(disb_df[amount_col], errors="coerce").sum()

            # Matured loans in current month
            matured_df = self.loans[self.loans[end_col].dt.to_period("M") == latest_month]
            total_matured = pd.to_numeric(matured_df[amount_col], errors="coerce").sum()

            replines = (total_disb / max(total_matured, 1)) * 100
            return float(replines) if replines > 0 else 0.0
        except Exception as e:
            logger.error("Error calculating replines: %s", e)
            return 0.0

    # === REVENUE METRICS ===

    def get_monthly_revenue(self) -> float:
        """Total payment/revenue in current month."""
        payment_col = self._find_column(
            ["payment_amount", "amount", "monto_pago", "true_total_payment"], self.payments
        )
        date_col = self._find_column(
            ["payment_date", "fecha_pago", "true_payment_date"], self.payments
        )

        if not payment_col or payment_col not in self.payments.columns:
            logger.warning("Cannot calculate monthly revenue: missing payment column")
            return 0.0

        try:
            # Use the latest month in the dataset if current month has no data
            all_months = self.payments[date_col].dt.to_period("M")
            if all_months.empty:
                return 0.0

            latest_month = all_months.max()
            monthly = self.payments[self.payments[date_col].dt.to_period("M") == latest_month]
            return pd.to_numeric(monthly[payment_col], errors="coerce").sum()
        except Exception as e:
            logger.error("Error calculating monthly revenue: %s", e)
            return 0.0

    def get_revenue_by_month(self) -> pd.Series:
        """Monthly revenue trend."""
        payment_col = self._find_column(
            ["payment_amount", "amount", "true_total_payment"], self.payments
        )
        date_col = self._find_column(
            ["payment_date", "fecha_pago", "true_payment_date"], self.payments
        )

        if not payment_col:
            return pd.Series()

        self.payments["month"] = self.payments[date_col].dt.to_period("M")
        return self.payments.groupby("month")[payment_col].sum()

    # === GROWTH METRICS ===

    def get_mom_growth_pct(self) -> float:
        """Month-over-Month growth percentage."""
        balance_col = self._find_column(["outstanding_loan_value", "outstanding_balance"])
        disb_date_col = self._find_column(["disbursement_date", "disburse_date"])
        if not balance_col or not disb_date_col:
            return 0.0

        try:
            self.loans["month"] = self.loans[disb_date_col].dt.to_period("M")
            aum_by_month = self.loans.groupby("month")[balance_col].sum().sort_index()

            if len(aum_by_month) < 2:
                return 0.0

            mom = aum_by_month.pct_change().iloc[-1] * 100
            return float(mom) if not np.isnan(mom) else 0.0
        except Exception as e:
            logger.error("Error calculating MoM: %s", e)
            return 0.0

    def get_yoy_growth_pct(self) -> float:
        """Year-over-Year growth percentage."""
        balance_col = self._find_column(["outstanding_loan_value", "outstanding_balance"])
        disb_date_col = self._find_column(["disbursement_date", "disburse_date"])
        if not balance_col or not disb_date_col:
            return 0.0

        try:
            self.loans["month"] = self.loans[disb_date_col].dt.to_period("M")
            aum_by_month = self.loans.groupby("month")[balance_col].sum().sort_index()

            if len(aum_by_month) < 13:
                logger.warning("Insufficient data for YoY calculation (need 13+ months)")
                return 0.0

            yoy = ((aum_by_month.iloc[-1] - aum_by_month.iloc[-13]) / aum_by_month.iloc[-13]) * 100
            return float(yoy) if not np.isnan(yoy) else 0.0
        except Exception as e:
            logger.error("Error calculating YoY: %s", e)
            return 0.0

    # === REVENUE PER CLIENT ===

    def get_revenue_per_active_client(self) -> float:
        """Monthly revenue divided by active clients."""
        active_clients = self.get_active_clients()
        monthly_revenue = self.get_monthly_revenue()

        if active_clients == 0:
            return 0.0

        return monthly_revenue / active_clients

    def get_annual_revenue_per_client(self) -> float:
        """Annualized revenue per client."""
        return self.get_revenue_per_active_client() * 12

    # === CAC & LTV / CAC RATIO ===

    def get_ltv_cac_ratio(self, cac_usd: float = 350.0) -> float:
        """
        LTV / CAC Ratio = (Annual Revenue per Client) / CAC
        Measures efficiency of customer acquisition.
        Healthy ratio: > 3.0x
        """
        annual_revenue = self.get_annual_revenue_per_client()

        if cac_usd <= 0:
            logger.warning("Invalid CAC value provided")
            return 0.0

        ratio = annual_revenue / cac_usd
        return float(ratio)

    # === DELINQUENCY METRICS ===

    def get_delinquency_rate(self, dpd_threshold: int = 30) -> float:
        """Percentage of loans with Days Past Due >= threshold."""
        dpd_col = self._find_column(["dpd", "days_past_due", "diasvencidos"])

        if not dpd_col or dpd_col not in self.loans.columns:
            return 0.0

        delinquent = (pd.to_numeric(self.loans[dpd_col], errors="coerce") >= dpd_threshold).sum()
        total = len(self.loans)

        return (delinquent / total * 100) if total > 0 else 0.0

    def get_par_90_ratio(self) -> float:
        """Portfolio at Risk (90+DPD) as % of outstanding balance."""
        dpd_col = self._find_column(["dpd", "days_past_due"])
        balance_col = self._find_column(["outstanding_loan_value", "outstanding_balance"])

        if not all([dpd_col, balance_col]):
            return 0.0

        loans_at_risk = self.loans[pd.to_numeric(self.loans[dpd_col], errors="coerce") >= 90]
        balance_at_risk = pd.to_numeric(loans_at_risk[balance_col], errors="coerce").sum()
        total_balance = pd.to_numeric(self.loans[balance_col], errors="coerce").sum()

        return (balance_at_risk / total_balance * 100) if total_balance > 0 else 0.0

    # === PORTFOLIO COMPOSITION ===

    def get_portfolio_by_product(self) -> pd.DataFrame:
        """Loan count and AUM by product type."""
        product_col = self._find_column(["product_type", "product"])
        balance_col = self._find_column(["outstanding_loan_value", "outstanding_balance"])

        if not product_col:
            return pd.DataFrame()

        result = (
            self.loans.groupby(product_col, dropna=False)
            .agg({"loan_id": "count", balance_col: "sum"})
            .rename(columns={"loan_id": "loan_count", balance_col: "aum"})
        )

        return result.reset_index()

    def get_portfolio_by_status(self) -> pd.DataFrame:
        """Loan distribution by status."""
        status_col = self._find_column(["loan_status", "status", "estado"])

        if not status_col:
            return pd.DataFrame()

        return self.loans[status_col].value_counts().reset_index()

    # === COMPREHENSIVE DASHBOARD ===

    def get_complete_kpi_dashboard(self, cac_usd: float = 350.0) -> Dict:
        """Generate complete KPI dashboard."""
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            # Portfolio Fundamentals
            "active_clients": self.get_active_clients(),
            "total_aum_usd": round(self.get_total_aum(), 2),
            "aum_by_customer_type": (
                self.get_aum_by_customer_type().to_dict("records")
                if not self.get_aum_by_customer_type().empty
                else []
            ),
            # Product Momentum
            "replines_percentage": round(self.get_replines_percentage(), 2),
            # Revenue
            "monthly_revenue_usd": round(self.get_monthly_revenue(), 2),
            "revenue_per_active_client_monthly": round(self.get_revenue_per_active_client(), 2),
            "revenue_per_active_client_annual": round(self.get_annual_revenue_per_client(), 2),
            # Growth
            "mom_growth_pct": round(self.get_mom_growth_pct(), 2),
            "yoy_growth_pct": round(self.get_yoy_growth_pct(), 2),
            # Efficiency
            "ltv_cac_ratio": round(self.get_ltv_cac_ratio(cac_usd), 2),
            "cac_usd": cac_usd,
            # Risk
            "delinquency_rate_30_pct": round(self.get_delinquency_rate(30), 2),
            "delinquency_rate_90_pct": round(self.get_delinquency_rate(90), 2),
            "par_90_ratio_pct": round(self.get_par_90_ratio(), 2),
            # Composition
            "portfolio_by_product": (
                self.get_portfolio_by_product().to_dict("records")
                if not self.get_portfolio_by_product().empty
                else []
            ),
            "portfolio_by_status": (
                self.get_portfolio_by_status().to_dict("records")
                if not self.get_portfolio_by_status().empty
                else []
            ),
        }

        return dashboard

    # === HELPER METHODS ===

    def _find_column(self, aliases: list, dataframe=None) -> Optional[str]:
        """Find actual column name from list of aliases.

        Args:
            aliases: List of column name aliases to search for
            dataframe: Optional dataframe to search in. Defaults to self.loans.
                      Pass self.payments to search payments dataframe.
        """
        df = dataframe if dataframe is not None else self.loans
        for alias in aliases:
            if alias in df.columns:
                return alias
        logger.warning("Column not found. Searched for: %s", aliases)
        return None


def main():
    """Example usage and demonstration."""
    # === MOCK DATA EXAMPLE ===
    np.random.seed(42)

    loans_data = {
        "loan_id": [f"L{i:05d}" for i in range(100)],
        "customer_id": [f"C{np.random.randint(1, 51):04d}" for i in range(100)],
        "disbursement_date": pd.date_range("2023-01-01", periods=100, freq="3D"),
        "loan_end_date": pd.date_range("2023-02-01", periods=100, freq="3D"),
        "loan_amount": np.random.uniform(1000, 50000, 100),
        "outstanding_loan_value": np.random.uniform(500, 45000, 100),
        "dpd": np.random.choice([0, 15, 45, 90], 100, p=[0.7, 0.15, 0.1, 0.05]),
        "loan_status": np.random.choice(
            ["Active", "Completed", "Defaulted"], 100, p=[0.6, 0.3, 0.1]
        ),
        "product_type": np.random.choice(["Factoring", "LOC", "Term Loan"], 100),
    }

    payments_data = {
        "payment_id": [f"P{i:06d}" for i in range(200)],
        "loan_id": np.random.choice(loans_data["loan_id"], 200),
        "payment_date": pd.date_range("2023-01-01", periods=200, freq="2D"),
        "payment_amount": np.random.uniform(100, 5000, 200),
    }

    customers_data = {
        "customer_id": [f"C{i:04d}" for i in range(1, 51)],
        "customer_type": np.random.choice(["SME", "Corporate", "Individual"], 50),
    }

    loans_df = pd.DataFrame(loans_data)
    payments_df = pd.DataFrame(payments_data)
    customers_df = pd.DataFrame(customers_data)

    # === RUN CALCULATOR ===
    calc = ABACOKPICalculator(loans_df, payments_df, customers_df)
    dashboard = calc.get_complete_kpi_dashboard(cac_usd=350)

    # === DISPLAY RESULTS ===
    print("\n" + "=" * 70)
    print("\ud83d\udcca ABACO COMPLETE KPI DASHBOARD")
    print("=" * 70)
    print(f"Generated: {dashboard['timestamp']}\n")

    print("\ud83d\udc65 PORTFOLIO FUNDAMENTALS")
    print(f"  Active Clients: {dashboard['active_clients']:,}")
    print(f"  Total AUM: ${dashboard['total_aum_usd']:,.2f}\n")

    print("\ud83d\udcc8 PRODUCT MOMENTUM")
    print(f"  Replines %: {dashboard['replines_percentage']:.2f}%\n")

    print("\ud83d\udcb5 REVENUE")
    print(f"  Monthly Revenue: ${dashboard['monthly_revenue_usd']:,.2f}")
    rev_per_client = dashboard["revenue_per_active_client_monthly"]
    print(f"  Revenue/Client (Monthly): ${rev_per_client:,.2f}")


if __name__ == "__main__":
    main()
