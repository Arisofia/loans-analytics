"""COMPATIBILITY_ONLY — Legacy analytics helpers.

This module provides utility functions (standardize_numeric, calculate_quality_score,
portfolio_kpis, project_growth) retained for backward compatibility and test support.

It is NOT the KPI Single Source of Truth.  Canonical KPI formulas live in:
  - backend.loans_analytics.kpis.ssot_asset_quality  (PAR, NPL, asset-quality)
  - backend.loans_analytics.kpis.engine              (KPIEngineV2)
  - backend.loans_analytics.kpis.health_score        (portfolio health scoring)

Do NOT add new financial math here.  Any new metric must be added to the
canonical KPI engine and routed through the SSoT layer.
"""
from __future__ import annotations
import math
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Optional
import numpy as np
import pandas as pd
from backend.loans_analytics.config.mype_rules import MYPEBusinessRules
from backend.src.kpi_engine.revenue import compute_portfolio_yield
from backend.src.kpi_engine.risk import compute_delinquency_rate_by_balance

_DECIMAL_SYMBOL_RE = re.compile(r'[$€£¥₽%,\s]')
_DECIMAL_NONNUM_RE = re.compile(r'[^0-9\-.]')


def _to_decimal(val: Any) -> Optional[Decimal]:
    """Convert a value to Decimal without an intermediate float coercion.

    Integers and existing Decimals are converted exactly.  Floats use Python's
    shortest-repr ``str()`` (safe for normal financial magnitudes).  Strings are
    cleaned of formatting characters (currency symbols, commas, whitespace) and
    then parsed directly, bypassing any float step.

    Returns None for null / unparseable values.
    """
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    if isinstance(val, int):
        return Decimal(val)
    if isinstance(val, float):
        return None if math.isnan(val) else Decimal(str(val))
    # String path — clean without float intermediate
    s = _DECIMAL_SYMBOL_RE.sub('', str(val).strip())
    s = _DECIMAL_NONNUM_RE.sub('', s)
    if not s:  # all letter/symbol variants cleaned to '' by regex above
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


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

def _validate_required_columns(df: pd.DataFrame) -> None:
    required = ['loan_amount', 'appraised_value', 'borrower_income', 'monthly_debt', 'principal_balance', 'interest_rate', 'loan_status']
    if missing := [col for col in required if col not in df.columns]:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _enrich_portfolio_data(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    numeric_cols = ['loan_amount', 'appraised_value', 'borrower_income', 'monthly_debt', 'principal_balance', 'interest_rate']
    for col in numeric_cols:
        enriched[col] = standardize_numeric(enriched[col])

    with np.errstate(divide='ignore', invalid='ignore'):
        enriched['ltv_ratio'] = enriched['loan_amount'] / enriched['appraised_value'].replace(0, np.nan)

    income_positive = enriched['borrower_income'] > 0
    enriched['dti_ratio'] = np.nan
    monthly_income = enriched.loc[income_positive, 'borrower_income'] / 12
    enriched.loc[income_positive, 'dti_ratio'] = enriched.loc[income_positive, 'monthly_debt'] / monthly_income
    return enriched


def _compute_manual_aggregations(df: pd.DataFrame, enriched: pd.DataFrame) -> dict[str, Any]:
    _D_ZERO = Decimal('0')
    _D_12 = Decimal('12')
    res = {
        'ltv_sum': _D_ZERO, 'ltv_count': 0,
        'dti_sum': _D_ZERO, 'dti_count': 0
    }

    delinquent_mask = enriched['loan_status'].astype(str).str.lower().eq('delinquent')
    delinquent_list = delinquent_mask.tolist()
    income_positive_list = (enriched['borrower_income'] > 0).tolist()

    for i, (la, av, bi, md, pb, ir) in enumerate(zip(
        df['loan_amount'], df['appraised_value'], df['borrower_income'],
        df['monthly_debt'], df['principal_balance'], df['interest_rate'],
    )):
        # LTV aggregation
        d_la, d_av = _to_decimal(la), _to_decimal(av)
        if d_la is not None and d_av is not None and d_av != _D_ZERO:
            res['ltv_sum'] += d_la / d_av
            res['ltv_count'] += 1

        # DTI aggregation
        if income_positive_list[i]:
            d_md, d_bi = _to_decimal(md), _to_decimal(bi)
            if d_md is not None and d_bi is not None:
                res['dti_sum'] += d_md / (d_bi / _D_12)
                res['dti_count'] += 1
    return res


def portfolio_kpis(df: pd.DataFrame) -> tuple[dict[str, float], pd.DataFrame]:
    _validate_required_columns(df)
    if df.empty:
        return ({'delinquency_rate': 0.0, 'portfolio_yield': 0.0, 'average_ltv': 0.0, 'average_dti': 0.0}, df.copy())

    enriched = _enrich_portfolio_data(df)
    agg = _compute_manual_aggregations(df, enriched)

    canonical_frame = pd.DataFrame({
        'outstanding_principal': enriched['principal_balance'],
        'interest_rate': enriched['interest_rate'],
        'status': enriched['loan_status'].astype(str).str.lower(),
    })

    delinquency_rate = float(compute_delinquency_rate_by_balance(canonical_frame))
    portfolio_yield = float(compute_portfolio_yield(canonical_frame) / Decimal('100'))
    average_ltv = 0.0 if agg['ltv_count'] == 0 else float(agg['ltv_sum'] / Decimal(agg['ltv_count']))
    average_dti = 0.0 if agg['dti_count'] == 0 else float(agg['dti_sum'] / Decimal(agg['dti_count']))

    metrics = {
        'delinquency_rate': delinquency_rate,
        'portfolio_yield': portfolio_yield,
        'average_ltv': average_ltv,
        'average_dti': average_dti
    }
    return (metrics, enriched)

def project_growth(start_yield: float, end_yield: float, start_loan_volume: float, end_loan_volume: float, periods: int=6) -> pd.DataFrame:
    if periods < 2:
        raise ValueError('periods must be at least 2')
    base_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    months = pd.date_range(base_month, periods=periods, freq='MS')
    return pd.DataFrame(
        {
            'month': months.strftime('%b %Y'),
            'yield': np.linspace(start_yield, end_yield, periods),
            'loan_volume': np.linspace(start_loan_volume, end_loan_volume, periods),
        }
    )
__all__ = ['MYPEBusinessRules', 'calculate_quality_score', 'portfolio_kpis', 'project_growth', 'standardize_numeric']
