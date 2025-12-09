"""Tests for KPI regression robustness and statistical properties."""
import pandas as pd
import numpy as np
from scipy.stats import normaltest, levene

def test_kpi_normality():
    """
    Test if the PAR90 values are normally distributed.

    This function reads the PAR90 values from the 'abaco_portfolio_sample.csv' file,
    performs a normality test using the `normaltest` function from the `scipy.stats` module,
    and asserts that the p-value is greater than 0.05.

    Returns:
        None
    """
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    values = df['par_90'].dropna().values
    _, p = normaltest(values)
    assert p > 0.05, (
        f"PAR90 values are not normally distributed (p={p})"
    )


def test_kpi_heteroscedasticity():
    """
    Test if there is heteroscedasticity between two groups.

    This function reads the PAR90 values from the 'abaco_portfolio_sample.csv' file,
    splits the data into two groups based on the 'segment' column,
    and performs a Levene's test to check for heteroscedasticity.

    Returns:
        None
    """
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    group1 = df[df['segment'] == 'Consumer']['par_90'].dropna().values
    group2 = df[df['segment'] == 'SME']['par_90'].dropna().values
    assert len(group1) >= 2, (
        f"Consumer segment missing or too small: {len(group1)} value(s) found. "
        "At least 2 required for Levene's test."
    )
    assert len(group2) >= 2, (
        f"SME segment missing or too small: {len(group2)} value(s) found. "
        "At least 2 required for Levene's test."
    )
    _, p = levene(group1, group2)
    assert p > 0.05, (
        f"Heteroscedasticity detected between Consumer and SME segments "
        f"(p={p})"
    )


def test_kpi_multicollinearity():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    # Filter out rows where either value is NaN
    clean_df = df[['par_90', 'collection_rate']].dropna()
    n = len(clean_df)
    if n < 3:
        raise AssertionError(
            f"Insufficient data for correlation: only {n} valid rows. "
            "At least 3 required."
        )
    par_90 = clean_df['par_90'].values
    collection_rate = clean_df['collection_rate'].values
    corr = np.corrcoef(par_90, collection_rate)[0, 1]
    if not np.isfinite(corr):
        raise AssertionError(
            "Correlation is undefined due to NaNs or constant values. "
            "Check input data."
        )
    assert abs(corr) < 0.8, (
        f"High multicollinearity detected (corr={corr})"
    )
