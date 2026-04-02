from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any
import numpy as np
import pandas as pd
from backend.loans_analytics.kpis.ssot_asset_quality import calculate_asset_quality_metrics
from backend.loans_analytics.kpis._column_utils import _col
logger = logging.getLogger(__name__)
HEAD_OF_RISK = 'Head of Risk'
HEAD_OF_PRICING = 'Head of Pricing'

def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors='coerce').fillna(0.0)

def _calculate_ssot_asset_quality_metrics(balance: pd.Series, dpd: pd.Series, status: pd.Series) -> dict[str, float]:
    values = calculate_asset_quality_metrics(balance, dpd, actor='strategic_modules', metric_aliases=('par30', 'par90', 'npl180'), status=status)
    return {'par30': values.get('par30', 0.0), 'par90': values.get('par90', 0.0), 'npl180': values.get('npl180', 0.0)}

def _empty_outlier_payload() -> dict[str, Any]:
    return {'alerts': [], 'summary': {}, 'total_flagged': 0, 'total_flagged_balance_usd': 0.0}

def _resolve_outlier_variables(loans_df: pd.DataFrame) -> dict[str, pd.Series]:
    mappings = [('apr', ['interest_rate_apr', 'interest_rate', 'TasaInteres']), ('dpd', ['days_past_due', 'dpd', 'DPD', 'days_in_default']), ('term_days', ['term', 'Term', 'term_days']), ('line_util_pct', ['porcentaje_utilizado', 'line_utilization', 'Porcentaje_Utilizado'])]
    resolved: dict[str, pd.Series] = {}
    for var_name, aliases in mappings:
        if column := _col(loans_df, aliases):
            resolved[var_name] = _num(loans_df, column)
    return resolved

def _append_outlier_alerts(alerts: list[dict[str, Any]], loans_df: pd.DataFrame, flag_mask: pd.Series, loan_id_col: str | None, var_name: str, series: pd.Series, z_scores: pd.Series, bal: pd.Series) -> None:
    if not flag_mask.any():
        return
    flagged = loans_df[flag_mask]
    for idx in flagged.index:
        loan_id = str(flagged.at[idx, loan_id_col]) if loan_id_col else str(idx)
        alerts.append({'loan_id': loan_id, 'variable': var_name, 'value': round(float(series.at[idx]), 4), 'z_score': round(float(z_scores.at[idx]), 2), 'outstanding_usd': round(float(bal.at[idx]), 2)})

def _compute_weighted_zscore_stats(var_name: str, series: pd.Series, bal: pd.Series, z_threshold: float, loans_df: pd.DataFrame, loan_id_col: str | None) -> tuple[dict, list[dict]]:
    """Compute Z-score statistics and detect outliers for a single variable."""
    total_w = bal.sum()
    w_mean = float((series * bal).sum() / total_w)
    w_var = float(((series - w_mean) ** 2 * bal).sum() / total_w)
    w_std = float(np.sqrt(w_var)) if w_var > 0 else 0.0
    
    summary_entry = {'mean_w': w_mean, 'std_w': 0.0, 'outlier_count': 0, 'outlier_balance_usd': 0.0}
    alerts: list[dict[str, Any]] = []
    
    if w_std == 0:
        summary_entry['mean_w'] = w_mean
        return (summary_entry, alerts)
    
    z_scores = (series - w_mean) / w_std
    flag_mask = z_scores.abs() > z_threshold
    flag_bal = float(bal[flag_mask].sum())
    
    summary_entry = {'mean_w': round(w_mean, 4), 'std_w': round(w_std, 4), 'outlier_count': int(flag_mask.sum()), 'outlier_balance_usd': round(flag_bal, 2)}
    
    if flag_mask.any():
        flag_df = loans_df[flag_mask].copy()
        for idx in flag_df.index:
            loan_id = str(flag_df.at[idx, loan_id_col]) if loan_id_col else str(idx)
            alerts.append({
                'loan_id': loan_id,
                'variable': var_name,
                'value': round(float(series.at[idx]), 4),
                'z_score': round(float(z_scores.at[idx]), 2),
                'outstanding_usd': round(float(bal.at[idx]), 2)
            })
    
    return (summary_entry, alerts)

def detect_exposure_weighted_outliers(loans_df: pd.DataFrame, z_threshold: float=2.58) -> dict[str, Any]:
    loan_id_col = _col(loans_df, ['loan_id', 'Loan ID', 'id'])
    bal_col = _col(loans_df, ['outstanding_loan_value', 'outstanding_balance', 'TotalSaldoVigente'])
    if bal_col is None:
        logger.warning('detect_exposure_weighted_outliers: no balance column found')
        return _empty_outlier_payload()
    
    bal = _num(loans_df, bal_col).clip(lower=0)
    if bal.sum() == 0:
        return _empty_outlier_payload()
    variables = _resolve_outlier_variables(loans_df)
    
    alerts: list[dict] = []
    summary: dict[str, dict] = {}
    
    for var_name, series in variables.items():
        summary_entry, var_alerts = _compute_weighted_zscore_stats(var_name, series, bal, z_threshold, loans_df, loan_id_col)
        summary[var_name] = summary_entry
        alerts.extend(var_alerts)
    
    alerts.sort(key=lambda x: abs(x['z_score']), reverse=True)
    total_bal = sum((a['outstanding_usd'] for a in alerts))
    return {'alerts': alerts[:200], 'summary': summary, 'total_flagged': len(alerts), 'total_flagged_balance_usd': round(total_bal, 2), 'z_threshold': z_threshold}

def _detect_pd_columns(loans_df: pd.DataFrame) -> tuple[str | None, str | None, str | None]:
    return (_col(loans_df, ['loan_status', 'Loan Status', 'status']), _col(loans_df, ['outstanding_loan_value', 'outstanding_balance']), _col(loans_df, ['loan_id', 'Loan ID', 'id']))

