"""Utility functions for common loan analytics KPIs."""

import logging
from typing import Dict, Iterable

import numpy as np
import pandas as pd

from python.validation import (
    ANALYTICS_NUMERIC_COLUMNS,
    REQUIRED_ANALYTICS_COLUMNS,
    safe_numeric,
    validate_dataframe,
)

# Alias for backward compatibility and clarity within this module
REQUIRED_KPI_COLUMNS = REQUIRED_ANALYTICS_COLUMNS

DELINQUENT_STATUSES = ["30-59 days past due", "60-89 days past due", "90+ days past due"]


def _coerce_numeric(series: pd.Series, field_name: str) -> pd.Series:
    """
    Convert a series to numeric values, preserving NaNs for validation
    visibility.

    Args:
        series (pd.Series): The input series to convert.
        field_name (str): The name of the field for error reporting.

    Returns:
        pd.Series: Numeric series with NaNs for invalid values.
    Raises:
        ValueError: If all values are non-numeric.
    """

    numeric = safe_numeric(series)
    if numeric.isna().all() and not series.empty:
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

    # Use centralized validation for structure and types
    validate_dataframe(
        loan_data, required_columns=REQUIRED_KPI_COLUMNS, numeric_columns=ANALYTICS_NUMERIC_COLUMNS
    )

    errors = []
    # Granular checks: NaN, data types, value ranges
    for col in REQUIRED_KPI_COLUMNS:
        if col in loan_data.columns:
            series = loan_data[col]
            if series.isna().any():
                msg = f"Column '{col}' contains NaN values."
                logging.error(msg)
                errors.append(msg)
            if col in ANALYTICS_NUMERIC_COLUMNS:
                # Value range checks (example: no negative values for amounts)
                if (series < 0).any():
                    msg = f"Column '{col}' contains negative values."
                    logging.error(msg)
                    errors.append(msg)

    if errors:
        # Optionally, raise a single error with all issues for monitoring systems
        raise ValueError("; ".join(errors))


def loan_to_value(loan_amounts: pd.Series, appraised_values: pd.Series) -> pd.Series:
    """
    Compute loan-to-value (LTV) ratio as a percentage, avoiding division by
    zero.

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
    Compute debt-to-income (DTI) ratio as a percentage, using monthly income
    and safeguarding against zero income.

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
    Calculate weighted portfolio yield, returning zero when principal is
    missing or zero.

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


def _data_quality_metrics(loan_data: pd.DataFrame) -> Dict[str, float]:
    """Build lightweight data quality KPIs used by dashboards."""
    null_ratio = float(loan_data.isna().mean().mean())
    duplicate_ratio = float(loan_data.duplicated().mean())

    numeric_columns = [col for col in ANALYTICS_NUMERIC_COLUMNS if col in loan_data.columns]
    total_numeric_cells = len(loan_data) * len(numeric_columns)
    invalid_numeric_count = 0
    for col in numeric_columns:
        coerced = safe_numeric(loan_data[col])
        invalid_numeric_count += max(0, coerced.isna().sum() - loan_data[col].isna().sum())

    invalid_numeric_ratio = (
        invalid_numeric_count / total_numeric_cells if total_numeric_cells > 0 else 0.0
    )
    data_quality_score = max(0.0, 100 - (null_ratio * 100) - (duplicate_ratio * 50))

    return {
        "data_quality_score": round(data_quality_score, 2),
        "average_null_ratio_percent": round(null_ratio * 100, 2),
        "invalid_numeric_ratio_percent": round(invalid_numeric_ratio * 100, 2),
    }


def portfolio_kpis(loan_data: pd.DataFrame) -> Dict[str, float]:
    """Aggregate portfolio KPIs used across analytics modules."""
    sanitized_data = loan_data.copy()
    for col in ANALYTICS_NUMERIC_COLUMNS:
        if col in sanitized_data.columns:
            sanitized_data[col] = safe_numeric(sanitized_data[col])

    validate_kpi_columns(sanitized_data)

    ltv_series = (
        _coerce_numeric(sanitized_data["ltv_ratio"], "ltv_ratio")
        if "ltv_ratio" in sanitized_data.columns
        else loan_to_value(sanitized_data["loan_amount"], sanitized_data["appraised_value"])
    )
    dti_series = (
        _coerce_numeric(sanitized_data["dti_ratio"], "dti_ratio")
        if "dti_ratio" in sanitized_data.columns
        else debt_to_income_ratio(sanitized_data["monthly_debt"], sanitized_data["borrower_income"])
    )

    avg_ltv = ltv_series.mean(skipna=True)
    avg_dti = dti_series.mean(skipna=True)

    kpis = {
        "portfolio_delinquency_rate_percent": portfolio_delinquency_rate(
            sanitized_data["loan_status"]
        ),
        "portfolio_yield_percent": weighted_portfolio_yield(
            sanitized_data["interest_rate"], sanitized_data["principal_balance"]
        ),
        "average_ltv_ratio_percent": float(avg_ltv if not np.isnan(avg_ltv) else 0.0),
        "average_dti_ratio_percent": float(avg_dti if not np.isnan(avg_dti) else 0.0),
    }

    kpis.update(_data_quality_metrics(sanitized_data))
    return kpis
