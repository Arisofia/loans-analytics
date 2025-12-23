"""
Enterprise Analytics Engine for loan portfolio KPI computation and risk analysis.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Protocol, runtime_checkable

import numpy as np
import pandas as pd

from python.validation import (
    REQUIRED_ANALYTICS_COLUMNS,
    ANALYTICS_NUMERIC_COLUMNS,
    validate_dataframe,
)

logger = logging.getLogger(__name__)


@runtime_checkable
class KPIExporter(Protocol):
    """Protocol for exporting KPI payloads."""

    def upload_metrics(self, metrics: Dict[str, float], blob_name: Optional[str] = None) -> str:
        """Upload computed KPI metrics and return a blob identifier."""
        raise NotImplementedError("KPIExporter must implement upload_metrics")


class LoanAnalyticsEngine:
    """Robust engine for computing KPI metrics with auditability, validation, and alerts."""

    @property
    def coercion_report(self) -> Dict[str, int]:
        """Report of invalid numeric coercions by column."""
        return self._coercion_report

    def __init__(self, loan_data: pd.DataFrame):
        """Initialize the engine with loan portfolio data."""
        if not isinstance(loan_data, pd.DataFrame) or loan_data.empty:
            raise ValueError("Input loan_data must be a non-empty pandas DataFrame.")

        self.loan_data = loan_data.copy()
        self._validate_columns()
        self._coercion_report = self._coerce_numeric_columns()
        self._check_data_sanity()

    def get_engine_info(self) -> str:
        """Short description for audit and traceability logs."""
        return (
            "LoanAnalyticsEngine: Computes KPIs for loan portfolios, "
            "designed for scalability, auditability, and actionable financial intelligence."
        )

    @classmethod
    def from_dict(cls, input_data: Dict[str, list]) -> "LoanAnalyticsEngine":
        """Alternate constructor from a dictionary payload."""
        return cls(pd.DataFrame(input_data))

    def _validate_columns(self) -> None:
        """Ensures the DataFrame contains the required analytics columns."""
        validate_dataframe(
            self.loan_data,
            required_columns=REQUIRED_ANALYTICS_COLUMNS,
        )

    def _coerce_numeric_columns(self) -> Dict[str, int]:
        """Coerce numeric columns and report values that turn into NaN."""
        numeric_cols: List[str] = [
            col for col in ANALYTICS_NUMERIC_COLUMNS if col in self.loan_data.columns
        ]
        coercion_report: Dict[str, int] = {}
        for col in numeric_cols:
            original = self.loan_data[col]
            coerced = pd.to_numeric(original, errors="coerce")
            invalid_count = int(coerced.isna().sum() - original.isna().sum())
            coercion_report[col] = max(invalid_count, 0)
            self.loan_data[col] = coerced

        return coercion_report

    def _check_data_sanity(self) -> None:
        """Heuristic checks on data values to flag potential issues."""
        if "interest_rate" in self.loan_data.columns:
            max_rate = self.loan_data["interest_rate"].max()
            if max_rate > 1.0:
                logger.warning(
                    "Max interest_rate is %s. Ensure rates are ratios (e.g., 0.05 for 5%%).",
                    max_rate,
                )

    def compute_loan_to_value(self) -> pd.Series:
        """Compute Loan-to-Value ratio as a percentage while avoiding division by zero."""
        appraised_value = self.loan_data["appraised_value"].replace(0, np.nan)
        ltv = (self.loan_data["loan_amount"] / appraised_value) * 100
        return ltv.replace([np.inf, -np.inf], np.nan)

    def compute_debt_to_income(self) -> pd.Series:
        """Compute Debt-to-Income ratio as a percentage for each borrower."""
        monthly_income = self.loan_data["borrower_income"] / 12
        positive_income = monthly_income > 0
        dti = np.where(
            positive_income,
            (self.loan_data["monthly_debt"] / monthly_income) * 100,
            np.nan,
        )
        return pd.Series(dti, index=self.loan_data.index)

    def compute_delinquency_rate(self) -> float:
        """Compute delinquency rate as a percentage of loans in arrears."""
        delinquent_statuses = [
            "30-59 days past due",
            "60-89 days past due",
            "90+ days past due",
        ]
        delinquent_count = self.loan_data["loan_status"].isin(delinquent_statuses).sum()
        total_loans = len(self.loan_data)
        return (delinquent_count / total_loans) * 100 if total_loans > 0 else 0.0

    def compute_portfolio_yield(self) -> float:
        """Compute weighted average portfolio yield."""
        total_principal = self.loan_data["principal_balance"].sum()
        if total_principal == 0:
            return 0.0

        weighted_interest = (
            self.loan_data["interest_rate"] * self.loan_data["principal_balance"]
        ).sum()
        return (weighted_interest / total_principal) * 100

    def data_quality_profile(self) -> Dict[str, float]:
        """Generate a lightweight data quality profile for audit and reporting."""
        row_count = len(self.loan_data)
        null_ratio = float(self.loan_data.isna().mean().mean())
        duplicate_ratio = float(self.loan_data.duplicated().mean())

        numeric_cols = [
            col for col in ANALYTICS_NUMERIC_COLUMNS if col in self.loan_data.columns
        ]
        total_numeric_cells = row_count * len(numeric_cols) if row_count and numeric_cols else 0
        invalid_numeric_count = sum(
            self._coercion_report.get(col, 0) for col in numeric_cols
        )
        invalid_numeric_ratio = (
            invalid_numeric_count / total_numeric_cells if total_numeric_cells > 0 else 0.0
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

    def risk_alerts(
        self, ltv_threshold: float = 90.0, dti_threshold: float = 40.0
    ) -> pd.DataFrame:
        """Flag high-risk loans using LTV and DTI thresholds."""
        ltv = self.compute_loan_to_value()
        dti = self.compute_debt_to_income()
        alerts = self.loan_data.copy().assign(ltv_ratio=ltv, dti_ratio=dti)
        alerts = alerts[
            (alerts["ltv_ratio"] > ltv_threshold)
            | (alerts["dti_ratio"] > dti_threshold)
        ]
        if alerts.empty:
            return alerts

        alerts = alerts.copy()
        alerts["ltv_component"] = np.clip((alerts["ltv_ratio"] - ltv_threshold) / 20, 0, 1)
        alerts["dti_component"] = np.clip((alerts["dti_ratio"] - dti_threshold) / 30, 0, 1)
        ltv_valid = alerts["ltv_component"].notna()
        dti_valid = alerts["dti_component"].notna()
        alerts["risk_score"] = np.where(
            ltv_valid & dti_valid,
            0.6 * alerts["ltv_component"] + 0.4 * alerts["dti_component"],
            np.where(
                ltv_valid,
                alerts["ltv_component"],
                np.where(dti_valid, alerts["dti_component"], 0.0),
            ),
        )
        return alerts[["ltv_ratio", "dti_ratio", "risk_score"]]

    def run_full_analysis(self) -> Dict[str, float]:
        """Run comprehensive KPI computation for the portfolio."""
        ltv_ratio = self.compute_loan_to_value()
        dti_ratio = self.compute_debt_to_income()
        quality = self.data_quality_profile()

        return {
            "portfolio_delinquency_rate_percent": self.compute_delinquency_rate(),
            "portfolio_yield_percent": self.compute_portfolio_yield(),
            "average_ltv_ratio_percent": float(ltv_ratio.mean(skipna=True)),
            "average_dti_ratio_percent": float(dti_ratio.mean(skipna=True)),
            "data_quality_score": quality["data_quality_score"],
            "average_null_ratio_percent": quality["average_null_ratio"],
            "invalid_numeric_ratio_percent": quality["invalid_numeric_ratio"],
        }

    def export_kpis_to_blob(
        self, exporter: KPIExporter, blob_name: Optional[str] = None
    ) -> str:
        """Export KPI metrics using the provided exporter."""
        if blob_name is not None and not isinstance(blob_name, str):
            raise ValueError("blob_name must be a string if provided.")

        kpis = self.run_full_analysis()
        return exporter.upload_metrics(kpis, blob_name=blob_name)

    def get_validation_errors(self) -> List[dict]:
        """Run CascadeIngestion validation checks and return any errors."""
        try:
            from python.ingestion import CascadeIngestion
        except ImportError:
            return []

        ci = CascadeIngestion()
        ci.errors.clear()
        ci.validate_loans(self.loan_data)
        return ci.errors


if __name__ == "__main__":
    sample = {
        "loan_amount": [250000, 450000, 150000, 600000],
        "appraised_value": [300000, 500000, 160000, 750000],
        "borrower_income": [80000, 120000, 60000, 150000],
        "monthly_debt": [1500, 2500, 1000, 3000],
        "loan_status": [
            "current",
            "30-59 days past due",
            "current",
            "current",
        ],
        "interest_rate": [0.035, 0.042, 0.038, 0.045],
        "principal_balance": [240000, 440000, 145000, 590000],
    }

    engine = LoanAnalyticsEngine(pd.DataFrame(sample))
    kpi_dashboard = engine.run_full_analysis()

    print("--- Loan Portfolio KPI Dashboard ---")
    for kpi, value in kpi_dashboard.items():
        print(f"{kpi.replace('_', ' ').title()}: {value:.2f}")
    print("------------------------------------")
