import pandas as pd
import numpy as np
from typing import Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class KPIExporter(Protocol):
    def upload_metrics(self, metrics: Dict[str, float], blob_name: Optional[str] = None) -> str:
        ...

class LoanAnalyticsEngine:
    """
    A robust engine for computing critical KPIs for a loan portfolio.
    This system is designed for scalability and provides traceable, actionable insights
    to drive financial intelligence and commercial growth.
    """

    NUMERIC_COLUMNS = [
        "loan_amount",
        "appraised_value",
        "borrower_income",
        "monthly_debt",
        "interest_rate",
        "principal_balance",
    ]

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
        # Track coercion report: count of invalid entries per numeric column
        self._coercion_report = {}
        coerced, coercion_report = self._coerce_numeric_columns_with_report(self.loan_data)
        self.loan_data = coerced
        self._coercion_report = coercion_report
        self._invalid_numeric_ratio = self._compute_invalid_numeric_ratio(loan_data, self.loan_data)

    @property
    def coercion_report(self) -> dict:
        """Public property exposing the coercion report (invalid entries per numeric column)."""
        return self._coercion_report

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

    def _coerce_numeric_columns_with_report(self, frame: pd.DataFrame):
        coerced = frame.copy()
        report = {}
        for column in self.NUMERIC_COLUMNS:
            orig = coerced[column]
            coerced[column] = pd.to_numeric(orig, errors="coerce")
            # Count how many values were coerced to NaN that were not NaN originally
            report[column] = int(((coerced[column].isna()) & (pd.Series(orig).notna())).sum())
        return coerced, report

    def _compute_invalid_numeric_ratio(
        self, original: pd.DataFrame, coerced: pd.DataFrame
    ) -> float:
        if coerced.empty:
            return 0.0

        invalid_count = 0
        total = 0

        for column in self.NUMERIC_COLUMNS:
            orig_series = original[column]
            coerced_series = coerced[column]
            converted_invalid = coerced_series.isna() & orig_series.notna()
            invalid_count += converted_invalid.sum()
            total += len(orig_series)

        return invalid_count / total if total else 0.0

    def compute_loan_to_value(self) -> pd.Series:
        """Computes the Loan-to-Value (LTV) ratio for each loan."""
        ltv = pd.Series(dtype=float, index=self.loan_data.index)

        denominator = self.loan_data['appraised_value']
        numerator = self.loan_data['loan_amount']
        valid_mask = denominator > 0

        ltv.loc[valid_mask] = (numerator[valid_mask] / denominator[valid_mask]) * 100
        ltv.loc[~valid_mask] = np.nan
        return ltv

    def compute_debt_to_income(self) -> pd.Series:
        """Computes the Debt-to-Income (DTI) ratio for each borrower.

        This method assumes that the ``borrower_income`` field in ``self.loan_data``
        represents an annual income amount, which is converted to a monthly value
        internally by dividing by 12 before computing the DTI.
        """
        # Assuming borrower_income is annual, convert to monthly
        monthly_income = self.loan_data['borrower_income'] / 12
        # Avoid division by zero
        dti = pd.Series(np.nan, index=self.loan_data.index, dtype=float)
        valid_mask = monthly_income > 0
        dti.loc[valid_mask] = (self.loan_data.loc[valid_mask, 'monthly_debt'] / monthly_income[valid_mask]) * 100
        return dti

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
        null_ratio = float(self.loan_data.isna().mean().mean()) if not self.loan_data.empty else 0.0
        invalid_numeric_ratio = float(self._invalid_numeric_ratio)
        # Duplicate ratio: number of duplicate rows / total rows
        duplicate_count = int(self.loan_data.duplicated().sum())
        total_rows = len(self.loan_data)
        duplicate_ratio = (duplicate_count / total_rows) if total_rows > 0 else 0.0
        # Average of the issue ratios (nulls, invalid numerics, duplicates)
        average_issue_ratio = (null_ratio + invalid_numeric_ratio + duplicate_ratio) / 3
        # Convert to a quality score where 1.0 means perfect quality
        raw_quality_score = 1 - average_issue_ratio
        # The clamping is redundant as raw_quality_score is already in [0, 1].
        # Express as a percentage in [0.0, 100.0].
        quality_score = raw_quality_score * 100

        return {
            "average_null_ratio": null_ratio,
            "invalid_numeric_ratio": invalid_numeric_ratio,
            "duplicate_ratio": duplicate_ratio,
            "data_quality_score": quality_score,
        }

    def risk_alerts(self, ltv_threshold: float = 85.0, dti_threshold: float = 36.0) -> pd.DataFrame:
        ltv = self.compute_loan_to_value()
        dti = self.compute_debt_to_income()

        alerts = pd.DataFrame(
            {
                "ltv_ratio": ltv,
                "dti_ratio": dti,
            },
            index=self.loan_data.index,
        )

        ltv_component = np.nan_to_num(ltv / max(ltv_threshold, 1), nan=0.0)
        dti_component = np.nan_to_num(dti / max(dti_threshold, 1), nan=0.0)
        alerts["risk_score"] = (0.5 * ltv_component) + (0.5 * dti_component)
        alerts["risk_score"] = alerts["risk_score"].clip(upper=1.0)

        return alerts[(alerts["ltv_ratio"] > ltv_threshold) | (alerts["dti_ratio"] > dti_threshold)]

    def run_full_analysis(self) -> Dict[str, float]:
        """
        Runs a comprehensive analysis and returns a dictionary of portfolio-level KPIs.
        """
        analysis_frame = self.loan_data.copy()
        analysis_frame['ltv_ratio'] = self.compute_loan_to_value()
        analysis_frame['dti_ratio'] = self.compute_debt_to_income()
        quality = self.data_quality_profile()

        return {
            "portfolio_delinquency_rate_percent": self.compute_delinquency_rate(),
            "portfolio_yield_percent": self.compute_portfolio_yield(),
            "average_ltv_ratio_percent": analysis_frame['ltv_ratio'].mean(),
            "average_dti_ratio_percent": analysis_frame['dti_ratio'].mean(),
            "data_quality_score": quality["data_quality_score"],
            "average_null_ratio_percent": quality["average_null_ratio"] * 100,
            "invalid_numeric_ratio_percent": quality["invalid_numeric_ratio"] * 100,
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
