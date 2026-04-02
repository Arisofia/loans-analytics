from typing import Any
import pandas as pd
from backend.loans_analytics.kpis._column_utils import first_matching_column as _first_col, resolve_dpd_heuristic, to_numeric_safe as _to_num
from backend.loans_analytics.logging_config import get_logger
logger = get_logger(__name__)
_NIM_FORMULA = '(gross_yield_rate - funding_cost_rate) * 100'
_CURE_RATE_FORMULA = 'delinquent_with_recent_payment / total_delinquent * 100'
_CURE_RATE_NOTE = 'Proxy metric: requires T/T-1 snapshots for precise cure rate'

def _safe_pct(numerator: float, denominator: float) -> float:
    return 0.0 if denominator <= 0 else round(numerator / denominator * 100.0, 4)

def _resolve_balance(df: pd.DataFrame) -> pd.Series:
    col = _first_col(df, ['principal_balance', 'outstanding_balance', 'outstanding_loan_value', 'amount', 'principal_amount', 'loan_amount'])
    if col is None:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)
    return _to_num(df[col])

def _resolve_dpd(df: pd.DataFrame) -> pd.Series:
    return resolve_dpd_heuristic(df)

def _resolve_default_mask(df: pd.DataFrame, dpd: pd.Series) -> pd.Series:
    status_col = _first_col(df, ['loan_status', 'status', 'current_status'])
    mask = dpd > 90
    if status_col:
        status = df[status_col].astype(str).str.lower()
        mask = mask | status.str.contains('default|charged|90\\+', regex=True, na=False)
    return mask