def _build_pd_feature_matrix(loans_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    feature_cols: dict[str, str] = {}
    for fname, aliases in [('apr', ['interest_rate_apr', 'interest_rate', 'TasaInteres']), ('term', ['term', 'Term', 'term_days']), ('disb_amount', ['disbursement_amount', 'MontoDesembolsado']), ('outstanding', ['outstanding_loan_value', 'TotalSaldoVigente']), ('tpv', ['tpv', 'TPV', 'total_portfolio_value'])]:
        if column := _col(loans_df, aliases):
            feature_cols[fname] = column
    x_raw = pd.DataFrame({fname: _num(loans_df, col) for fname, col in feature_cols.items()}).fillna(0)
    return (x_raw, feature_cols)

def _build_pd_weights(loans_df: pd.DataFrame, bal_col: str | None) -> pd.Series:
    if bal_col:
        return _num(loans_df, bal_col).clip(lower=1.0)
    return pd.Series(np.ones(len(loans_df)), index=loans_df.index)

def _run_pd_cross_validation(clf: Any, x_scaled: Any, y: pd.Series, weights: pd.Series, cv_folds: int) -> Any:
    from sklearn.base import clone
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    scores: list[float] = []
    for train_idx, test_idx in skf.split(x_scaled, y):
        model = clone(clf)
        model.fit(x_scaled[train_idx], y.iloc[train_idx], sample_weight=weights.iloc[train_idx].values)
        fold_scores = model.predict_proba(x_scaled[test_idx])[:, 1]
        scores.append(float(roc_auc_score(y.iloc[test_idx], fold_scores)))
    return np.array(scores, dtype=float)

def _compute_pd_calibration(y: pd.Series, pd_scores: Any) -> float | None:
    try:
        from sklearn.calibration import calibration_curve
        from numpy.polynomial.polynomial import polyfit as npfit
        frac_pos, mean_pred = calibration_curve(y, pd_scores, n_bins=5)
        return float(npfit(mean_pred, frac_pos, 1)[1]) if len(frac_pos) > 1 else 1.0
    except Exception:
        logger.warning('PD calibration failed — returning None', exc_info=True)
        return None

def build_pd_model(loans_df: pd.DataFrame, min_defaults: int=30, min_non_defaults: int=30, cv_folds: int=5) -> dict[str, Any]:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return {'status': 'error', 'message': 'scikit-learn not installed'}
    status_col, bal_col, loan_id_col = _detect_pd_columns(loans_df)
    if status_col is None:
        return {'status': 'error', 'message': 'No status column found'}
    status_series = loans_df[status_col].astype(str).str.lower()
    y = status_series.str.contains('default|defaulted', regex=True, na=False).astype(int)
    n_pos = int(y.sum())
    n_neg = int((y == 0).sum())
    if n_pos < min_defaults or n_neg < min_non_defaults:
        return {'status': 'insufficient_data', 'n_defaults': n_pos, 'n_non_defaults': n_neg, 'min_required': f'{min_defaults} defaults + {min_non_defaults} non-defaults', 'message': 'Dataset does not meet minimum class size for stable PD model.'}
    x_raw, feature_cols = _build_pd_feature_matrix(loans_df)
    if len(feature_cols) < 2:
        return {'status': 'error', 'message': f'Insufficient features: {list(feature_cols)}'}
    weights = _build_pd_weights(loans_df, bal_col)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x_raw)
    clf = LogisticRegression(max_iter=1000, class_weight='balanced', solver='lbfgs')
    auc_scores = _run_pd_cross_validation(clf, x_scaled, y, weights, cv_folds)
    clf.fit(x_scaled, y, sample_weight=weights.values)
    pd_scores = clf.predict_proba(x_scaled)[:, 1]
    calib_slope = _compute_pd_calibration(y, pd_scores)
    feature_importance = {fname: round(float(coef), 4) for fname, coef in zip(feature_cols.keys(), clf.coef_[0])}
    loan_ids = loans_df[loan_id_col].astype(str).tolist() if loan_id_col else [str(i) for i in range(len(loans_df))]
    pd_output = sorted([{'loan_id': lid, 'pd_score': round(float(s), 4)} for lid, s in zip(loan_ids, pd_scores)], key=lambda x: x['pd_score'], reverse=True)
    return {'status': 'ok', 'auc_mean': round(float(auc_scores.mean()), 4), 'auc_std': round(float(auc_scores.std()), 4), 'auc_by_fold': [round(float(s), 4) for s in auc_scores], 'calibration_slope': round(calib_slope, 4) if calib_slope else None, 'feature_importance': feature_importance, 'features_used': list(feature_cols.keys()), 'n_defaults': n_pos, 'n_non_defaults': n_neg, 'default_rate_actual': round(n_pos / (n_pos + n_neg) * 100, 2), 'cv_folds': cv_folds, 'model_type': 'logistic_regression_exposure_weighted', 'pd_scores': pd_output[:500]}

def _linear_forecast_from_cutoff(series: pd.Series, horizon: int, cutoff: pd.Timestamp) -> list[dict[str, float | str]]:
    clean_series = series.dropna()
    if len(clean_series) < 3:
        return []
    x_axis = np.arange(len(clean_series))
    slope, intercept = np.polyfit(x_axis, clean_series.values, 1)
    residuals = clean_series.values - (slope * x_axis + intercept)
    sigma = float(np.std(residuals))
    rows: list[dict[str, float | str]] = []
    for horizon_step in range(1, horizon + 1):
        month = cutoff + pd.DateOffset(months=horizon_step)
        point = float(slope * (len(clean_series) - 1 + horizon_step) + intercept)
        rows.append({'month': month.strftime('%Y-%m'), 'value': round(max(point, 0), 2), 'lower': round(max(point - 1.5 * sigma, 0), 2), 'upper': round(point + 1.5 * sigma, 2)})
    return rows

