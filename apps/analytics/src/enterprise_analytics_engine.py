import numpy as np
<<<<<<< HEAD
from typing import Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class KPIExporter(Protocol):
    def upload_metrics(self, metrics: Dict[str, float], blob_name: Optional[str] = None) -> str:
        ...
=======
import pandas as pd
from typing import Dict, List
>>>>>>> origin/main

class LoanAnalyticsEngine:
    """
    A robust engine for computing critical KPIs for a loan portfolio.
    This system is designed for scalability and provides traceable, actionable insights
    to drive financial intelligence and commercial growth.
    """

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
        self._coercion_report = self._coerce_numeric_columns()

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

    def _coerce_numeric_columns(self) -> Dict[str, int]:
        """
        Convert numeric columns to proper dtypes while recording invalid values for auditability.

        Returns:
            Dict[str, int]: Count of values per column that became NaN during coercion.
        """
        numeric_cols: List[str] = [
            'loan_amount',
            'appraised_value',
            'borrower_income',
            'monthly_debt',
            'interest_rate',
            'principal_balance',
        ]

        coercion_report: Dict[str, int] = {}
        for col in numeric_cols:
            original = self.loan_data[col]
            coerced = pd.to_numeric(original, errors='coerce')
            invalid_count = int(coerced.isna().sum() - original.isna().sum())
            coercion_report[col] = max(invalid_count, 0)
            self.loan_data[col] = coerced

        return coercion_report

    def compute_loan_to_value(self) -> pd.Series:
        """Computes the Loan-to-Value (LTV) ratio for each loan while avoiding division by zero."""
        appraised_value = self.loan_data['appraised_value'].replace(0, np.nan)
        ltv = (self.loan_data['loan_amount'] / appraised_value) * 100
        return ltv.replace([np.inf, -np.inf], np.nan)

    def compute_debt_to_income(self) -> pd.Series:
        """Computes the Debt-to-Income (DTI) ratio for each borrower."""
        monthly_income = self.loan_data['borrower_income'] / 12
        positive_income = monthly_income > 0
        dti = np.where(
            positive_income,
            (self.loan_data['monthly_debt'] / monthly_income) * 100,
            np.nan
        )
        return pd.Series(dti, index=self.loan_data.index)

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

    def data_quality_profile(self) -> Dict[str, float]:
        """
        Generates a lightweight data quality profile to keep KPI calculations auditable and traceable.

        Returns:
            Dict[str, float]: Percentages for completeness and duplicate risk, plus the volume inspected.
        """
        row_count = len(self.loan_data)
        null_ratio = float(self.loan_data.isna().mean().mean())
        duplicate_ratio = float(self.loan_data.duplicated().mean())

        total_numeric_cells = row_count * len(self._coercion_report) if row_count else 0
        invalid_numeric_ratio = (
            sum(self._coercion_report.values()) / total_numeric_cells
            if total_numeric_cells
            else 0.0
        )

        data_quality_score = max(
            0.0,
            100
            - (null_ratio * 100)
            - (duplicate_ratio * 50)
            - (invalid_numeric_ratio * 60),
        )

        return {
            "row_count": float(row_count),
            "average_null_ratio": round(null_ratio * 100, 2),
            "duplicate_ratio": round(duplicate_ratio * 100, 2),
            "invalid_numeric_ratio": round(invalid_numeric_ratio * 100, 2),
            "data_quality_score": round(data_quality_score, 2),
        }

    def risk_alerts(self, ltv_threshold: float = 90.0, dti_threshold: float = 40.0) -> pd.DataFrame:
        """
        Flags high-risk loans for downstream dashboards and operational alerts.

        Args:
            ltv_threshold (float): LTV threshold for alerting.
            dti_threshold (float): DTI threshold for alerting.

        Returns:
            pd.DataFrame: Subset of loans exceeding thresholds with calculated risk scores.
        """
        ltv = self.compute_loan_to_value()
        dti = self.compute_debt_to_income()
        alerts = self.loan_data.copy().assign(
            ltv_ratio=ltv,
            dti_ratio=dti,
        )
        alerts = alerts[(alerts['ltv_ratio'] > ltv_threshold) | (alerts['dti_ratio'] > dti_threshold)]
        if alerts.empty:
            return alerts

        alerts['risk_score'] = (
            alerts[['ltv_ratio', 'dti_ratio']]
            .fillna(0)
            .assign(
                ltv_component=lambda d: np.clip((d['ltv_ratio'] - ltv_threshold) / 20, 0, 1),
                dti_component=lambda d: np.clip((d['dti_ratio'] - dti_threshold) / 30, 0, 1),
            )
            .pipe(lambda d: (d['ltv_component'] + d['dti_component']) / 2)
        )
        return alerts[['ltv_ratio', 'dti_ratio', 'risk_score']]

    def run_full_analysis(self) -> Dict[str, float]:
        """
        Runs a comprehensive analysis and returns a dictionary of portfolio-level KPIs.
        """
        ltv_ratio = self.compute_loan_to_value()
        dti_ratio = self.compute_debt_to_income()

        quality = self.data_quality_profile()

        return {
            "portfolio_delinquency_rate_percent": self.compute_delinquency_rate(),
            "portfolio_yield_percent": self.compute_portfolio_yield(),
            "average_ltv_ratio_percent": ltv_ratio.mean(),
            "average_dti_ratio_percent": dti_ratio.mean(),
            "data_quality_score": quality["data_quality_score"],
            "average_null_ratio_percent": quality["average_null_ratio"],
            "invalid_numeric_ratio_percent": quality["invalid_numeric_ratio"],
        }

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
