from __future__ import annotations
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from backend.python.config.mype_rules import MYPEBusinessRules

def standardize_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors='coerce').astype(float)
    cleaned = series.astype('string').str.strip().replace({'': pd.NA, 'nan': pd.NA, 'None': pd.NA, '<NA>': pd.NA}).str.replace(',', '', regex=False).str.replace('[$€£¥₽%]', '', regex=True).str.replace('\\s+', '', regex=True).str.replace('[^0-9\\-.]', '', regex=True)
    return pd.to_numeric(cleaned, errors='coerce').astype(float)

def calculate_quality_score(df: pd.DataFrame) -> float:
    if df.empty or len(df.columns) == 0:
        return 0.0
    total_cells = int(df.shape[0] * df.shape[1])
    if total_cells == 0:
        return 0.0
    non_null_cells = int(df.notna().sum().sum())
    if non_null_cells == 0:
        return 0.0
    return round(non_null_cells / total_cells * 100, 1)

def portfolio_kpis(df: pd.DataFrame) -> tuple[dict[str, float], pd.DataFrame]:
    required = ['loan_amount', 'appraised_value', 'borrower_income', 'monthly_debt', 'principal_balance', 'interest_rate', 'loan_status']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if df.empty:
        return ({'delinquency_rate': 0.0, 'portfolio_yield': 0.0, 'average_ltv': 0.0, 'average_dti': 0.0}, df.copy())
    enriched = df.copy()
    for col in ['loan_amount', 'appraised_value', 'borrower_income', 'monthly_debt', 'principal_balance', 'interest_rate']:
        enriched[col] = standardize_numeric(enriched[col])
    with np.errstate(divide='ignore', invalid='ignore'):
        enriched['ltv_ratio'] = enriched['loan_amount'] / enriched['appraised_value'].replace(0, np.nan)
    income_positive = enriched['borrower_income'] > 0
    enriched['dti_ratio'] = np.nan
    enriched.loc[income_positive, 'dti_ratio'] = enriched.loc[income_positive, 'monthly_debt'] / (enriched.loc[income_positive, 'borrower_income'] / 12.0)
    principal_series = enriched['principal_balance'].dropna()
    principal_sum = float(principal_series.sum())
    delinquent_mask = enriched['loan_status'].astype(str).str.lower().eq('delinquent')
    delinquent_principal = float(enriched.loc[delinquent_mask, 'principal_balance'].dropna().sum())
    delinquency_rate = delinquent_principal / principal_sum if principal_sum > 0 else 0.0
    weighted_interest = (enriched['principal_balance'] * enriched['interest_rate']).dropna()
    portfolio_yield = float(weighted_interest.sum()) / principal_sum if principal_sum > 0 else 0.0
    average_ltv = 0.0 if enriched['ltv_ratio'].dropna().empty else float(enriched['ltv_ratio'].mean(skipna=True))
    average_dti = 0.0 if enriched['dti_ratio'].dropna().empty else float(enriched['dti_ratio'].mean(skipna=True))
    metrics = {'delinquency_rate': delinquency_rate, 'portfolio_yield': portfolio_yield, 'average_ltv': average_ltv, 'average_dti': average_dti}
    return (metrics, enriched)

def project_growth(start_yield: float, end_yield: float, start_loan_volume: float, end_loan_volume: float, periods: int=6) -> pd.DataFrame:
    if periods < 2:
        raise ValueError('periods must be at least 2')
    base_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    months = pd.date_range(base_month, periods=periods, freq='MS')
    projection = pd.DataFrame({'month': months.strftime('%b %Y'), 'yield': np.linspace(float(start_yield), float(end_yield), periods), 'loan_volume': np.linspace(float(start_loan_volume), float(end_loan_volume), periods)})
    return projection
__all__ = ['MYPEBusinessRules', 'calculate_quality_score', 'portfolio_kpis', 'project_growth', 'standardize_numeric']