def _monthly_sum_series(df: pd.DataFrame, date_col: str | None, amount_col: str | None, tail_months: int=12) -> pd.Series:
    if not (date_col and amount_col):
        return pd.Series(dtype=float)
    monthly_df = df.copy()
    monthly_df['_month'] = pd.to_datetime(monthly_df[date_col], errors='coerce', format='mixed').dt.to_period('M')
    return monthly_df.groupby('_month')[amount_col].apply(lambda series: pd.to_numeric(series, errors='coerce').fillna(0).sum()).tail(tail_months)

def _par_history_series(loans_df: pd.DataFrame, dpd_col: str | None, disb_col: str | None, bal_col: str | None, status_col: str | None) -> tuple[pd.Series, pd.Series]:
    if not (dpd_col and disb_col and bal_col):
        return (pd.Series(dtype=float), pd.Series(dtype=float))
    df_par = loans_df.copy()
    df_par['_dpd'] = pd.to_numeric(df_par[dpd_col], errors='coerce').fillna(0)
    df_par['_bal'] = pd.to_numeric(df_par[bal_col], errors='coerce').fillna(0)
    df_par['_month'] = pd.to_datetime(df_par[disb_col], errors='coerce', format='mixed').dt.to_period('M')
    month_rows: list[dict[str, float | pd.Period]] = []
    for month, month_df in df_par.groupby('_month'):
        month_status = month_df[status_col].astype(str) if status_col and status_col in month_df.columns else pd.Series(['active'] * len(month_df), index=month_df.index)
        try:
            quality = _calculate_ssot_asset_quality_metrics(balance=month_df['_bal'], dpd=month_df['_dpd'], status=month_status)
            par30_value = quality['par30']
            par90_value = quality['par90']
        except Exception:
            logger.warning('SSOT asset quality failed for month %s — using manual DPD fallback', month, exc_info=True)
            monthly_total = float(month_df['_bal'].sum())
            par30_value = float(month_df.loc[month_df['_dpd'] >= 30, '_bal'].sum() / monthly_total * 100) if monthly_total > 0 else 0.0
            par90_value = float(month_df.loc[month_df['_dpd'] >= 90, '_bal'].sum() / monthly_total * 100) if monthly_total > 0 else 0.0
        month_rows.append({'_month': month, 'par30': par30_value, 'par90': par90_value})
    if not month_rows:
        return (pd.Series(dtype=float), pd.Series(dtype=float))
    monthly = pd.DataFrame(month_rows).sort_values('_month')
    return (monthly.set_index('_month')['par30'].astype(float).tail(12), monthly.set_index('_month')['par90'].astype(float).tail(12))

def predict_kpis(loans_df: pd.DataFrame, payments_df: pd.DataFrame, horizon_months: int=6) -> dict[str, Any]:
    cutoff = pd.Timestamp.now().normalize()
    disb_col = _col(loans_df, ['disbursement_date', 'FechaDesembolso'])
    bal_col = _col(loans_df, ['outstanding_loan_value', 'outstanding_balance'])
    disb_amt_col = _col(loans_df, ['disbursement_amount', 'MontoDesembolsado'])
    aum_series = _monthly_sum_series(loans_df, disb_col, disb_amt_col)
    pay_date_col = _col(payments_df, ['true_payment_date', 'payment_date'])
    pay_amt_col = _col(payments_df, ['true_total_payment', 'payment_amount', 'amount'])
    rev_series = _monthly_sum_series(payments_df, pay_date_col, pay_amt_col)
    dpd_col = _col(loans_df, ['days_past_due', 'dpd', 'days_in_default'])
    status_col = _col(loans_df, ['loan_status', 'status', 'current_status'])
    par30_series, par90_series = _par_history_series(loans_df, dpd_col, disb_col, bal_col, status_col)
    return {'horizon_months': horizon_months, 'generated_at': datetime.now(timezone.utc).isoformat(), 'aum_forecast': _linear_forecast_from_cutoff(aum_series, horizon_months, cutoff), 'revenue_forecast': _linear_forecast_from_cutoff(rev_series, horizon_months, cutoff), 'par30_forecast': _linear_forecast_from_cutoff(par30_series, horizon_months, cutoff), 'par90_forecast': _linear_forecast_from_cutoff(par90_series, horizon_months, cutoff), 'methodology': 'linear_trend_1.5sigma_bands', 'data_notes': {'aum': 'monthly disbursement_amount by origination month (bullet-loan proxy)', 'par': 'vintage approximation from single DPD snapshot — no historical PAR archives', 'revenue': 'true_total_payment per payment month from real_payment.csv'}, 'training_months': {'aum': len(aum_series), 'revenue': len(rev_series), 'par30': len(par30_series)}}

def _default_guardrails() -> dict[str, float]:
    try:
        from backend.loans_analytics.config import settings
        return {'rotation_x': settings.financial.min_rotation, 'top1_concentration_pct': settings.financial.max_single_obligor_concentration * 100, 'top10_concentration_pct': settings.financial.max_top_10_concentration * 100, 'par30_pct': 5.0, 'par90_pct': settings.financial.max_default_rate * 100 / 2, 'npl_180_pct': settings.financial.max_default_rate * 100, 'utilization_pct_min': settings.financial.utilization_min * 100, 'utilization_pct_max': settings.financial.utilization_max * 100, 'apr_pct_min': settings.financial.target_apr_min * 100, 'apr_pct_max': settings.financial.target_apr_max * 100, 'ce_6m_pct': settings.financial.min_ce_6m * 100, 'dscr': settings.financial.min_dscr}
    except Exception:
        logger.warning('Failed to load guardrails from settings — using empty defaults', exc_info=True)
        return {}

