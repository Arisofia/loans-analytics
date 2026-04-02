import logging
from decimal import Decimal
from typing import Any
import pandas as pd
from backend.loans_analytics.kpis._column_utils import first_matching_column as _first_existing_column, resolve_dpd_heuristic, to_numeric_safe as _to_numeric
from backend.loans_analytics.kpis.ssot_asset_quality import calculate_asset_quality_metrics

logger = logging.getLogger(__name__)

def _series_sum_decimal(series: pd.Series) -> Decimal:
    return Decimal(str(series.sum()))

def _safe_pct(numerator: float | Decimal, denominator: float | Decimal) -> Decimal:
    num_dec = Decimal(str(numerator)) if isinstance(numerator, float) else Decimal(numerator)
    denom_dec = Decimal(str(denominator)) if isinstance(denominator, float) else Decimal(denominator)
    return num_dec / denom_dec * Decimal('100') if denom_dec > 0 else Decimal('0')

def _rounded_pct_from_sums(numerator_sum: Decimal, denominator_series: pd.Series) -> float:
    denominator_sum = _series_sum_decimal(denominator_series)
    return round(float(_safe_pct(numerator_sum, denominator_sum)), 2)

def _normalize_interest_rate(series: pd.Series) -> pd.Series:
    """Normalize interest rates to decimal form (e.g. 24 % → 0.24).

    Uses a simple median > 1.0 heuristic — see the fuller implementation in
    ``transformation.py._normalize_interest_rate`` for term-aware logic.
    """
    if series.empty:
        return series
    clean = series.copy()
    median = clean.median()
    if pd.notna(median) and median > 1.0:
        clean = clean / 100.0
    return clean

def _build_dpd_bucket(bucket_name: str, mask: pd.Series, balance: pd.Series, total_balance: Decimal) -> dict[str, float | int | str]:
    bucket_balance = _series_sum_decimal(balance[mask])
    balance_share = _safe_pct(bucket_balance, total_balance)
    return {'bucket': bucket_name, 'loan_count': int(mask.sum()), 'balance': round(float(bucket_balance), 2), 'balance_share_pct': round(float(balance_share), 2)}

def _build_default_mask(df: pd.DataFrame, dpd: pd.Series) -> pd.Series:
    if (status_col := _first_existing_column(df, ['loan_status', 'status', 'current_status'])):
        status = df[status_col].astype(str).str.lower()
        return status.str.contains('default|charged', regex=True, na=False)
    return dpd > 90

def _resolve_series(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    col = _first_existing_column(df, candidates)
    if col is None:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)
    return _to_numeric(df[col])

