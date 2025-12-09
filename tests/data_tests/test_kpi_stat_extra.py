import pandas as pd
import pytest
from scipy.stats import mannwhitneyu, chi2_contingency

def test_kpi_mannwhitneyu():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    group1 = df[df['segment'] == 'Consumer']['par_90'].dropna().values
    group2 = df[df['segment'] == 'SME']['par_90'].dropna().values
    stat, p = mannwhitneyu(group1, group2)
    assert p > 0.05, f"Significant difference detected between Consumer and SME (p={p})"

def test_kpi_chi2_contingency():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    contingency = pd.crosstab(df['segment'], df['delinquency_flag'])
    stat, p, dof, expected = chi2_contingency(contingency)
    assert p > 0.05, f"Chi-squared test detects association between segment and delinquency (p={p})"