def _default_owners() -> dict[str, str]:
    return {'rotation_x': 'CFO', 'top1_concentration_pct': 'CRO', 'top10_concentration_pct': 'CRO', 'par30_pct': HEAD_OF_RISK, 'par90_pct': HEAD_OF_RISK, 'npl_180_pct': HEAD_OF_RISK, 'utilization_pct': 'CFO', 'apr_pct_ann': HEAD_OF_PRICING, 'dscr': 'Finance', 'utilization_pct_min': 'CFO', 'apr_pct_min': HEAD_OF_PRICING, 'ce_6m_pct': 'Head of Collections'}

def _resolve_compliance_columns(loans_df: pd.DataFrame) -> dict[str, str | None]:
    return {'bal_col': _col(loans_df, ['outstanding_loan_value', 'outstanding_balance', 'TotalSaldoVigente']), 'disb_col': _col(loans_df, ['disbursement_date', 'FechaDesembolso']), 'apr_col': _col(loans_df, ['interest_rate_apr', 'interest_rate', 'TasaInteres']), 'dpd_col': _col(loans_df, ['days_past_due', 'dpd', 'DPD', 'days_in_default']), 'deb_col': _col(loans_df, ['pagador', 'cliente', 'emisor', 'Emisor', 'debtor_id', 'payer_id']), 'util_col': _col(loans_df, ['porcentaje_utilizado', 'Porcentaje_Utilizado', 'line_utilization']), 'line_col': _col(loans_df, ['lineacredito', 'LineaCredito', 'credit_line']), 'noi_col': _col(loans_df, ['net_operating_income', 'net_income', 'ebitda', 'noi']), 'debt_service_col': _col(loans_df, ['debt_service', 'total_debt_service', 'debt_service_amount', 'monthly_debt_service'])}

def _compute_rotation(loans_df: pd.DataFrame, disb_col: str | None, bal_col: str | None, total_bal: float) -> float:
    if not (disb_col and bal_col and total_bal > 0):
        return 0.0
    dates = pd.to_datetime(loans_df[disb_col], errors='coerce', format='mixed')
    disb_amt = _col(loans_df, ['disbursement_amount', 'MontoDesembolsado'])
    if not disb_amt:
        return 0.0
    cutoff = dates.max()
    mask12 = dates >= cutoff - pd.DateOffset(months=12)
    disb12 = _num(loans_df[mask12], disb_amt).sum() if mask12.any() else 0.0
    return float(disb12 / total_bal)

def _compute_concentration(loans_df: pd.DataFrame, deb_col: str | None, bal: pd.Series, total_bal: float) -> tuple[float, float]:
    if not (deb_col and total_bal > 0):
        return (0.0, 0.0)
    deb_bal = loans_df.assign(_b=bal).groupby(deb_col)['_b'].sum().sort_values(ascending=False)
    top1_pct = float(deb_bal.iloc[0] / total_bal * 100) if len(deb_bal) > 0 else 0.0
    top10_pct = float(deb_bal.head(10).sum() / total_bal * 100)
    return (top1_pct, top10_pct)

def _compute_quality_metrics_or_fallback(bal: pd.Series, dpd: pd.Series, status_series: pd.Series, total_bal: float) -> tuple[float, float, float]:
    try:
        quality_metrics = _calculate_ssot_asset_quality_metrics(bal, dpd, status_series)
        return (quality_metrics['par30'], quality_metrics['par90'], quality_metrics['npl180'])
    except Exception:
        logger.warning('SSOT quality metrics failed — using manual DPD fallback', exc_info=True)
        par30 = float(bal[dpd >= 30].sum() / total_bal * 100) if total_bal > 0 else 0.0
        par90 = float(bal[dpd >= 90].sum() / total_bal * 100) if total_bal > 0 else 0.0
        npl180 = float(bal[dpd >= 180].sum() / total_bal * 100) if total_bal > 0 else 0.0
        return (par30, par90, npl180)

def _compute_utilization(loans_df: pd.DataFrame, util_col: str | None, line_col: str | None, bal_col: str | None, bal: pd.Series) -> float | None:
    if util_col:
        return float(_num(loans_df, util_col).replace(0, np.nan).mean())
    if line_col and bal_col:
        line_values = _num(loans_df, line_col)
        mask = line_values > 0
        if mask.any():
            return float((bal[mask] / line_values[mask]).clip(0, 1).mean() * 100)
    return None

def _compute_ce_6m(loans_df: pd.DataFrame, payments_df: pd.DataFrame, disb_col: str | None) -> float | None:
    pay_amt = _col(payments_df, ['true_total_payment', 'payment_amount'])
    sched = _col(loans_df, ['total_scheduled', 'scheduled_payment', 'ValorAprobado'])
    disb_amt = _col(loans_df, ['disbursement_amount', 'MontoDesembolsado'])
    pay_date = _col(payments_df, ['true_payment_date', 'payment_date'])
    if not (pay_amt and pay_date and disb_col):
        return None
    payment_dates = pd.to_datetime(payments_df[pay_date], errors='coerce', format='mixed')
    mask6m = payment_dates >= payment_dates.max() - pd.DateOffset(months=6)
    collected6 = _num(payments_df[mask6m], pay_amt).sum() if mask6m.any() else 0.0
    disb_dates = pd.to_datetime(loans_df[disb_col], errors='coerce', format='mixed')
    loan_6m = disb_dates >= disb_dates.max() - pd.DateOffset(months=6)
    if sched:
        sched_total = _num(loans_df[loan_6m], sched).sum() if loan_6m.any() else 0.0
    elif disb_amt:
        sched_total = _num(loans_df[loan_6m], disb_amt).sum() if loan_6m.any() else 0.0
    else:
        sched_total = 0.0
    return (collected6 / sched_total * 100) if sched_total > 0 else None

