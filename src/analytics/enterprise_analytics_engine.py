import logging
from typing import Dict, Optional, Protocol, runtime_checkable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@runtime_checkable
class KPIExporter(Protocol):
    def upload_metrics(self, metrics: Dict[str, float], blob_name: Optional[str] = None) -> str:
        pass


class LoanAnalyticsEngine:
    """
    A robust engine for computing critical KPIs for a loan portfolio.
    This system is designed for scalability and provides traceable, actionable insights
    to drive financial intelligence and commercial growth.
    """

    @property
    def coercion_report(self):
        return self._coercion_report

    def __init__(self, loan_data: pd.DataFrame):
        """
        Initializes the engine with loan portfolio data.

        Args:
            loan_data (pd.DataFrame): A DataFrame containing loan records.
                Expected columns: 'loan_amount', 'appraised_value',
                'borrower_income', 'monthly_debt', 'loan_status',
                'interest_rate', 'principal_balance'.
        """
        if not isinstance(loan_data, pd.DataFrame) or loan_data.empty:
            raise ValueError("Input loan_data must be a non-empty pandas DataFrame.")

        self.loan_data = loan_data.copy()
        self._coercion_report: Dict[str, int] = {}
        self._validate_columns()
        self._coerce_numeric_columns()
        self._check_data_sanity()

    @classmethod
    def from_dict(cls, data: Dict[str, list]) -> "LoanAnalyticsEngine":
        return cls(pd.DataFrame(data))

    def _validate_columns(self):
        """Ensures the DataFrame contains the necessary columns for KPI computation."""
        required_cols = [
            "loan_amount",
            "appraised_value",
            "borrower_income",
            "monthly_debt",
            "loan_status",
            "interest_rate",
            "principal_balance",
        ]
        missing_cols = [col for col in required_cols if col not in self.loan_data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in loan_data: {', '.join(missing_cols)}")

    def _coerce_numeric_columns(self):
        """Coerce numeric columns to float and track invalid conversions."""
        numeric_cols = [
            "loan_amount",
            "appraised_value",
            "borrower_income",
            "monthly_debt",
            "interest_rate",
            "principal_balance",
        ]
        for col in numeric_cols:
            if col in self.loan_data.columns:
                invalid_count = 0
                coerced_values = []
                for val in self.loan_data[col]:
                    try:
                        coerced_values.append(float(val))
                    except (ValueError, TypeError):
                        coerced_values.append(np.nan)
                        invalid_count += 1
                self.loan_data[col] = coerced_values
                if invalid_count > 0:
                    self._coercion_report[col] = invalid_count

    def _check_data_sanity(self):
        """Check data sanity and log warnings for suspicious values."""
        if "interest_rate" in self.loan_data.columns:
            max_rate = self.loan_data["interest_rate"].max()
            if max_rate > 1.0:
                logger.warning(
                    "Max interest_rate is %s. "
                    "Ensure rates are ratios (e.g., 0.035 for 3.5%%) not percentages.",
                    max_rate,
                )

    def compute_loan_to_value(self) -> pd.Series:
        """Computes the Loan-to-Value (LTV) ratio for each loan."""
        appraised_value = self.loan_data["appraised_value"]
        ltv_values = np.where(
            appraised_value > 0,
            (self.loan_data["loan_amount"] / appraised_value) * 100,
            np.nan,
        )
        ltv_series = pd.Series(ltv_values, index=self.loan_data.index)
        ltv_series = ltv_series.replace([np.inf, -np.inf], np.nan)

        self.loan_data["ltv_ratio"] = ltv_series
        return ltv_series

    def compute_debt_to_income(self) -> pd.Series:
        """Computes the Debt-to-Income (DTI) ratio for each borrower."""
        # Assuming borrower_income is annual, convert to monthly
        monthly_income = self.loan_data["borrower_income"] / 12
        # Avoid division by zero and preserve index alignment by returning a Series
        dti_values = np.where(
            monthly_income > 0,
            (self.loan_data["monthly_debt"] / monthly_income) * 100,
            np.nan,
        )
        dti_series = pd.Series(dti_values, index=self.loan_data.index)

        self.loan_data["dti_ratio"] = dti_series
        return dti_series

    def compute_delinquency_rate(self) -> float:
        """Computes the portfolio delinquency rate using KPIEngineV2."""
        from src.kpi_engine_v2 import \
            KPIEngineV2  # pylint: disable=import-outside-toplevel

        engine_v2 = KPIEngineV2(self.loan_data, actor="enterprise_engine")
        val, _ = engine_v2.calculate_par_30()
        return float(val)

    def compute_portfolio_yield(self) -> float:
        """Computes the weighted average portfolio yield using KPIEngineV2."""
        from src.kpi_engine_v2 import \
            KPIEngineV2  # pylint: disable=import-outside-toplevel

        engine_v2 = KPIEngineV2(self.loan_data, actor="enterprise_engine")
        val, _ = engine_v2.calculate_portfolio_yield()
        return float(val)

    def data_quality_profile(self) -> Dict[str, float]:
        """
        Analyzes data quality and returns a profile with metrics.

        Returns:
            Dict with keys: duplicate_ratio, average_null_ratio,
            data_quality_score, invalid_numeric_ratio
        """
        df = self.loan_data

        duplicate_rows = df.duplicated().sum()
        total_rows = len(df)
        duplicate_ratio = (duplicate_rows / total_rows * 100) if total_rows > 0 else 0.0

        null_counts = df.isnull().sum().sum()
        total_cells = df.size
        average_null_ratio = (null_counts / total_cells * 100) if total_cells > 0 else 0.0

        invalid_count = sum(self._coercion_report.values())
        numeric_cols = [
            "loan_amount",
            "appraised_value",
            "borrower_income",
            "monthly_debt",
            "interest_rate",
            "principal_balance",
        ]
        numeric_col_count = len([col for col in numeric_cols if col in df.columns])
        total_numeric_cells = total_rows * numeric_col_count
        invalid_numeric_ratio = (
            (invalid_count / total_numeric_cells * 100) if total_numeric_cells > 0 else 0.0
        )

        data_quality_score = (
            100.0 - (duplicate_ratio + average_null_ratio + invalid_numeric_ratio) / 3
        )
        data_quality_score = max(0, min(100, data_quality_score))

        return {
            "duplicate_ratio": duplicate_ratio,
            "average_null_ratio": average_null_ratio,
            "invalid_numeric_ratio": invalid_numeric_ratio,
            "data_quality_score": data_quality_score,
        }

    def risk_alerts(self, ltv_threshold: float = 80.0, dti_threshold: float = 50.0) -> pd.DataFrame:
        """
        Identifies high-risk loans based on LTV and DTI thresholds.

        Args:
            ltv_threshold: LTV ratio threshold (default 80%)
            dti_threshold: DTI ratio threshold (default 50%)

        Returns:
            DataFrame with high-risk loans and their risk scores
        """
        if "ltv_ratio" not in self.loan_data.columns:
            self.compute_loan_to_value()
        if "dti_ratio" not in self.loan_data.columns:
            self.compute_debt_to_income()

        ltv = self.loan_data["ltv_ratio"]
        dti = self.loan_data["dti_ratio"]

        high_risk = (ltv > ltv_threshold) | (dti > dti_threshold)
        risk_loans = self.loan_data[high_risk].copy()

        if not risk_loans.empty:
            risk_loans["ltv_ratio"] = ltv[high_risk]
            risk_loans["dti_ratio"] = dti[high_risk]

            ltv_norm = (risk_loans["ltv_ratio"].fillna(0) / 100).clip(0, 1)
            dti_norm = (risk_loans["dti_ratio"].fillna(0) / 100).clip(0, 1)
            risk_loans["risk_score"] = (ltv_norm + dti_norm) / 2

        return risk_loans

    def run_full_analysis(self) -> Dict[str, float]:
        """
        Runs a comprehensive analysis and returns a portfolio-level KPIs dict.
        Delegates core computations to KPIEngineV2 for consistency.
        """
        from src.kpi_engine_v2 import \
            KPIEngineV2  # pylint: disable=import-outside-toplevel

        engine_v2 = KPIEngineV2(self.loan_data, actor="enterprise_engine")
        results = engine_v2.calculate_all()

        dashboard = {
            "portfolio_delinquency_rate_percent": results.get("PAR30", {}).get("value", 0.0),
            "portfolio_yield_percent": engine_v2.get_metric("PortfolioYield") or 0.0,
            "average_ltv_ratio_percent": engine_v2.get_metric("LTV") or 0.0,
            "average_dti_ratio_percent": engine_v2.get_metric("DTI") or 0.0,
            # Short keys for backward compatibility
            "delinquency_rate": results.get("PAR30", {}).get("value", 0.0),
            "portfolio_yield": engine_v2.get_metric("PortfolioYield") or 0.0,
            "average_ltv": engine_v2.get_metric("LTV") or 0.0,
            "average_dti": engine_v2.get_metric("DTI") or 0.0,
        }

        quality = self.data_quality_profile()
        dashboard.update(
            {
                "data_quality_score": quality["data_quality_score"],
                "average_null_ratio_percent": quality["average_null_ratio"],
                "invalid_numeric_ratio_percent": quality["invalid_numeric_ratio"],
            }
        )

        return dashboard

    def export_kpis_to_blob(self, exporter: KPIExporter, blob_name: Optional[str] = None) -> str:
        if blob_name is not None and not isinstance(blob_name, str):
            raise ValueError("blob_name must be a string if provided.")

        kpis = self.run_full_analysis()
        return exporter.upload_metrics(kpis, blob_name=blob_name)


if __name__ == "__main__":
    # Example usage demonstrating the engine's capabilities
    # This simulates a data-driven workflow for generating actionable insights.

    # Sample data representing a loan portfolio
    data = {
        "loan_amount": [250000, 450000, 150000, 600000],
        "appraised_value": [300000, 500000, 160000, 750000],
        "borrower_income": [80000, 120000, 60000, 150000],
        "monthly_debt": [1500, 2500, 1000, 3000],
        "loan_status": ["current", "30-59 days past due", "current", "current"],
        "interest_rate": [0.035, 0.042, 0.038, 0.045],
        "principal_balance": [240000, 440000, 145000, 590000],
    }
    portfolio_df = pd.DataFrame(data)

    # Initialize and run the analytics engine
    engine = LoanAnalyticsEngine(portfolio_df)
    kpi_dashboard = engine.run_full_analysis()

    # Output the KPI dashboard - ready for visualization or reporting
    print("--- Loan Portfolio KPI Dashboard ---")
    for kpi, value in kpi_dashboard.items():
        print(f"{kpi.replace('_', ' ').title()}: {value:.2f}")
    print("------------------------------------")
