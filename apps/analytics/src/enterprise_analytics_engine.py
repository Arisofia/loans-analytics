import pandas as pd
import numpy as np
from typing import Dict, Optional, Protocol, runtime_checkable


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
                Expected columns: 'loan_amount', 'appraised_value', 'borrower_income',
                                  'monthly_debt', 'loan_status', 'interest_rate', 'principal_balance'.
        """
        if not isinstance(loan_data, pd.DataFrame) or loan_data.empty:
            raise ValueError("Input loan_data must be a non-empty pandas DataFrame.")

        self.loan_data = loan_data.copy()
        self._validate_columns()

    @classmethod
    def from_dict(cls, data: Dict[str, list]) -> "LoanAnalyticsEngine":
        return cls(pd.DataFrame(data))

    def _validate_columns(self):
        """Ensures the DataFrame contains the necessary columns for KPI computation."""
        required_cols = [
            'loan_amount', 'appraised_value', 'borrower_income', 'monthly_debt',
            'loan_status', 'interest_rate', 'principal_balance'
        ]
        missing_cols = [col for col in required_cols if col not in self.loan_data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in loan_data: {', '.join(missing_cols)}")

    def compute_loan_to_value(self) -> pd.Series:
        """Computes the Loan-to-Value (LTV) ratio for each loan."""
        appraised_value = self.loan_data['appraised_value']
        ltv_values = np.where(
            appraised_value > 0,
            (self.loan_data['loan_amount'] / appraised_value) * 100,
            np.nan,
        )
        ltv_series = pd.Series(ltv_values, index=self.loan_data.index)
        ltv_series = ltv_series.replace([np.inf, -np.inf], np.nan)

        self.loan_data['ltv_ratio'] = ltv_series
        return ltv_series

    def compute_debt_to_income(self) -> pd.Series:
        """Computes the Debt-to-Income (DTI) ratio for each borrower."""
        # Assuming borrower_income is annual, convert to monthly
        monthly_income = self.loan_data['borrower_income'] / 12
        # Avoid division by zero and preserve index alignment by returning a Series
        dti_values = np.where(
            monthly_income > 0,
            (self.loan_data['monthly_debt'] / monthly_income) * 100,
            np.nan,
        )
        dti_series = pd.Series(dti_values, index=self.loan_data.index)

        self.loan_data['dti_ratio'] = dti_series
        return dti_series

    def compute_delinquency_rate(self) -> float:
        """Computes the overall portfolio delinquency rate."""
        delinquent_statuses = ['30-59 days past due', '60-89 days past due', '90+ days past due']
        delinquent_count = self.loan_data['loan_status'].isin(delinquent_statuses).sum()
        total_loans = len(self.loan_data)
        return (delinquent_count / total_loans) * 100 if total_loans > 0 else 0.0

    def compute_portfolio_yield(self) -> float:
        """Computes the weighted average portfolio yield."""
        total_principal = self.loan_data['principal_balance'].sum()
        if total_principal == 0:
            return 0.0

        weighted_interest = (self.loan_data['interest_rate'] * self.loan_data['principal_balance']).sum()
        return (weighted_interest / total_principal) * 100

    def run_full_analysis(self) -> Dict[str, float]:
        """
        Runs a comprehensive analysis and returns a dictionary of portfolio-level KPIs.
        Ensures all keys from portfolio_kpis are included in the output.
        """
        # Compute the original dashboard

        dashboard = {
            "portfolio_delinquency_rate_percent": self.compute_delinquency_rate(),
            "portfolio_yield_percent": self.compute_portfolio_yield(),
            "average_ltv_ratio_percent": self.loan_data['ltv_ratio'].mean(),
            "average_dti_ratio_percent": self.loan_data['dti_ratio'].mean(),
        }
        # Import and call portfolio_kpis to ensure all expected keys are present
        try:
            from apps.analytics.src.metrics_utils import portfolio_kpis
        except ImportError:
            from .metrics_utils import portfolio_kpis
        kpi_results = portfolio_kpis(self.loan_data)
        dashboard.update(kpi_results)
        return dashboard

    def export_kpis_to_blob(
        self, exporter: KPIExporter, blob_name: Optional[str] = None
    ) -> str:
        if blob_name is not None and not isinstance(blob_name, str):
            raise ValueError("blob_name must be a string if provided.")

        kpis = self.run_full_analysis()
        return exporter.upload_metrics(kpis, blob_name=blob_name)

if __name__ == '__main__':
    # Example usage demonstrating the engine's capabilities
    # This simulates a data-driven workflow for generating actionable insights.

    # Sample data representing a loan portfolio
    data = {
        'loan_amount': [250000, 450000, 150000, 600000],
        'appraised_value': [300000, 500000, 160000, 750000],
        'borrower_income': [80000, 120000, 60000, 150000],
        'monthly_debt': [1500, 2500, 1000, 3000],
        'loan_status': ['current', '30-59 days past due', 'current', 'current'],
        'interest_rate': [0.035, 0.042, 0.038, 0.045],
        'principal_balance': [240000, 440000, 145000, 590000]
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