def _resolve_identifier(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    col = _first_existing_column(df, candidates)
    if col is not None:
        return df[col].astype(str).fillna('')
    loan_col = _first_existing_column(df, ['loan_id', 'id'])
    if loan_col is not None:
        return df[loan_col].astype(str).fillna('')
    return pd.Series([f'loan-{idx + 1}' for idx in range(len(df))], index=df.index)

def _status_series(df: pd.DataFrame) -> pd.Series:
    status_col = _first_existing_column(df, ['status', 'loan_status', 'current_status'])
    if status_col is None:
        return pd.Series(['active'] * len(df), index=df.index, dtype=str)
    return df[status_col].astype(str).str.lower().fillna('active')

def _calculate_ssot_par_metrics(balance: pd.Series, dpd: pd.Series, status: pd.Series) -> dict[str, float]:
    values = calculate_asset_quality_metrics(balance, dpd, actor='advanced_risk', metric_aliases=('par30', 'par60', 'par90'), status=status)
    return {'par30': round(values.get('par30', 0.0), 2), 'par60': round(values.get('par60', 0.0), 2), 'par90': round(values.get('par90', 0.0), 2)}

def _build_credit_quality_index(df: pd.DataFrame) -> float:
    score_col = _first_existing_column(df, ['credit_score', 'equifax_score', 'Equifax Score'])
    if not score_col:
        return 0.0
    scores = _to_numeric(df[score_col])
    scores = scores[scores > 0]
    if scores.empty:
        return 0.0
    avg_score = float(scores.mean())
    quality_index = (avg_score - 300.0) / 550.0 * 100.0
    return round(max(0.0, min(100.0, quality_index)), 2)

def calculate_advanced_risk_metrics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {'par30': 0.0, 'par60': 0.0, 'par90': 0.0, 'default_rate': 0.0, 'collections_coverage': 0.0, 'fee_yield': 0.0, 'total_yield': 0.0, 'recovery_rate': 0.0, 'concentration_hhi': 0.0, 'repeat_borrower_rate': 0.0, 'credit_quality_index': 0.0, 'total_loans': 0, 'dpd_buckets': []}
    balance = _resolve_series(df, ['principal_balance', 'outstanding_balance', 'outstanding_loan_value', 'amount', 'principal_amount', 'loan_amount'])
    principal = _resolve_series(df, ['loan_amount', 'principal_amount', 'amount'])
    interest_rate = _normalize_interest_rate(_resolve_series(df, ['interest_rate', 'interest_rate_apr']))
    dpd = resolve_dpd_heuristic(df)
    status = _status_series(df)
    default_mask = _build_default_mask(df, dpd)
    borrower_id = _resolve_identifier(df, ['borrower_id', 'customer_id', 'Customer ID_cust', 'borrower_name'])
    total_balance = _series_sum_decimal(balance)
    total_loans = len(df)
    try:
        par_metrics = _calculate_ssot_par_metrics(balance, dpd, status)
        par30 = par_metrics['par30']
        par60 = par_metrics['par60']
        par90 = par_metrics['par90']
    except Exception:
        logger.warning(
            "SSOT PAR calculation failed; using DPD-only fallback "
            "(status-based delinquency flags will be ignored)"
        )
        par30_pct = _safe_pct(_series_sum_decimal(balance[dpd >= 30]), total_balance)
        par60_pct = _safe_pct(_series_sum_decimal(balance[dpd >= 60]), total_balance)
        par90_pct = _safe_pct(_series_sum_decimal(balance[dpd >= 90]), total_balance)
        par30 = round(float(par30_pct), 2)
        par60 = round(float(par60_pct), 2)
        par90 = round(float(par90_pct), 2)
    default_count = _series_sum_decimal(default_mask)
    default_rate_pct = _safe_pct(default_count, Decimal(str(total_loans)))
    default_rate = round(float(default_rate_pct), 2)
    collected = _resolve_series(df, ['last_payment_amount', 'payment_amount', 'payments_collected'])
    scheduled = _resolve_series(df, ['total_scheduled', 'scheduled_amount', 'payments_due'])
    collected_sum = _series_sum_decimal(collected)
    collections_coverage = _rounded_pct_from_sums(collected_sum, scheduled)
    fee = _resolve_series(df, ['origination_fee', 'fee_amount'])
    fee_taxes = _resolve_series(df, ['origination_fee_taxes', 'fee_taxes'])
    fee_sum = _series_sum_decimal(fee + fee_taxes)
    fee_yield = _rounded_pct_from_sums(fee_sum, principal)
    interest_yield_pct = _safe_pct(_series_sum_decimal(interest_rate * balance), total_balance)
    interest_yield = float(interest_yield_pct)
    total_yield = round(float(Decimal(str(interest_yield)) + Decimal(str(fee_yield))), 2)
    recovery = _resolve_series(df, ['recovery_value', 'Recovery Value', 'recovery_amount'])
    default_balance = _series_sum_decimal(balance[default_mask])
    recovery_sum = _series_sum_decimal(recovery[default_mask]) if default_mask.any() else _series_sum_decimal(recovery)
    recovery_rate_pct = _safe_pct(recovery_sum, default_balance)
    recovery_rate = round(float(recovery_rate_pct), 2)
    exposure_by_borrower = pd.DataFrame({'borrower_id': borrower_id, 'balance': balance})
    exposure_by_borrower = exposure_by_borrower.groupby('borrower_id', dropna=False)['balance'].sum()
    if total_balance > 0 and (not exposure_by_borrower.empty):
        shares = exposure_by_borrower / float(total_balance)
        concentration_hhi = round(float(_series_sum_decimal(shares.pow(2)) * Decimal('10000')), 2)
    else:
        concentration_hhi = 0.0
    loans_per_borrower = borrower_id.value_counts(dropna=False)
    repeat_borrowers = int((loans_per_borrower > 1).sum())
    repeat_borrower_pct = _safe_pct(Decimal(str(repeat_borrowers)), Decimal(str(len(loans_per_borrower))))
    repeat_borrower_rate = round(float(repeat_borrower_pct), 2)
    dpd_buckets = [_build_dpd_bucket('current', dpd <= 0, balance, total_balance), _build_dpd_bucket('1_30', (dpd > 0) & (dpd <= 30), balance, total_balance), _build_dpd_bucket('31_60', (dpd > 30) & (dpd <= 60), balance, total_balance), _build_dpd_bucket('61_90', (dpd > 60) & (dpd <= 90), balance, total_balance), _build_dpd_bucket('90_plus', dpd > 90, balance, total_balance)]
    return {'par30': par30, 'par60': par60, 'par90': par90, 'default_rate': default_rate, 'collections_coverage': collections_coverage, 'fee_yield': fee_yield, 'total_yield': total_yield, 'recovery_rate': recovery_rate, 'concentration_hhi': concentration_hhi, 'repeat_borrower_rate': repeat_borrower_rate, 'credit_quality_index': _build_credit_quality_index(df), 'total_loans': total_loans, 'dpd_buckets': dpd_buckets}
