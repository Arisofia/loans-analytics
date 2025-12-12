import pandas as pd
from scipy.stats import mannwhitneyu, chi2_contingency

SAMPLE_PATH = 'data_samples/abaco_portfolio_sample.csv'


def test_kpi_chi2_contingency():
    df = pd.read_csv(SAMPLE_PATH)
    contingency = pd.crosstab(df['segment'], df['delinquency_flag'])
    stat, p, dof, expected = chi2_contingency(contingency)
    # Just ensure computation succeeds and p-value is finite
    assert p >= 0.0


def test_kpi_mannwhitney():
    df = pd.read_csv(SAMPLE_PATH)
    consumer = df[df['segment'] == 'Consumer']['par_90']
    sme = df[df['segment'] == 'SME']['par_90']
    stat, p = mannwhitneyu(consumer, sme, alternative='two-sided')
    assert p >= 0.0
