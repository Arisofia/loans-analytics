"""Utility functions for common loan analytics KPIs."""
from typing import Dict, Iterable

import numpy as np
import pandas as pd

REQUIRED_KPI_COLUMNS = [
    "loan_amount",
    "appraised_value",
    "borrower_income",
    "monthly_debt",
    "loan_status",
    "interest_rate",
    "principal_balance",
]

DELINQUENT_STATUSES = ["30-59 days past due", "60-89 days past due", "90+ days past due"]

def _coerce_numeric(series: pd.Series, field_name: str) -> pd.Series:
    """
    Convert a series to numeric values, preserving NaNs for validation visibility.

    Args:
        series (pd.Series): The input series to convert.
        field_name (str): The name of the field for error reporting.

    Returns:
        pd.Series: Numeric series with NaNs for invalid values.
    Raises:
        ValueError: If all values are non-numeric.
    """

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().all():
        raise ValueError(f"Field '{field_name}' must contain at least one numeric value")
    return numeric


def validate_kpi_columns(loan_data: pd.DataFrame) -> None:
    """
    Validate that all KPI columns exist in the provided dataframe.

    Args:
        loan_data (pd.DataFrame): The loan data to validate.

    Raises:
        ValueError: If the DataFrame is empty or required columns are missing.
    """

    if loan_data.empty:
        raise ValueError("Input loan_data must be a non-empty DataFrame.")

    missing_cols = [col for col in REQUIRED_KPI_COLUMNS if col not in loan_data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in loan_data: {', '.join(missing_cols)}")


def loan_to_value(loan_amounts: pd.Series, appraised_values: pd.Series) -> pd.Series:
    """
    Compute loan-to-value (LTV) ratio as a percentage, avoiding division by zero.

    Args:
        loan_amounts (pd.Series): Series of loan amounts.
        appraised_values (pd.Series): Series of appraised property values.

    Returns:
        pd.Series: LTV ratios as percentages.
    """

    sanitized_amounts = _coerce_numeric(loan_amounts, "loan_amount")
    sanitized_appraised = _coerce_numeric(appraised_values, "appraised_value")
    safe_appraised = sanitized_appraised.replace(0, np.nan)
    return (sanitized_amounts / safe_appraised) * 100


def debt_to_income_ratio(monthly_debts: pd.Series, borrower_incomes: pd.Series) -> pd.Series:
    """
    Compute debt-to-income (DTI) ratio as a percentage, using monthly income and safeguarding against zero income.

    Args:
        monthly_debts (pd.Series): Series of monthly debt payments.
        borrower_incomes (pd.Series): Series of borrower annual incomes.

    Returns:
        pd.Series: DTI ratios as percentages.
    """

    sanitized_debt = _coerce_numeric(monthly_debts, "monthly_debt")
    monthly_income = _coerce_numeric(borrower_incomes, "borrower_income") / 12
    safe_income = monthly_income.replace({0: np.nan})
    return (sanitized_debt / safe_income) * 100


def portfolio_delinquency_rate(statuses: Iterable[str]) -> float:
    """
    Calculate the delinquency rate as a percentage of total loans.

    Args:
        statuses (Iterable[str]): Iterable of loan status strings.

    Returns:
        float: Delinquency rate percentage.
    """
    series = pd.Series(list(statuses))
    delinquent_count = series.isin(DELINQUENT_STATUSES).sum()
    total = len(series)
    return (delinquent_count / total) * 100 if total else 0.0


def weighted_portfolio_yield(interest_rates: pd.Series, principal_balances: pd.Series) -> float:
    """
    Calculate weighted portfolio yield, returning zero when principal is missing or zero.

    Args:
        interest_rates (pd.Series): Series of interest rates.
        principal_balances (pd.Series): Series of principal balances.

    Returns:
        float: Weighted yield percentage.
    """

    sanitized_principal = _coerce_numeric(principal_balances, "principal_balance").fillna(0)
    total_principal = sanitized_principal.sum()
    if total_principal == 0:
        return 0.0

    sanitized_interest = _coerce_numeric(interest_rates, "interest_rate").fillna(0)
    weighted_interest = (sanitized_interest * sanitized_principal).sum()
    return (weighted_interest / total_principal) * 100


def portfolio_kpis(loan_data: pd.DataFrame) -> Dict[str, float]:
    """Aggregate portfolio KPIs used across analytics modules."""
    validate_kpi_columns(loan_data)

    ltv_series = (
        _coerce_numeric(loan_data["ltv_ratio"], "ltv_ratio")
        if "ltv_ratio" in loan_data.columns
        else loan_to_value(loan_data["loan_amount"], loan_data["appraised_value"])
    )
    dti_series = (
        _coerce_numeric(loan_data["dti_ratio"], "dti_ratio")
        if "dti_ratio" in loan_data.columns
        else debt_to_income_ratio(loan_data["monthly_debt"], loan_data["borrower_income"])
    )

    avg_ltv = ltv_series.mean(skipna=True)
    avg_dti = dti_series.mean(skipna=True)

    return {
        "portfolio_delinquency_rate_percent": portfolio_delinquency_rate(
            loan_data["loan_status"]
        ),
        "portfolio_yield_percent": weighted_portfolio_yield(
            loan_data["interest_rate"], loan_data["principal_balance"]
        ),
        "average_ltv_ratio_percent": float(avg_ltv if not np.isnan(avg_ltv) else 0.0),
        "average_dti_ratio_percent": float(avg_dti if not np.isnan(avg_dti) else 0.0),
    }
