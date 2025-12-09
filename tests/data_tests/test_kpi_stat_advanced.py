import pandas as pd
import numpy as np
import pytest
from scipy.stats import shapiro, bartlett, durbin_watson
from statsmodels.stats.outliers_influence import variance_inflation_factor
from python.kpi_engine import calculate_par_90, calculate_collection_rate

def test_kpi_shapiro_normality():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    values = df['par_90'].dropna().values
    stat, p = shapiro(values)
    assert p > 0.05, f"PAR90 values fail Shapiro-Wilk normality (p={p})"

def test_kpi_bartlett_homoscedasticity():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    group1 = df[df['segment'] == 'Consumer']['par_90'].dropna().values
    group2 = df[df['segment'] == 'SME']['par_90'].dropna().values
    stat, p = bartlett(group1, group2)
    assert p > 0.05, f"Bartlett test detects heteroscedasticity (p={p})"

def test_kpi_durbin_watson_autocorrelation():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    stat = durbin_watson(df['par_90'].dropna().values)
    assert 1.5 < stat < 2.5, f"Durbin-Watson statistic out of range (stat={stat})"

def test_kpi_vif_multicollinearity():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    X = df[['par_90', 'collection_rate']].dropna().values
    vif = [variance_inflation_factor(X, i) for i in range(X.shape[1])]
    for v in vif:
        assert v < 5, f"High VIF detected (VIF={v})"
