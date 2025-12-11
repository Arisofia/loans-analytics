"""
Enterprise Analytics Engine for loan portfolio KPI computation and
risk analysis.
"""

from typing import Dict, List, Optional, Protocol, runtime_checkable
import numpy as np
import pandas as pd


@runtime_checkable
class KPIExporter(Protocol):
    """
    Interface/Protocol defining required methods for exporting KPI data.
    Implementations should provide methods such as export_kpis, serialize, and close
    to handle the transfer, serialization, and finalization of KPI metric outputs to external systems
    (e.g., cloud storage, files, APIs). This does not perform analytics computation.
    """
    def upload_metrics(
        self,
        metrics: Dict[str, float],
        blob_name: Optional[str] = None
    ) -> str:
        """
        Upload KPI metrics to a remote storage location
        (e.g., Azure Blob Storage).

        Args:
            metrics (Dict[str, float]):
                Dictionary of KPI metric names and their float values.
            blob_name (Optional[str]):
                Optional name for the blob or file to store the metrics.

        Returns:
            str: The URI or path of the uploaded metrics blob.
        """
        raise NotImplementedError("KPIExporter must implement upload_metrics")


class LoanAnalyticsEngine:
    """
    A robust engine for computing critical KPIs for a loan portfolio.
    This system is designed for scalability and provides traceable,
    actionable insights to drive financial intelligence and commercial growth.
    """

    @property
    def coercion_report(self):
        """
        Returns the coercion report for numeric columns.
        """
        return self._coercion_report

    def __init__(self, loan_data: pd.DataFrame):
        """
        Initialize the LoanAnalyticsEngine with loan data.

        Args:
            loan_data (pd.DataFrame):
                DataFrame containing loan records. Expected columns:
                'loan_amount', 'appraised_value', 'borrower_income',
                'monthly_debt', 'loan_status', 'interest_rate',
                'principal_balance'.
        """
        if not isinstance(loan_data, pd.DataFrame) or loan_data.empty:
            raise ValueError(
                "Input loan_data must be a non-empty pandas DataFrame."
            )
        self.loan_data = loan_data.copy()
        self._validate_columns()
        self._coercion_report = self._coerce_numeric_columns()

    def get_engine_info(self) -> str:
        """
        Returns a brief description of the LoanAnalyticsEngine for audit and
        traceability.
        """
        return (
            "LoanAnalyticsEngine: Computes KPIs for loan portfolios, "
            "designed for scalability, auditability, and actionable "
            "financial intelligence."
        )

    @classmethod
    def from_dict(cls, input_data: Dict[str, list]) -> "LoanAnalyticsEngine":
        """
        Alternate constructor to create an engine from a dictionary.

        Args:
            input_data (Dict[str, list]):
                Dictionary of column names to lists of values.

        Returns:
            LoanAnalyticsEngine: An instance of the analytics engine.
        """
        return cls(pd.DataFrame(input_data))

    def _validate_columns(self):
        # Ensures the DataFrame contains the necessary columns
        # for KPI computation.
        """
        Ensures the DataFrame contains the necessary columns for KPI
        computation.
        """
        required_cols = [
            'loan_amount', 'appraised_value', 'borrower_income',
            'monthly_debt', 'loan_status', 'interest_rate', 'principal_balance'
        ]
        missing_cols = [
            col for col in required_cols if col not in self.loan_data.columns
        ]
        if missing_cols:
            raise ValueError(
                f"Missing required columns in loan_data: "
                f"{', '.join(missing_cols)}"
            )

    def _coerce_numeric_columns(self) -> Dict[str, int]:
        # Convert numeric columns to proper dtypes and record
        # invalid values for auditability.

        # Returns a report of invalid values coerced to NaN for each column.
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
        """
        Compute the Loan-to-Value (LTV) ratio for each loan.
        Avoids division by zero.
        """
        appraised_value = self.loan_data['appraised_value'].replace(0, np.nan)
        ltv = (self.loan_data['loan_amount'] / appraised_value) * 100
        return ltv.replace([np.inf, -np.inf], np.nan)

    def compute_debt_to_income(self) -> pd.Series:
        """
        Computes the Debt-to-Income (DTI) ratio for each borrower.
        """
        # Computes the Debt-to-Income (DTI) ratio for each borrower.
        monthly_income = self.loan_data['borrower_income'] / 12
        positive_income = monthly_income > 0
        dti = np.where(
            positive_income,
            (self.loan_data['monthly_debt'] / monthly_income) * 100,
            np.nan
        )
        return pd.Series(dti, index=self.loan_data.index)

    def compute_delinquency_rate(self) -> float:
        """
        Computes the overall portfolio delinquency rate.

        Returns:
            float: The delinquency rate as a percentage.
        """
        # Computes the overall portfolio delinquency rate.
        delinquent_statuses = [
            '30-59 days past due',
            '60-89 days past due',
            '90+ days past due',
        ]
        delinquent_count = self.loan_data['loan_status'].isin(
            delinquent_statuses
        ).sum()
        total_loans = len(self.loan_data)
        return (
            (delinquent_count / total_loans) * 100 if total_loans > 0 else 0.0
        )

    def compute_portfolio_yield(self) -> float:
        """
        Compute the weighted average portfolio yield for the loan portfolio.
        """
        total_principal = self.loan_data['principal_balance'].sum()
        if total_principal == 0:
            return 0.0

        weighted_interest = (
            self.loan_data['interest_rate'] *
            self.loan_data['principal_balance']
        ).sum()
        return (weighted_interest / total_principal) * 100

    def data_quality_profile(self) -> Dict[str, float]:
        """
        Generate a lightweight data quality profile for auditability and traceability.
        """
        null_ratio = float(self.loan_data.isna().mean().mean())
        duplicate_ratio = float(self.loan_data.duplicated().mean())
        total_numeric_cells = (
            len(self.loan_data) * len(self._coercion_report)
            if len(self.loan_data) > 0 else 0
        )
        invalid_numeric_ratio = (
            sum(self._coercion_report.values()) / total_numeric_cells
            if total_numeric_cells > 0 else 0.0
        )
        data_quality_score = max(
            0.0,
            100 - (null_ratio * 100) - (duplicate_ratio * 50)
        )
        return {
            "average_null_ratio": round(null_ratio * 100, 2),
            "duplicate_ratio": round(duplicate_ratio * 100, 2),
            "invalid_numeric_ratio": round(invalid_numeric_ratio * 100, 2),
            "data_quality_score": round(data_quality_score, 2),
        }

    def risk_alerts(
        self,
        ltv_threshold: float = 90.0,
        dti_threshold: float = 40.0
    ) -> pd.DataFrame:
        """
        Flags high-risk loans for downstream dashboards and operational alerts.

        Args:
            ltv_threshold (float, optional):
                The LTV threshold for flagging loans. Defaults to 90.0.
            dti_threshold (float, optional):
                The DTI threshold for flagging loans. Defaults to 40.0.

        Returns:
            pd.DataFrame: A DataFrame containing flagged loans.
        """
        # Flags high-risk loans for downstream dashboards and
        # operational alerts.
        ltv = self.compute_loan_to_value()
        dti = self.compute_debt_to_income()
        alerts = self.loan_data.copy().assign(
            ltv_ratio=ltv,
            dti_ratio=dti,
        )
        alerts = alerts[
            (alerts['ltv_ratio'] > ltv_threshold)
            | (alerts['dti_ratio'] > dti_threshold)
        ]
        if alerts.empty:
            return alerts

        alerts = alerts.copy()
        alerts['ltv_component'] = np.clip(
            (alerts['ltv_ratio'] - ltv_threshold) / 20, 0, 1
        )
        alerts['dti_component'] = np.clip(
            (alerts['dti_ratio'] - dti_threshold) / 30, 0, 1
        )
        # Compute risk_score using available components with adjusted weights
        ltv_valid = alerts['ltv_component'].notna()
        dti_valid = alerts['dti_component'].notna()
        # Use only available components, normalizing weights
        alerts['risk_score'] = np.where(
            ltv_valid & dti_valid,
            0.6 * alerts['ltv_component'] + 0.4 * alerts['dti_component'],
            np.where(
                ltv_valid,
                alerts['ltv_component'],
                np.where(dti_valid, alerts['dti_component'], 0.0)
            )
        )
        return alerts[['ltv_ratio', 'dti_ratio', 'risk_score']]

    def run_full_analysis(self) -> Dict[str, float]:
        # Runs a comprehensive analysis and returns a dictionary
        # of portfolio-level KPIs.
        """
        Runs a comprehensive analysis and returns a dictionary of
        portfolio-level KPIs.
        """
        ltv_ratio = self.compute_loan_to_value()
        dti_ratio = self.compute_debt_to_income()

        quality = self.data_quality_profile()

        return {
            "portfolio_delinquency_rate_percent": (
                self.compute_delinquency_rate()
            ),
            "portfolio_yield_percent": self.compute_portfolio_yield(),
            "average_ltv_ratio_percent": ltv_ratio.mean(),
            "average_dti_ratio_percent": dti_ratio.mean(),
            "data_quality_score": quality["data_quality_score"],
            "average_null_ratio_percent": quality["average_null_ratio"],
            "invalid_numeric_ratio_percent": quality["invalid_numeric_ratio"],
        }

    def export_kpis_to_blob(
        self,
        exporter: KPIExporter,
        blob_name: Optional[str] = None
    ) -> str:
        """
        Exports KPIs to a remote blob using the provided exporter.
        """
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
        'loan_status': [
            'current', '30-59 days past due', 'current', 'current'
        ],
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