def _compute_dscr(loans_df: pd.DataFrame, noi_col: str | None, debt_service_col: str | None) -> float | None:
    if not (noi_col and debt_service_col):
        return None
    noi_sum = float(_num(loans_df, noi_col).sum())
    debt_service_sum = float(_num(loans_df, debt_service_col).sum())
    return noi_sum / debt_service_sum if debt_service_sum > 0 else None

def _evaluate_metric_status(actual: float, target: float, lower_is_better: bool, warn_band: float) -> str:
    if lower_is_better:
        if actual <= target:
            return 'ok'
        else:
            return 'warning' if actual <= target + warn_band else 'breach'
    if actual >= target:
        return 'ok'
    else:
        return 'warning' if actual >= target - warn_band else 'breach'

def _build_core_metric_rows(actuals: dict[str, Any], guardrails: dict[str, Any], owners: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    metric_defs = {'rotation_x': ('rotation_x', 4.5, False, 0.3), 'top1_concentration_pct': ('top1_concentration_pct', 4.0, True, 1.0), 'top10_concentration_pct': ('top10_concentration_pct', 30.0, True, 3.0), 'par30_pct': ('par30_pct', 5.0, True, 1.0), 'par90_pct': ('par90_pct', 2.0, True, 0.5), 'npl_180_pct': ('npl_180_pct', 4.0, True, 0.5), 'utilization_pct': ('utilization_pct', 75.0, False, 5.0), 'dscr': ('dscr', float(guardrails.get('dscr', 1.2)), False, 0.1), 'ce_6m_pct': ('ce_6m_pct', 96.0, False, 2.0)}
    rows: list[dict[str, Any]] = []
    counts = {'ok': 0, 'warning': 0, 'breach': 0, 'no_data': 0}
    for metric, (act_key, target, lower_is_better, warn_band) in metric_defs.items():
        actual = actuals.get(act_key)
        if actual is None:
            counts['no_data'] += 1
            rows.append({'metric': metric, 'actual': 'NO_DATA', 'target': target, 'variance': None, 'variance_pct': None, 'status': 'no_data', 'lower_is_better': lower_is_better, 'owner': owners.get(metric, '—')})
            continue
        status = _evaluate_metric_status(float(actual), float(target), bool(lower_is_better), float(warn_band))
        variance = float(actual) - float(target)
        variance_pct = round(variance / float(target) * 100, 1) if target else 0.0
        counts[status] += 1
        rows.append({'metric': metric, 'actual': actual, 'target': target, 'variance': round(variance, 2), 'variance_pct': variance_pct, 'status': status, 'lower_is_better': lower_is_better, 'owner': owners.get(metric, '—')})
    return (rows, counts)

def _append_apr_row(rows: list[dict[str, Any]], counts: dict[str, int], actuals: dict[str, Any], owners: dict[str, Any], apr_min: float, apr_max: float) -> None:
    apr_actual = actuals.get('apr_pct_ann')
    owner = owners.get('apr_pct_ann', owners.get('apr_pct_min', HEAD_OF_PRICING))
    if apr_actual is None:
        counts['no_data'] += 1
        rows.append({'metric': 'apr_pct_ann', 'actual': 'NO_DATA', 'target': f'{apr_min:.1f}-{apr_max:.1f}', 'variance': None, 'variance_pct': None, 'status': 'no_data', 'lower_is_better': False, 'owner': owner})
        return
    apr_warn_band = 2.0
    if apr_actual < apr_min:
        apr_var = round(apr_actual - apr_min, 2)
        apr_var_pct = round(apr_var / apr_min * 100, 1) if apr_min else None
        apr_status = 'warning' if apr_actual >= apr_min - apr_warn_band else 'breach'
    elif apr_actual > apr_max:
        apr_var = round(apr_actual - apr_max, 2)
        apr_var_pct = round(apr_var / apr_max * 100, 1) if apr_max else None
        apr_status = 'warning' if apr_actual <= apr_max + apr_warn_band else 'breach'
    else:
        apr_var = 0.0
        apr_var_pct = 0.0
        apr_status = 'ok'
    counts[apr_status] += 1
    rows.append({'metric': 'apr_pct_ann', 'actual': apr_actual, 'target': f'{apr_min:.1f}-{apr_max:.1f}', 'variance': apr_var, 'variance_pct': apr_var_pct, 'status': apr_status, 'lower_is_better': False, 'owner': owner})

def _build_compliance_data_sources(loans_df: pd.DataFrame, dpd_col: str | None, deb_col: str | None, util_col: str | None, line_col: str | None, apr_col: str | None, noi_col: str | None, debt_service_col: str | None) -> dict[str, str]:
    sched = _col(loans_df, ['total_scheduled', 'scheduled_payment', 'ValorAprobado'])
    if util_col:
        util_source = f'loan.{util_col}'
    elif line_col:
        util_source = f'loan.{line_col}'
    else:
        util_source = 'NO_DATA'
    par_source = f'loan.{dpd_col}' if dpd_col else 'NO_DATA'
    concentration_source = f'loan.{deb_col}' if deb_col else 'NO_DATA'
    ce_source = f'payments.true_total_payment / loan.{sched}' if sched else 'payments.true_total_payment / loan.disbursement_amount (6m proxy)'
    apr_source = f'loan.{apr_col} (annual decimal ×100)' if apr_col else 'NO_DATA'
    dscr_source = f'loan.{noi_col} / loan.{debt_service_col}' if noi_col and debt_service_col else 'NO_DATA'
    return {'par': par_source, 'concentration': concentration_source, 'ce_6m': ce_source, 'utilization': util_source, 'apr': apr_source, 'dscr': dscr_source}

def _apr_variance_decomposition(apr_actual: float | None, apr_min: float, apr_max: float) -> dict[str, Any]:
    if apr_actual is None:
        return {'driver': 'APR source unavailable', 'magnitude': None, 'explanation': 'APR cannot be computed because no APR column was found in the loan tape.'}
    if apr_actual < apr_min:
        return {'driver': 'Pricing below target floor', 'magnitude': round(apr_actual - apr_min, 1), 'explanation': f'Weighted APR {apr_actual:.1f}% is below minimum {apr_min:.1f}%. Review pricing floors and discount approvals by segment.'}
    if apr_actual > apr_max:
        return {'driver': 'Pricing above target ceiling', 'magnitude': round(apr_actual - apr_max, 1), 'explanation': f'Weighted APR {apr_actual:.1f}% exceeds maximum {apr_max:.1f}%. Review competitiveness and channel mix impacts.'}
    return {'driver': 'APR within policy corridor', 'magnitude': 0.0, 'explanation': f'Weighted APR {apr_actual:.1f}% is inside the configured range {apr_min:.1f}% to {apr_max:.1f}%.'}

def _dscr_variance_decomposition(dscr_actual: float | None, dscr_target: float) -> dict[str, Any]:
    if dscr_actual is None:
        return {'driver': 'DSCR inputs unavailable', 'magnitude': None, 'explanation': 'DSCR cannot be computed because NOI and debt service fields are not present.'}
    return {'driver': 'Income coverage vs debt service', 'magnitude': round(dscr_actual - dscr_target, 2), 'explanation': f'DSCR {dscr_actual:.2f}x vs target {dscr_target:.2f}x. Improve cash generation or reduce scheduled debt service to lift coverage.'}

def _build_variance_decomposition(top1_pct: float, par30: float, par90: float, rotation_actual: float, apr_actual: float | None, apr_min: float, apr_max: float, dscr_actual: float | None, dscr_target: float) -> dict[str, Any]:
    return {'top1_concentration_pct': {'driver': 'La Constancia LTDA — single pagador dominates', 'magnitude': round(top1_pct - 4.0, 1), 'explanation': f'La Constancia represents ~{top1_pct:.0f}% of AUM vs 4% guardrail. Reduce exposure by originating with competing debtors or applying per-debtor cap.'}, 'par30_pct': {'driver': 'Plazo extension + 2026 payment recording lag', 'magnitude': round(par30 - 5.0, 1), 'explanation': 'PAR30 elevated; partial cause is INTERMEDIA DPD calculated from FechaPagoProgramado without 2026 payment records. Verify with real collections.'}, 'par90_pct': {'driver': 'Structural: factoring ops with extended terms breach 90-day bucket', 'magnitude': round(par90 - 2.0, 1), 'explanation': 'PAR90 guardrail (2%) is aggressive for a 46-day median term book. Recommend reviewing guardrail calibration against peer benchmarks.'}, 'rotation_x': {'driver': 'AUM growth outpacing disbursement velocity in trailing 12m', 'magnitude': round(rotation_actual - 4.5, 2), 'explanation': f'Rotation {rotation_actual:.1f}x vs target 4.5x. Accelerate collections cycle or reduce average term to recover velocity.'}, 'apr_pct_ann': _apr_variance_decomposition(apr_actual, apr_min, apr_max), 'dscr': _dscr_variance_decomposition(dscr_actual, dscr_target)}

def _resolve_status_series(loans_df: pd.DataFrame) -> pd.Series:
    status_col = _col(loans_df, ['loan_status', 'status', 'current_status'])
    if status_col and status_col in loans_df.columns:
        return loans_df[status_col].astype(str)
    return pd.Series(['active'] * len(loans_df), index=loans_df.index)

def build_compliance_dashboard(loans_df: pd.DataFrame, payments_df: pd.DataFrame, guardrails: dict | None=None, owners: dict | None=None) -> dict[str, Any]:
    guardrails = guardrails or _default_guardrails()
    owners = owners or _default_owners()
    columns = _resolve_compliance_columns(loans_df)
    bal_col = columns['bal_col']
    disb_col = columns['disb_col']
    apr_col = columns['apr_col']
    dpd_col = columns['dpd_col']
    deb_col = columns['deb_col']
    util_col = columns['util_col']
    line_col = columns['line_col']
    noi_col = columns['noi_col']
    debt_service_col = columns['debt_service_col']
    loans_df = loans_df.reset_index(drop=True)
    bal = _num(loans_df, bal_col) if bal_col else pd.Series([0.0] * len(loans_df))
    dpd = _num(loans_df, dpd_col) if dpd_col else pd.Series([0.0] * len(loans_df))
    apr = _num(loans_df, apr_col) if apr_col else pd.Series([0.0] * len(loans_df))
    total_bal = bal.sum()
    rotation_actual = _compute_rotation(loans_df, disb_col, bal_col, float(total_bal))
    top1_pct, top10_pct = _compute_concentration(loans_df, deb_col, bal, float(total_bal))
    status_series = _resolve_status_series(loans_df)
    par30, par90, npl180 = _compute_quality_metrics_or_fallback(bal, dpd, status_series, float(total_bal))
    apr_ann = float((apr * bal).sum() / total_bal * 100) if total_bal > 0 and apr_col else None
    util_actual = _compute_utilization(loans_df, util_col, line_col, bal_col, bal)
    ce_actual = _compute_ce_6m(loans_df, payments_df, disb_col)
    dscr_actual = _compute_dscr(loans_df, noi_col, debt_service_col)
    util_actual_val = round(util_actual, 1) if util_actual is not None else None
    apr_ann_val = round(apr_ann, 1) if apr_ann is not None else None
    ce_actual_val = round(ce_actual, 1) if ce_actual is not None else None
    dscr_actual_val = round(dscr_actual, 2) if dscr_actual is not None else None
    actuals = {
        'rotation_x': round(rotation_actual, 2),
        'top1_concentration_pct': round(top1_pct, 1),
        'top10_concentration_pct': round(top10_pct, 1),
        'par30_pct': round(par30, 1),
        'par90_pct': round(par90, 1),
        'npl_180_pct': round(npl180, 1),
        'utilization_pct': util_actual_val,
        'apr_pct_ann': apr_ann_val,
        'ce_6m_pct': ce_actual_val,
        'dscr': dscr_actual_val
    }
    data_sources = _build_compliance_data_sources(loans_df, dpd_col, deb_col, util_col, line_col, apr_col, noi_col, debt_service_col)
    apr_min = float(guardrails.get('apr_pct_min', 36.0))
    apr_max = float(guardrails.get('apr_pct_max', 99.0))
    rows, counts = _build_core_metric_rows(actuals, guardrails, owners)
    _append_apr_row(rows, counts, actuals, owners, apr_min, apr_max)
    apr_actual = actuals.get('apr_pct_ann')
    dscr_target = float(guardrails.get('dscr', 1.2))
    variance_decomp = _build_variance_decomposition(top1_pct, par30, par90, rotation_actual, apr_actual, apr_min, apr_max, dscr_actual, dscr_target)
    return {'generated_at': datetime.now(timezone.utc).isoformat(), 'metrics': rows, 'summary': counts, 'actuals': actuals, 'data_sources': data_sources, 'variance_decomposition': variance_decomp}
_IMPACT_MAP = {'top1_concentration_pct': ('high', 'medium', 'Credit / Risk', 'Cap single-debtor exposure. Originate diversification ops with alternative pagadores.'), 'top10_concentration_pct': ('high', 'low', 'Credit / Risk', 'Activate debtor-limit alerts. Rebalance origination pipeline away from top-10 cluster.'), 'par30_pct': ('high', 'medium', 'Collections', 'Launch DPD 15+ early warning workflow. Assign KAM follow-up for outstanding ops.'), 'par90_pct': ('high', 'high', 'Collections / Risk', 'Escalate 90+ DPD bucket to recovery team. Review provisions and LGD assumptions.'), 'npl_180_pct': ('medium', 'medium', 'Risk / Finance', 'Review NPL provisioning; confirm write-off criteria and recovery pipeline status.'), 'revenue_usd': ('high', 'medium', 'Sales', 'Revenue under target trajectory. Activate KAM recovery plan and prioritize quick-conversion opportunities.'), 'rotation_x': ('medium', 'medium', 'Operations', 'Reduce average term by 5–10 days on new originations. Prioritise faster-cycling segments.'), 'ce_6m_pct': ('high', 'medium', 'Collections', 'Audit 6M collection shortfall by KAM and debtor. Escalate top-5 lagging accounts.'), 'apr_pct_ann': ('medium', 'low', 'Pricing', 'Recalibrate APR corridor by segment/channel. Review floor exceptions and competitiveness trade-offs.'), 'dscr': ('high', 'medium', 'Finance / Risk', 'Improve debt-service coverage by tightening affordability policy and restructuring weak cash-flow profiles.')}
_NO_DATA_ACTION_MAP = {'apr_pct_ann': ('medium', 'low', 'Pricing', 'APR data unavailable. Complete APR field mapping in loan tape and backfill historical values for policy monitoring.'), 'dscr': ('high', 'medium', 'Finance / Risk', 'DSCR data unavailable. Integrate NOI and debt service fields from borrower financials to enable covenant monitoring.')}

def _plan_impact_rank(impact: str) -> int:
    return {'high': 0, 'medium': 1, 'low': 2}.get(impact.lower(), 3)

def _plan_is_stronger(candidate: dict[str, Any], current: dict[str, Any]) -> bool:
    cand_rank = _plan_impact_rank(candidate.get('impact', 'low'))
    curr_rank = _plan_impact_rank(current.get('impact', 'low'))
    if cand_rank != curr_rank:
        return cand_rank < curr_rank
    cand_var = candidate.get('variance')
    curr_var = current.get('variance')
    cand_mag = abs(float(cand_var)) if isinstance(cand_var, (int, float)) else 0.0
    curr_mag = abs(float(curr_var)) if isinstance(curr_var, (int, float)) else 0.0
    return cand_mag > curr_mag

def _canonical_plan_metric(metric: Any) -> str:
    metric_s = str(metric).strip().lower()
    return {'par30_pct': 'par30', 'par90_pct': 'par90', 'revenue_usd': 'revenue', 'apr_pct_ann': 'apr'}.get(metric_s, metric_s)

def _plan_policy_lookup(metric: Any, policy_map: dict[str, Any]) -> Any:
    metric_s = str(metric).strip().lower()
    if metric_s in policy_map:
        return policy_map[metric_s]
    canonical = _canonical_plan_metric(metric_s)
    if canonical in policy_map:
        return policy_map[canonical]
    fallback = {'par30': 'par30_pct', 'par90': 'par90_pct', 'revenue': 'revenue_usd', 'apr': 'apr_pct_ann'}.get(canonical)
    return policy_map.get(fallback) if fallback else None

def _compose_contextual_action(base_action: str, variance_details: dict[str, Any]) -> str:
    driver = variance_details.get('driver') if isinstance(variance_details, dict) else None
    explanation = variance_details.get('explanation') if isinstance(variance_details, dict) else None
    if driver:
        return f'{base_action} Driver: {driver}.'
    else:
        return f'{base_action} Context: {explanation}' if explanation else base_action

def _resolve_compliance_meta(status: str, metric_name: Any) -> tuple[Any, Any, Any]:
    if status in {'breach', 'warning'}:
        return (_plan_policy_lookup(metric_name, _IMPACT_MAP), 'compliance', 'variance')
    if status == 'no_data':
        return (_plan_policy_lookup(metric_name, _NO_DATA_ACTION_MAP), 'compliance', None)
    return (None, None, None)

def _build_compliance_action(row: dict[str, Any], variance_details: dict[str, Any]) -> dict[str, Any] | None:
    meta, source, variance_key = _resolve_compliance_meta(str(row.get('status', '')), row.get('metric'))
    if not meta or not source:
        return None
    impact, effort, area, action_text = meta
    variance_value = row.get('variance') if variance_key == 'variance' else None
    sort_value = row.get('variance', 0) if variance_key == 'variance' else 0
    return {'area': area, 'action': _compose_contextual_action(action_text, variance_details), 'impact': impact, 'effort': effort, 'source': source, 'metric': row.get('metric'), 'variance': variance_value, '_sort_key': (0 if impact == 'high' else 1, sort_value)}

def _load_compliance_actions(compliance: dict[str, Any], variance_decomp: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for row in compliance.get('metrics', []):
        metric_name = row.get('metric')
        variance_details = variance_decomp.get(metric_name, {}) if isinstance(variance_decomp, dict) else {}
        if action := _build_compliance_action(row, variance_details):
            actions.append(action)
    return actions

def _load_forecast_actions(forecast: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for kpi_name, forecast_key in [('PAR30', 'par30_forecast'), ('PAR90', 'par90_forecast'), ('Revenue', 'revenue_forecast')]:
        rows = forecast.get(forecast_key, [])
        if len(rows) < 2:
            continue
        first_val = rows[0].get('value', 0)
        last_val = rows[-1].get('value', 0)
        if kpi_name in ('PAR30', 'PAR90') and last_val > first_val * 1.1:
            actions.append({'area': 'Risk', 'action': f'{kpi_name} forecast rises {first_val:.1f}% → {last_val:.1f}% over {len(rows)} months. Pre-emptively tighten underwriting for high-DPD segments.', 'impact': 'high', 'effort': 'medium', 'source': 'forecast', 'metric': kpi_name.lower(), 'variance': round(last_val - first_val, 2), '_sort_key': (0, last_val - first_val)})
        elif kpi_name == 'Revenue' and last_val < first_val * 0.9:
            actions.append({'area': 'Sales', 'action': f'Revenue forecast declines ${first_val:,.0f} → ${last_val:,.0f}/month. Activate KAM pipeline review; prioritise upgrades in $50–150K bucket.', 'impact': 'high', 'effort': 'medium', 'source': 'forecast', 'metric': 'revenue', 'variance': round(last_val - first_val, 2), '_sort_key': (0, first_val - last_val)})
    return actions

def _load_outlier_actions(outlier_alerts: list[dict] | None) -> list[dict[str, Any]]:
    if not outlier_alerts:
        return []
    total_flagged_bal = sum((a.get('outstanding_usd', 0) for a in outlier_alerts[:20]))
    top_var = outlier_alerts[0].get('variable', 'unknown')
    return [{'area': 'Risk', 'action': f'{len(outlier_alerts)} exposure-weighted outliers flagged (total ${total_flagged_bal:,.0f} outstanding). Top anomaly variable: {top_var}. Review weekly watchlist in CRO pack.', 'impact': 'medium', 'effort': 'low', 'source': 'outlier', 'metric': 'outlier_detection', 'variance': None, '_sort_key': (1, -total_flagged_bal)}]

def _load_pd_model_actions(pd_result: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not (pd_result and pd_result.get('status') == 'ok'):
        return []
    if top_pd := [r for r in pd_result.get('pd_scores', []) if r['pd_score'] >= 0.5]:
        return [{'area': 'Credit', 'action': f"PD model identifies {len(top_pd)} loans with PD >= 50% (AUC {pd_result.get('auc_mean', 0):.3f}). Flag for enhanced monitoring, provisioning review, and collections escalation.", 'impact': 'high', 'effort': 'low', 'source': 'pd_model', 'metric': 'probability_of_default', 'variance': None, '_sort_key': (0, -len(top_pd))}]
    return []

def _merge_plan_actions(candidate: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    primary = candidate if _plan_is_stronger(candidate, current) else current
    secondary = current if primary is candidate else candidate
    if secondary.get('action') and secondary['action'] not in primary.get('action', ''):
        primary['action'] = f"{primary['action']} Additional context: {secondary['action']}"
    primary_sources = {source.strip() for source in str(primary.get('source', '')).split('+') if source.strip()}
    secondary_sources = {source.strip() for source in str(secondary.get('source', '')).split('+') if source.strip()}
    primary['source'] = '+'.join(sorted(primary_sources | secondary_sources)) or 'compliance'
    if primary.get('variance') is None and secondary.get('variance') is not None:
        primary['variance'] = secondary.get('variance')
    return primary

def _consolidate_plan_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    consolidated: dict[str, dict[str, Any]] = {}
    passthrough: list[dict[str, Any]] = []
    for action in actions:
        metric = action.get('metric')
        if metric is None:
            passthrough.append(action)
            continue
        key = _canonical_plan_metric(metric)
        current = consolidated.get(key)
        if current is None:
            consolidated[key] = action
            continue
        consolidated[key] = _merge_plan_actions(action, current)
    return passthrough + list(consolidated.values())

def build_next_steps_plan(forecast: dict[str, Any], compliance: dict[str, Any], outlier_alerts: list[dict] | None=None, pd_result: dict[str, Any] | None=None) -> dict[str, Any]:
    variance_decomp = compliance.get('variance_decomposition', {})
    actions = _load_compliance_actions(compliance, variance_decomp) + _load_forecast_actions(forecast) + _load_outlier_actions(outlier_alerts) + _load_pd_model_actions(pd_result)
    actions = _consolidate_plan_actions(actions)
    actions.sort(key=lambda x: x.pop('_sort_key', (9, 0)))
    for i, action in enumerate(actions, 1):
        action['priority'] = i
    return {'generated_at': datetime.now(timezone.utc).isoformat(), 'action_count': len(actions), 'actions': actions, 'sources_used': list({a['source'] for a in actions})}