def calculate_npl_ratio(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {'npl_ratio': 0.0, 'npl_balance': 0.0, 'total_balance': 0.0, 'npl_loan_count': 0, 'formula': "SUM(balance WHERE dpd >= 90 OR status IN (defaulted, written_off)) / SUM(balance) * 100"}
    balance = _resolve_balance(df)
    dpd = _resolve_dpd(df)
    npl_mask = dpd >= 90
    if status_col := _first_col(df, ['loan_status', 'status', 'current_status']):
        status = df[status_col].astype(str).str.lower().str.strip()
        npl_mask = npl_mask | status.isin({'defaulted', 'written_off'})
    from decimal import Decimal
    total_balance_raw = balance.sum()
    npl_balance_raw = balance[npl_mask].sum()
    total_balance = Decimal(str(total_balance_raw))
    npl_balance = Decimal(str(npl_balance_raw))
    npl_loan_count = int(npl_mask.sum())
    npl_ratio = float(_safe_pct(float(npl_balance), float(total_balance)))
    logger.debug('NPL ratio=%.4f%%, balance=%.2f, count=%d', npl_ratio, float(npl_balance), npl_loan_count)
    return {'npl_ratio': npl_ratio, 'npl_balance': float(round(npl_balance, 2)), 'total_balance': float(round(total_balance, 2)), 'npl_loan_count': npl_loan_count, 'formula': "SUM(balance WHERE dpd >= 90 OR status IN (defaulted, written_off)) / SUM(balance) * 100"}

def calculate_lgd(df: pd.DataFrame) -> dict[str, Any]:
    empty_result: dict[str, Any] = {'lgd_pct': 0.0, 'recovery_rate_pct': 0.0, 'defaulted_balance': 0.0, 'recovered_amount': 0.0, 'formula': '(defaulted_balance - recovered_amount) / defaulted_balance * 100'}
    if df.empty:
        return empty_result
    balance = _resolve_balance(df)
    dpd = _resolve_dpd(df)
    default_mask = _resolve_default_mask(df, dpd)
    defaulted_balance = float(balance[default_mask].sum())
    if defaulted_balance <= 0:
        return empty_result
    if recovery_col := _first_col(df, ['recovery_value', 'Recovery Value', 'recovery_amount']):
        recovery = _to_num(df[recovery_col])
        recovered = float(recovery[default_mask].sum())
    else:
        collected_col = _first_col(df, ['last_payment_amount', 'payment_amount'])
        recovered = float(_to_num(df[collected_col])[default_mask].sum()) if collected_col else 0.0
    recovery_rate = _safe_pct(recovered, defaulted_balance)
    lgd = max(0.0, round(100.0 - recovery_rate, 4))
    logger.debug('LGD=%.4f%%, recovery_rate=%.4f%%', lgd, recovery_rate)
    return {'lgd_pct': lgd, 'recovery_rate_pct': round(recovery_rate, 4), 'defaulted_balance': round(defaulted_balance, 2), 'recovered_amount': round(recovered, 2), 'formula': '(defaulted_balance - recovered_amount) / defaulted_balance * 100'}

def calculate_cost_of_risk(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {'cost_of_risk_pct': 0.0, 'npl_ratio': 0.0, 'lgd_pct': 0.0, 'expected_loss_balance': 0.0, 'formula': 'NPL_ratio * LGD / 100'}
    npl_data = calculate_npl_ratio(df)
    lgd_data = calculate_lgd(df)
    npl_ratio = npl_data['npl_ratio']
    lgd_pct = lgd_data['lgd_pct']
    cor = round(npl_ratio * lgd_pct / 100.0, 4)
    logger.debug('Cost of Risk=%.4f%%, NPL=%.4f%%, LGD=%.4f%%', cor, npl_ratio, lgd_pct)
    return {'cost_of_risk_pct': cor, 'npl_ratio': npl_ratio, 'lgd_pct': lgd_pct, 'expected_loss_balance': round(npl_data['total_balance'] * cor / 100.0, 2), 'formula': 'NPL_ratio * LGD / 100'}

def calculate_nim(df: pd.DataFrame, funding_cost_rate: float=0.08) -> dict[str, Any]:
    funding_cost_pct = round(funding_cost_rate * 100.0, 4)
    if df.empty:
        return {'nim_pct': 0.0, 'gross_yield_pct': 0.0, 'funding_cost_pct': funding_cost_pct, 'interest_income': 0.0, 'total_balance': 0.0, 'formula': _NIM_FORMULA}
    balance = _resolve_balance(df)
    total_balance = float(balance.sum())
    if total_balance <= 0:
        return {'nim_pct': 0.0, 'gross_yield_pct': 0.0, 'funding_cost_pct': funding_cost_pct, 'interest_income': 0.0, 'total_balance': 0.0, 'formula': _NIM_FORMULA}
    if rate_col := _first_col(df, ['interest_rate', 'interest_rate_apr']):
        rates = _to_num(df[rate_col])
        median_rate = float(rates[rates > 0].median()) if (rates > 0).any() else 0.0
        if median_rate > 1.0:
            rates = rates / 100.0
        interest_income = float((rates * balance).sum())
    else:
        interest_income = 0.0
    gross_yield = _safe_pct(interest_income, total_balance)
    nim = round(gross_yield - funding_cost_pct, 4)
    logger.debug('NIM=%.4f%%, gross_yield=%.4f%%, funding_cost=%.4f%%', nim, gross_yield, funding_cost_pct)
    return {'nim_pct': nim, 'gross_yield_pct': round(gross_yield, 4), 'funding_cost_pct': funding_cost_pct, 'interest_income': round(interest_income, 2), 'total_balance': round(total_balance, 2), 'formula': _NIM_FORMULA}

def calculate_payback_period(cac: float, monthly_arpu: float) -> dict[str, Any]:
    if monthly_arpu <= 0 or cac <= 0:
        return {'payback_months': None, 'cac': round(cac, 2), 'monthly_arpu': round(monthly_arpu, 2), 'formula': 'CAC / monthly_ARPU'}
    payback = round(cac / monthly_arpu, 2)
    logger.debug('Payback period=%.2f months, CAC=%.2f, ARPU=%.2f', payback, cac, monthly_arpu)
    return {'payback_months': payback, 'cac': round(cac, 2), 'monthly_arpu': round(monthly_arpu, 2), 'formula': 'CAC / monthly_ARPU'}

def calculate_cure_rate(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {'cure_rate_pct': 0.0, 'delinquent_count': 0, 'curing_count': 0, 'formula': _CURE_RATE_FORMULA, 'note': _CURE_RATE_NOTE}
    dpd = _resolve_dpd(df)
    delinquent_mask = dpd > 0
    delinquent_count = int(delinquent_mask.sum())
    if delinquent_count == 0:
        return {'cure_rate_pct': 0.0, 'delinquent_count': 0, 'curing_count': 0, 'formula': _CURE_RATE_FORMULA, 'note': _CURE_RATE_NOTE}
    if collected_col := _first_col(df, ['last_payment_amount', 'payment_amount']):
        collected = _to_num(df[collected_col])
        curing_mask = delinquent_mask & (collected > 0)
    else:
        curing_mask = pd.Series([False] * len(df), index=df.index)
    curing_count = int(curing_mask.sum())
    cure_rate = _safe_pct(float(curing_count), float(delinquent_count))
    logger.debug('Cure rate=%.4f%%, delinquent=%d, curing=%d', cure_rate, delinquent_count, curing_count)
    return {'cure_rate_pct': round(cure_rate, 4), 'delinquent_count': delinquent_count, 'curing_count': curing_count, 'formula': _CURE_RATE_FORMULA, 'note': _CURE_RATE_NOTE}

def calculate_dpd_migration_risk(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    balance = _resolve_balance(df)
    dpd = _resolve_dpd(df)
    total_balance = float(balance.sum())
    buckets_def: list[tuple[str, pd.Series, str, str]] = [('current', dpd <= 0, 'low', 'Monitor – no immediate action'), ('dpd_1_30', (dpd > 0) & (dpd <= 30), 'medium', 'Trigger early collection contact (SMS / call)'), ('dpd_31_60', (dpd > 30) & (dpd <= 60), 'high', 'Escalate collection intensity – send formal notice'), ('dpd_61_90', (dpd > 60) & (dpd <= 90), 'critical', 'Activate legal / field team and restructure review'), ('dpd_90_plus', dpd > 90, 'critical', 'Full provision write-off candidate – activate recovery workflow')]
    rows: list[dict[str, Any]] = []
    for bucket_name, mask, risk_level, recommended_action in buckets_def:
        bucket_balance = float(balance[mask].sum())
        rows.append({'bucket': bucket_name, 'loan_count': int(mask.sum()), 'balance': round(bucket_balance, 2), 'balance_share_pct': round(_safe_pct(bucket_balance, total_balance), 4), 'risk_level': risk_level, 'recommended_action': recommended_action})
    return rows

def calculate_all_unit_economics(df: pd.DataFrame, funding_cost_rate: float=0.08, cac: float=0.0, monthly_arpu: float=0.0) -> dict[str, Any]:
    if df.empty:
        return {'npl': calculate_npl_ratio(pd.DataFrame()), 'lgd': calculate_lgd(pd.DataFrame()), 'cost_of_risk': calculate_cost_of_risk(pd.DataFrame()), 'nim': calculate_nim(pd.DataFrame(), funding_cost_rate), 'payback': calculate_payback_period(cac, monthly_arpu), 'cure_rate': calculate_cure_rate(pd.DataFrame()), 'dpd_migration': []}
    return {'npl': calculate_npl_ratio(df), 'lgd': calculate_lgd(df), 'cost_of_risk': calculate_cost_of_risk(df), 'nim': calculate_nim(df, funding_cost_rate), 'payback': calculate_payback_period(cac, monthly_arpu), 'cure_rate': calculate_cure_rate(df), 'dpd_migration': calculate_dpd_migration_risk(df)}
