"""Tests for KPI regression robustness and statistical properties."""
import pandas as pd
import numpy as np
from scipy.stats import normaltest, levene

def test_kpi_normality():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    values = df['par_90'].dropna().values
    _, p = normaltest(values)
    assert p > 0.05, (
        f"PAR90 values are not normally distributed (p={p})"
    )


def test_kpi_heteroscedasticity():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    group1 = df[df['segment'] == 'Consumer']['par_90'].dropna().values
    group2 = df[df['segment'] == 'SME']['par_90'].dropna().values
    _, p = levene(group1, group2)
    assert p > 0.05, (
        f"Heteroscedasticity detected between Consumer and SME segments "
        f"(p={p})"
    )


def test_kpi_multicollinearity():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    corr = np.corrcoef(df['par_90'], df['collection_rate'])[0, 1]
    assert abs(corr) < 0.8, (
        f"High multicollinearity detected (corr={corr})"
    )
