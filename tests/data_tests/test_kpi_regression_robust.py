import pandas as pd
import numpy as np
import pytest
from scipy.stats import normaltest, levene
from python.kpi_engine import calculate_par_90, calculate_collection_rate

def test_kpi_normality():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    values = df['par_90'].dropna().values
    stat, p = normaltest(values)
    assert p > 0.05, f"PAR90 values are not normally distributed (p={p})"

def test_kpi_heteroscedasticity():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    group1 = df[df['segment'] == 'Consumer']['par_90'].dropna().values
    group2 = df[df['segment'] == 'SME']['par_90'].dropna().values
    stat, p = levene(group1, group2)
    assert p > 0.05, f"Heteroscedasticity detected between Consumer and SME segments (p={p})"

def test_kpi_multicollinearity():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    corr = np.corrcoef(df['par_90'], df['collection_rate'])[0, 1]
    assert abs(corr) < 0.8, f"High multicollinearity detected (corr={corr})"
