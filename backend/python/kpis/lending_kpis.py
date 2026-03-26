from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any, cast
import numpy as np
import pandas as pd
logger = logging.getLogger(__name__)

def _col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None

def _num(df: pd.DataFrame, col: str) -> pd.Series:
    res = pd.to_numeric(df[col], errors='coerce')
    if res.isna().any():
        logger.warning('Column %s has %d missing or invalid numeric values - excluding from KPI calculation', col, res.isna().sum())
        return res.dropna()
    return res

def _resolve_lgd_config() -> float:
    try:
        from backend.python.config import settings
        return settings.risk.loss_given_default
    except Exception:
        return 0.1

def _merge_customer_segments(loans_df: pd.DataFrame, customer_df: pd.DataFrame | None, loan_id: str | None) -> pd.DataFrame:
    df = loans_df.copy()
    if customer_df is None or loan_id is None or loan_id not in customer_df.columns:
        return df
    cat_col = _col(customer_df, ['categorialineacredito'])
    clt_col = _col(customer_df, ['client_type'])
    if cat_col:
        df = df.merge(customer_df[[loan_id, cat_col]].drop_duplicates(loan_id), on=loan_id, how='left')
    if clt_col and clt_col not in df.columns:
        df = df.merge(customer_df[[loan_id, clt_col]].drop_duplicates(loan_id), on=loan_id, how='left')
    return df

def _segment_summary(df: pd.DataFrame, group_col: str | None, lgd: float) -> list[dict[str, Any]]:
    if not group_col or group_col not in df.columns:
        return []
    rows = []
    for seg, grp in df.groupby(group_col, dropna=False):
        balance = float(grp['_bal'].sum())
        ecl = float(grp['_ecl'].sum())
        rows.append({'segment': str(seg), 'outstanding_usd': round(balance, 2), 'ecl_usd': round(ecl, 2), 'ecl_coverage_pct': round(ecl / max(balance, 1) * 100, 2), 'default_count': int(grp['_default'].sum()), 'pd_avg': round(float(grp['_pd'].mean()), 4), 'lgd': lgd})
    return sorted(rows, key=lambda row: row['ecl_usd'], reverse=True)

def _build_mype_agg_dict(cust_col: str, bal_col: str | None, dpd_col: str | None, disb_col: str | None, tpv_col: str | None) -> dict[str, Any]:
    agg_dict: dict[str, Any] = {'n_default': ('_default', 'sum'), 'n_loans': (cust_col, 'count')}
    if bal_col:
        agg_dict['outstanding'] = (bal_col, 'sum')
    if dpd_col:
        agg_dict['max_dpd'] = (dpd_col, 'max')
    if disb_col:
        agg_dict['total_disb'] = (disb_col, 'sum')
    if tpv_col:
        agg_dict['total_tpv'] = (tpv_col, 'sum')
    return agg_dict

def _build_collection_map(payments_df: pd.DataFrame | None) -> dict[str, float]:
    if payments_df is None:
        return {}
    pay_cust = _col(payments_df, ['customer_id'])
    pay_amt = _col(payments_df, ['true_total_payment'])
    if not (pay_cust and pay_amt):
        return {}
    return payments_df.groupby(pay_cust)[pay_amt].apply(lambda s: pd.to_numeric(s, errors='coerce').sum()).to_dict()

def _classify_mype_decision(pod: float, max_dpd: float, npl_ratio: float) -> tuple[str, str]:
    if pod >= 0.75 or max_dpd >= 90:
        return ('CRITICAL', 'DECLINE')
    if pod >= 0.5 or npl_ratio >= 0.05:
        return ('HIGH', 'REVIEW')
    if pod >= 0.25 or npl_ratio >= 0.03:
        return ('MEDIUM', 'REVIEW')
    return ('LOW', 'APPROVE')

def _build_mype_decision_row(row: pd.Series, cust_col: str, ce_map: dict[str, float]) -> dict[str, float | str]:
    cid = str(row[cust_col])
    outstanding = float(row.get('outstanding', 0))
    max_dpd = float(row.get('max_dpd', 0))
    n_loans = int(row.get('n_loans', 1))
    n_default = int(row.get('n_default', 0))
    total_disb = float(row.get('total_disb', 0))
    total_recv = float(ce_map.get(cid, 0))
    npl_ratio = n_default / max(n_loans, 1)
    collection_rate = total_recv / max(total_disb, 1) if total_disb > 0 else 1.0
    pod = min(1.0, max_dpd / 90 * 0.8 + npl_ratio * 0.2)
    risk, decision = _classify_mype_decision(pod, max_dpd, npl_ratio)
    return {'customer_id': cid, 'decision': decision, 'risk_level': risk, 'pod': round(pod, 4), 'max_dpd': round(max_dpd, 0), 'npl_ratio': round(npl_ratio, 3), 'collection_rate': round(min(collection_rate, 1.0), 3), 'outstanding_usd': round(outstanding, 2)}

def cdr_by_cohort(loans_df: pd.DataFrame) -> dict[str, Any]:
    disb_col = _col(loans_df, ['disbursement_date', 'FechaDesembolso'])
    disb_amt = _col(loans_df, ['disbursement_amount', 'MontoDesembolsado'])
    status_col = _col(loans_df, ['loan_status', 'Loan Status'])
    bal_col = _col(loans_df, ['outstanding_loan_value', 'outstanding_balance'])
    if not disb_col or not status_col:
        return {'status': 'missing_columns'}
    df = loans_df.copy()
    df['_date'] = pd.to_datetime(df[disb_col], errors='coerce')
    df['_cohort'] = df['_date'].dt.to_period('M')
    df['_disb'] = _num(df, disb_amt) if disb_amt else pd.Series(1.0, index=df.index)
    df['_bal'] = _num(df, bal_col) if bal_col else df['_disb']
    df['_default'] = df[status_col].astype(str).str.lower().str.contains('default', na=False)
    total_disb = df['_disb'].sum()
    default_disb = df[df['_default']]['_disb'].sum()
    portfolio_cdr = float(default_disb / max(total_disb, 1) * 100)
    by_cohort: list[dict[str, float | int | str]] = []
    for cohort, grp in df.groupby('_cohort'):
        orig = float(grp['_disb'].sum())
        defs = float(grp.loc[grp['_default'], '_disb'].sum())
        by_cohort.append({'cohort': str(cohort), 'originations_usd': round(orig, 2), 'defaults_usd': round(defs, 2), 'cdr_pct': round(defs / max(orig, 1) * 100, 2), 'default_count': int(grp['_default'].sum())})
    by_cohort.sort(key=lambda x: str(x['cohort']))
    trend: dict[str, Any] = {}
    if len(by_cohort) >= 6:
        latest3 = [float(cast(float, r['cdr_pct'])) for r in by_cohort[-3:] if float(cast(float, r['originations_usd'])) > 0]
        prev3 = [float(cast(float, r['cdr_pct'])) for r in by_cohort[-6:-3] if float(cast(float, r['originations_usd'])) > 0]
        if latest3 and prev3:
            l_avg = round(float(np.mean(latest3)), 2)
            p_avg = round(float(np.mean(prev3)), 2)
            trend = {'latest_3m_avg_cdr': l_avg, 'prev_3m_avg_cdr': p_avg, 'direction': 'deteriorating' if l_avg > p_avg else 'improving', 'change_pp': round(l_avg - p_avg, 2)}
    return {'status': 'ok', 'portfolio_cdr_pct': round(portfolio_cdr, 2), 'default_count': int(df['_default'].sum()), 'default_balance_usd': round(float(df.loc[df['_default'], '_bal'].sum()), 2), 'total_originations_usd': round(float(total_disb), 2), 'by_cohort': by_cohort, 'trend': trend}

def liquidation_rate(loans_df: pd.DataFrame, payments_df: pd.DataFrame | None=None) -> dict[str, Any]:
    status_col = _col(loans_df, ['loan_status'])
    bal_col = _col(loans_df, ['outstanding_loan_value'])
    rec_col = _col(loans_df, ['recovery_value', 'recovery_amount'])
    loan_id_col = _col(loans_df, ['loan_id'])
    df = loans_df.copy()
    df['_default'] = df[status_col].astype(str).str.lower().str.contains('default', na=False) if status_col else False
    df['_bal'] = _num(df, bal_col) if bal_col else pd.Series(0.0, index=df.index)
    df['_rec'] = _num(df, rec_col) if rec_col else pd.Series(0.0, index=df.index)
    default_bal = float(df.loc[df['_default'], '_bal'].sum())
    recovery_val = float(df.loc[df['_default'], '_rec'].sum())
    if recovery_val == 0 and payments_df is not None and loan_id_col:
        default_loan_ids = set(df.loc[df['_default'], loan_id_col].astype(str))
        pay_lid = _col(payments_df, ['loan_id'])
        pay_amt = _col(payments_df, ['true_total_payment', 'true_principal_payment'])
        if pay_lid and pay_amt:
            post_default_pay = payments_df[payments_df[pay_lid].astype(str).isin(default_loan_ids)]
            recovery_val = float(_num(post_default_pay, pay_amt).sum())
    liquidation_pct = float(recovery_val / max(default_bal, 1) * 100)
    lgd_pct = 100.0 - liquidation_pct
    if rec_col and _num(df, rec_col).sum() > 0:
        data_quality = 'direct'
    elif recovery_val > 0:
        data_quality = 'proxy_from_payments'
    else:
        data_quality = 'no_recovery_data'
    return {'status': 'ok', 'default_balance_usd': round(default_bal, 2), 'recovery_usd': round(recovery_val, 2), 'liquidation_rate_pct': round(liquidation_pct, 2), 'lgd_pct': round(lgd_pct, 2), 'data_quality': data_quality, 'note': 'recovery_value column is all zeros - enter actual recovery amounts in loan tape to get real liquidation rate.' if recovery_val == 0 else ''}

def lgd_ecl_by_segment(loans_df: pd.DataFrame, customer_df: pd.DataFrame | None=None, lgd_override: float | None=None) -> dict[str, Any]:
    lgd = lgd_override if lgd_override is not None else _resolve_lgd_config()
    loan_id = _col(loans_df, ['loan_id'])
    bal_col = _col(loans_df, ['outstanding_loan_value'])
    dpd_col = _col(loans_df, ['days_in_default', 'dpd'])
    disb_col = _col(loans_df, ['disbursement_amount'])
    stat_col = _col(loans_df, ['loan_status'])
    df = _merge_customer_segments(loans_df, customer_df, loan_id)
    df['_bal'] = _num(df, bal_col) if bal_col else pd.Series(1.0, index=df.index)
    df['_dpd'] = _num(df, dpd_col) if dpd_col else pd.Series(0.0, index=df.index)
    df['_disb'] = _num(df, disb_col) if disb_col else df['_bal']
    df['_default'] = df[stat_col].astype(str).str.lower().str.contains('default', na=False) if stat_col else False
    df['_pd'] = (df['_dpd'] / 180).clip(upper=1.0)
    df['_ecl'] = df['_pd'] * lgd * df['_bal']
    portfolio_ecl = float(df['_ecl'].sum())
    total_bal = float(df['_bal'].sum())
    ecl_coverage_pct = portfolio_ecl / max(total_bal, 1) * 100
    cat_col = _col(df, ['categorialineacredito'])
    clt_col = _col(df, ['client_type'])
    return {'status': 'ok', 'portfolio_ecl_usd': round(portfolio_ecl, 2), 'total_outstanding_usd': round(total_bal, 2), 'ecl_coverage_pct': round(ecl_coverage_pct, 2), 'lgd_used': lgd, 'pd_method': 'dpd/180 proxy (replace with model scores for precision)', 'by_credit_line_cat': _segment_summary(df, cat_col, lgd), 'by_client_type': _segment_summary(df, clt_col, lgd)}

def balance_sheet_proxy(loans_df: pd.DataFrame, payments_df: pd.DataFrame, monthly_opex_usd: float=50000.0) -> dict[str, Any]:
    disb_amt = _col(loans_df, ['disbursement_amount'])
    bal_col = _col(loans_df, ['outstanding_loan_value'])
    pay_date = _col(payments_df, ['true_payment_date'])
    pay_prin = _col(payments_df, ['true_principal_payment'])
    pay_int = _col(payments_df, ['true_interest_payment'])
    pay_fee = _col(payments_df, ['true_fee_payment'])
    pay_tax = _col(payments_df, ['true_tax_payment'])
    total_outstanding = float(_num(loans_df, bal_col).sum()) if bal_col else 0.0
    total_disbursed = float(_num(loans_df, disb_amt).sum()) if disb_amt else 0.0
    total_principal_recv = float(_num(payments_df, pay_prin).sum()) if pay_prin else 0.0
    total_interest_recv = float(_num(payments_df, pay_int).sum()) if pay_int else 0.0
    total_fees_recv = float(_num(payments_df, pay_fee).sum()) if pay_fee else 0.0
    total_tax_recv = float(_num(payments_df, pay_tax).sum()) if pay_tax else 0.0
    total_revenue = total_interest_recv + total_fees_recv - total_tax_recv
    monthly_rev = 0.0
    if pay_date and pay_int:
        pay_df = payments_df.copy()
        pay_df['_month'] = pd.to_datetime(pay_df[pay_date], errors='coerce').dt.to_period('M')
        pay_df['_rev'] = _num(pay_df, pay_int) + (_num(pay_df, pay_fee) if pay_fee else 0)
        latest = pay_df['_month'].max()
        monthly_rev = float(pay_df[pay_df['_month'] == latest]['_rev'].sum())
    arr_usd = monthly_rev * 12
    runway_months = arr_usd / max(monthly_opex_usd * 12, 1) * 12
    return {'status': 'ok', 'assets': {'loan_book_outstanding_usd': round(total_outstanding, 2), 'total_disbursed_all_time': round(total_disbursed, 2), 'cash_balance_usd': 'NOT_AVAILABLE - needs debt schedule / bank feed'}, 'liabilities': {'total_liabilities_usd': 'NOT_AVAILABLE - needs external debt/funding data', 'note': 'Add funding lines and warehouse facility to get actual leverage'}, 'income_statement': {'total_revenue_collected_usd': round(total_revenue, 2), 'total_principal_collected_usd': round(total_principal_recv, 2), 'latest_month_revenue_usd': round(monthly_rev, 2), 'arr_estimate_usd': round(arr_usd, 2), 'monthly_opex_assumption_usd': monthly_opex_usd, 'net_income_estimate_usd': round(monthly_rev - monthly_opex_usd, 2), 'runway_months_estimate': round(runway_months, 1), 'runway_note': f'Based on opex ${monthly_opex_usd:,.0f}/mo. Update monthly_opex_usd param.'}, 'data_gaps': ['Cash balance: requires bank feed or EEFF (only 1 week available)', 'Debt/equity: requires funding structure data', 'Debt-to-equity ratio: NOT_COMPUTABLE without liabilities']}

def approval_metrics(customer_df: pd.DataFrame) -> dict[str, Any]:
    app_status_col = _col(customer_df, ['application_status'])
    chan_col = _col(customer_df, ['sales_channel'])
    if app_status_col:
        statuses = customer_df[app_status_col].value_counts().to_dict()
        total = len(customer_df)
        approved = int(customer_df[app_status_col].astype(str).str.lower().str.contains('approv', na=False).sum())
        declined = int(customer_df[app_status_col].astype(str).str.lower().str.contains('declin|reject', na=False).sum())
        auto_dec = int(customer_df[app_status_col].astype(str).str.lower().str.contains('auto', na=False).sum())
    else:
        statuses = {}
        total = len(customer_df)
        approved = declined = auto_dec = 0
    by_channel: list[dict[str, Any]] = []
    if chan_col:
        for ch, grp in customer_df.groupby(chan_col, dropna=False):
            app_in_ch = len(grp)
            appr_in_ch = int(grp[app_status_col].astype(str).str.lower().str.contains('approv', na=False).sum()) if app_status_col else app_in_ch
            by_channel.append({'channel': str(ch), 'applications': app_in_ch, 'approved': appr_in_ch, 'approval_rate_pct': round(appr_in_ch / max(app_in_ch, 1) * 100, 1)})
    return {'status': 'ok', 'total_applications': total, 'approved': approved, 'declined': declined, 'approval_rate_pct': round(approved / max(total, 1) * 100, 1), 'auto_decision_rate_pct': round(auto_dec / max(total, 1) * 100, 1), 'application_statuses': statuses, 'by_channel': by_channel, 'data_quality_note': 'loan tape only contains funded loans - true approval rate requires application log including rejected apps. Integrate with origination system / Taktile decision logs.', 'thresholds': {'approval_rate_amber': 40.0, 'approval_rate_red': 35.0, 'auto_decision_amber': 70.0}}

def cure_rate_by_period(payments_df: pd.DataFrame) -> dict[str, Any]:
    cust_col = _col(payments_df, ['customer_id', 'CodCliente'])
    stat_col = _col(payments_df, ['true_payment_status'])
    date_col = _col(payments_df, ['true_payment_date'])
    if not cust_col or not stat_col or (not date_col):
        return {'status': 'missing_columns'}
    pay = payments_df.copy()
    pay['_date'] = pd.to_datetime(pay[date_col], errors='coerce')
    pay['_month'] = pay['_date'].dt.to_period('M')
    pay['_status'] = pay[stat_col].astype(str).str.strip()
    pay = pay.sort_values([cust_col, '_date'])
    pay['_prev'] = pay.groupby(cust_col)['_status'].shift(1)
    cured_mask = (pay['_prev'] == 'Late') & pay['_status'].isin(['On Time', 'Prepayment'])
    all_late = pay['_status'] == 'Late'
    monthly_rows = []
    for month, grp in pay.groupby('_month'):
        late_in_month = int((grp['_status'] == 'Late').sum())
        cured_in_month = int(cured_mask[grp.index].sum())
        if late_in_month > 0:
            monthly_rows.append({'month': str(month), 'late_count': late_in_month, 'cured_count': cured_in_month, 'cure_rate_pct': round(cured_in_month / late_in_month * 100, 1)})
    total_late = int(all_late.sum())
    total_cured = int(cured_mask.sum())
    return {'status': 'ok', 'total_late_events': total_late, 'total_cured_events': total_cured, 'portfolio_cure_rate_pct': round(total_cured / max(total_late, 1) * 100, 1), 'monthly_cure_rates': monthly_rows, 'method': 'Late->(OnTime|Prepayment) consecutive payment transition', 'threshold': {'red_below_pp': 3, 'note': 'Red if cure_rate drops 3pp below rolling 3-month baseline'}}

def promise_to_pay_metrics(payments_df: pd.DataFrame) -> dict[str, Any]:
    cust_col = _col(payments_df, ['customer_id'])
    stat_col = _col(payments_df, ['true_payment_status'])
    date_col = _col(payments_df, ['true_payment_date'])
    amt_col = _col(payments_df, ['true_total_payment'])
    if not cust_col or not stat_col:
        return {'status': 'missing_columns'}
    pay = payments_df.copy()
    pay['_date'] = pd.to_datetime(pay[date_col], errors='coerce') if date_col else pd.NaT
    pay['_status'] = pay[stat_col].astype(str).str.strip()
    pay['_amt'] = _num(pay, amt_col) if amt_col else pd.Series(1.0, index=pay.index)
    pay = pay.sort_values([cust_col, '_date'])
    pay['_prev'] = pay.groupby(cust_col)['_status'].shift(1)
    kept_mask = (pay['_prev'] == 'Late') & pay['_status'].isin(['On Time', 'Prepayment'])
    broken_mask = (pay['_prev'] == 'Late') & (pay['_status'] == 'Late')
    total_late = int((pay['_status'] == 'Late').sum())
    kept = int(kept_mask.sum())
    broken = int(broken_mask.sum())
    amt_kept = float(pay.loc[kept_mask, '_amt'].sum())
    amt_broken = float(pay.loc[broken_mask, '_amt'].sum())
    return {'status': 'ok', 'total_late_events': total_late, 'ptp_kept_proxy': kept, 'ptp_broken_proxy': broken, 'ptp_kept_rate_pct': round(kept / max(total_late, 1) * 100, 1), 'amount_kept_usd': round(amt_kept, 2), 'amount_broken_usd': round(amt_broken, 2), 'data_quality': 'proxy', 'note': 'True PTP requires dedicated PTP log (promise date + amount). Integrate collections system to log actual promises.', 'thresholds': {'red_below_pct': 80.0, 'note': 'Red if PTP kept rate < 80%'}}

def mype_approval_batch(loans_df: pd.DataFrame, payments_df: pd.DataFrame | None=None) -> dict[str, Any]:
    cust_col = _col(loans_df, ['customer_id'])
    bal_col = _col(loans_df, ['outstanding_loan_value'])
    dpd_col = _col(loans_df, ['days_in_default', 'dpd'])
    disb_col = _col(loans_df, ['disbursement_amount'])
    tpv_col = _col(loans_df, ['tpv'])
    stat_col = _col(loans_df, ['loan_status'])
    if not cust_col:
        return {'status': 'missing_columns'}
    df = loans_df.copy()
    for c in [bal_col, dpd_col, disb_col, tpv_col]:
        if c:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    df['_default'] = df[stat_col].astype(str).str.lower().str.contains('default', na=False) if stat_col else False
    clients = df.groupby(cust_col).agg(**_build_mype_agg_dict(cust_col, bal_col, dpd_col, disb_col, tpv_col)).reset_index()
    ce_map = _build_collection_map(payments_df)
    decisions: list[dict[str, float | str]] = []
    counts = {'APPROVE': 0, 'REVIEW': 0, 'DECLINE': 0}
    for _, row in clients.iterrows():
        decision_row = _build_mype_decision_row(row, cust_col, ce_map)
        decision = str(decision_row['decision'])
        counts[decision] += 1
        decisions.append(decision_row)
    decisions.sort(key=lambda x: float(cast(float, x['pod'])), reverse=True)
    return {'status': 'ok', 'total_clients': len(decisions), 'summary': counts, 'approve_rate_pct': round(counts['APPROVE'] / max(len(decisions), 1) * 100, 1), 'high_risk_balance_usd': round(sum((float(cast(float, d['outstanding_usd'])) for d in decisions if str(cast(str, d['risk_level'])) in ('HIGH', 'CRITICAL'))), 2), 'decisions': decisions[:100], 'data_gaps': ['utilization = 0 (LineaCredito not in loan_data.csv)', 'collection_rate = proxy from disbursement (needs payment_schedule)']}

def cash_balance_treasury(
    cash_balance_usd: float,
    pending_disbursements_usd: float = 0.0,
    loans_df: pd.DataFrame | None = None,
    avg_portfolio_apr: float | None = None,
    reserve_ratio: float = 0.10,
) -> dict[str, Any]:
    """Daily cash position, disbursement capacity, and opportunity cost.

    Parameters
    ----------
    cash_balance_usd:
        Total cash available in bank accounts today (manual daily entry).
    pending_disbursements_usd:
        Approved loans approved but not yet funded (sitting in the pipeline).
    loans_df:
        Loan tape used to derive weighted-average APR when avg_portfolio_apr is None.
    avg_portfolio_apr:
        Override for portfolio APR (e.g. 0.28 for 28%).  Calculated from loans_df
        if not supplied.
    reserve_ratio:
        Fraction of cash held in reserve (not deployable).  Default 10%.
    """
    # --- derive APR from loan tape when not provided ---
    if avg_portfolio_apr is None and loans_df is not None:
        apr_col = _col(loans_df, ['interest_rate_apr', 'APR'])
        if apr_col:
            avg_portfolio_apr = float(_num(loans_df, apr_col).mean())
    if avg_portfolio_apr is None:
        avg_portfolio_apr = 0.28  # conservative LatAm fintech default

    reserve_usd = cash_balance_usd * reserve_ratio
    available_to_disburse_usd = max(cash_balance_usd - reserve_usd - pending_disbursements_usd, 0.0)
    idle_cash_usd = max(cash_balance_usd - reserve_usd - pending_disbursements_usd, 0.0)

    # --- opportunity cost: money sitting in bank vs deployed in loans ---
    daily_rate = avg_portfolio_apr / 365.0
    opp_cost_idle_daily_usd = idle_cash_usd * daily_rate
    opp_cost_idle_monthly_usd = idle_cash_usd * (avg_portfolio_apr / 12.0)

    # --- opportunity cost of pending disbursements not yet funded ---
    opp_cost_pending_daily_usd = pending_disbursements_usd * daily_rate
    opp_cost_pending_monthly_usd = pending_disbursements_usd * (avg_portfolio_apr / 12.0)

    # --- utilisation ---
    aum_usd = 0.0
    if loans_df is not None:
        bal_col = _col(loans_df, ['outstanding_loan_value', 'outstanding_balance'])
        if bal_col:
            aum_usd = float(_num(loans_df, bal_col).sum())

    total_deployable_capital = aum_usd + cash_balance_usd
    utilisation_rate_pct = round(aum_usd / max(total_deployable_capital, 1) * 100, 1)

    # --- alerts ---
    alerts: list[str] = []
    if idle_cash_usd > 50_000:
        alerts.append(f'HIGH_IDLE_CASH: ${idle_cash_usd:,.0f} sitting undeployed — opportunity cost ${opp_cost_idle_monthly_usd:,.0f}/mo')
    if pending_disbursements_usd > cash_balance_usd * 0.5:
        alerts.append(f'PIPELINE_EXCEEDS_50PCT_CASH: ${pending_disbursements_usd:,.0f} pending vs ${cash_balance_usd:,.0f} available')
    if available_to_disburse_usd == 0 and pending_disbursements_usd > 0:
        alerts.append('INSUFFICIENT_CASH: pending disbursements exceed deployable cash — funding gap detected')
    if utilisation_rate_pct < 70:
        alerts.append(f'LOW_UTILISATION: {utilisation_rate_pct}% — AUM/Capital ratio below 70% target')

    return {
        'status': 'ok',
        'as_of': datetime.now(timezone.utc).date().isoformat(),
        'inputs': {
            'cash_balance_usd': round(cash_balance_usd, 2),
            'pending_disbursements_usd': round(pending_disbursements_usd, 2),
            'reserve_ratio_pct': round(reserve_ratio * 100, 1),
            'avg_portfolio_apr': round(avg_portfolio_apr, 4),
        },
        'capacity': {
            'reserve_held_usd': round(reserve_usd, 2),
            'available_to_disburse_usd': round(available_to_disburse_usd, 2),
            'aum_deployed_usd': round(aum_usd, 2),
            'utilisation_rate_pct': utilisation_rate_pct,
        },
        'opportunity_cost': {
            'idle_cash_usd': round(idle_cash_usd, 2),
            'opp_cost_idle_daily_usd': round(opp_cost_idle_daily_usd, 2),
            'opp_cost_idle_monthly_usd': round(opp_cost_idle_monthly_usd, 2),
            'pending_dis_opp_cost_daily_usd': round(opp_cost_pending_daily_usd, 2),
            'pending_dis_opp_cost_monthly_usd': round(opp_cost_pending_monthly_usd, 2),
            'total_monthly_opp_cost_usd': round(opp_cost_idle_monthly_usd + opp_cost_pending_monthly_usd, 2),
        },
        'alerts': alerts,
        'note': (
            'cash_balance_usd is a required DAILY MANUAL INPUT from bank accounts. '
            'Integrate bank feed (Belvo/Plaid) to automate. '
            'pending_disbursements_usd = sum of approved-not-yet-funded loans from origination system.'
        ),
    }


def collection_efficiency_6m(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame | None = None,
    window_days: int = 180,
    target_ce: float | None = None,
) -> dict[str, Any]:
    """CE 6M proxy using due_date / fechapagoprogramado from the loan tape."""
    if target_ce is None:
        try:
            from backend.python.config import settings
            target_ce = settings.guardrails.min_ce_6m
        except Exception:
            target_ce = 0.96

    due_col = _col(loans_df, ['due_date', 'fechapagoprogramado', 'fecha_vencimiento', 'fecha_de_vencimiento'])
    bal_col = _col(loans_df, ['outstanding_loan_value', 'principal_amount', 'disbursement_amount'])
    cap_col = _col(loans_df, ['capital_collected', 'capitalcobrado'])
    loan_id_col = _col(loans_df, ['loan_id'])

    if due_col is None or bal_col is None:
        return {
            'status': 'insufficient_data',
            'ce_6m_pct': None,
            'target_ce_pct': round(target_ce * 100, 1),
            'note': 'Requires due_date (fechapagoprogramado) and outstanding_loan_value columns.',
        }

    df = loans_df.copy()
    df['_due'] = pd.to_datetime(df[due_col], errors='coerce')
    df['_bal'] = pd.to_numeric(df[bal_col], errors='coerce').fillna(0)

    today = pd.Timestamp.now()
    cutoff = today - pd.Timedelta(days=window_days)
    window_df = df[(df['_due'] >= cutoff) & (df['_due'] <= today)].copy()

    if window_df.empty:
        return {
            'status': 'no_loans_in_window',
            'ce_6m_pct': None,
            'target_ce_pct': round(target_ce * 100, 1),
            'window_days': window_days,
            'note': f'No loans with due_date between {cutoff.date()} and {today.date()}.',
        }

    scheduled_usd = float(window_df['_bal'].sum())
    collected_usd = 0.0
    data_source = 'no_payment_data'

    # Method 1: direct capital_collected column on the loan tape
    if cap_col and cap_col in window_df.columns:
        window_df['_cap'] = pd.to_numeric(window_df[cap_col], errors='coerce').fillna(0)
        collected_usd = float(window_df['_cap'].sum())
        if collected_usd > 0:
            data_source = 'direct_capital_collected'

    # Method 2: match payments_df by loan_id for loans in the window
    if collected_usd == 0 and payments_df is not None and loan_id_col:
        pay_lid = _col(payments_df, ['loan_id'])
        pay_amt = _col(payments_df, ['true_principal_payment', 'true_total_payment'])
        pay_date_col = _col(payments_df, ['true_payment_date'])
        if pay_lid and pay_amt:
            window_ids = set(window_df[loan_id_col].astype(str))
            flt = payments_df[payments_df[pay_lid].astype(str).isin(window_ids)].copy()
            if pay_date_col:
                flt['_pdate'] = pd.to_datetime(flt[pay_date_col], errors='coerce')
                flt = flt[(flt['_pdate'] >= cutoff) & (flt['_pdate'] <= today)]
            collected_usd = float(pd.to_numeric(flt[pay_amt], errors='coerce').fillna(0).sum())
            if collected_usd > 0:
                data_source = 'payments_df_principal'

    ce_6m = collected_usd / max(scheduled_usd, 1)
    breach = ce_6m < target_ce

    return {
        'status': 'ok',
        'ce_6m_pct': round(ce_6m * 100, 2),
        'target_ce_pct': round(target_ce * 100, 1),
        'breach': breach,
        'scheduled_usd': round(scheduled_usd, 2),
        'collected_usd': round(collected_usd, 2),
        'gap_usd': round(max(scheduled_usd * target_ce - collected_usd, 0), 2),
        'loans_in_window': int(len(window_df)),
        'window_days': window_days,
        'data_source': data_source,
        'note': (
            'Uses due_date / fechapagoprogramado as scheduled payment proxy. '
            f'Target CE {round(target_ce * 100, 1)}% from business_parameters.yml (min_ce_6m).'
        ),
    }


def sla_targets(loans_df: pd.DataFrame | None = None) -> dict[str, Any]:
    """
    SLA Decisión / Fondeo — targets from business_parameters.yml.

    Without per-loan origination timestamps the metric runs in *target mode*
    and shows the committed SLA goals.  If the loan tape contains both
    application_date and disbursement_date the function also computes a proxy
    median tap-to-fund time.
    """
    try:
        from backend.python.config import settings
        decision_hrs = settings.sla.decision_sla_hours
        funding_hrs = settings.sla.funding_sla_hours
        compliance_target = settings.sla.sla_compliance_target
    except Exception:
        decision_hrs = 24
        funding_hrs = 48
        compliance_target = 0.90

    actual_median_hrs: float | None = None
    data_source = 'target_only'

    if loans_df is not None:
        app_col = _col(loans_df, ['application_date', 'fechasolicitado'])
        orig_col = _col(loans_df, ['origination_date', 'disbursement_date', 'fechadesembolso'])
        if app_col and orig_col:
            tmp = loans_df.copy()
            tmp['_app'] = pd.to_datetime(tmp[app_col], errors='coerce')
            tmp['_orig'] = pd.to_datetime(tmp[orig_col], errors='coerce')
            tmp['_hrs'] = (tmp['_orig'] - tmp['_app']).dt.total_seconds() / 3600
            valid = tmp['_hrs'].dropna()
            positive = valid[valid > 0]
            if len(positive) > 0:
                actual_median_hrs = round(float(positive.median()), 1)
                data_source = 'proxy_app_to_disbursement'

    result: dict[str, Any] = {
        'status': 'ok',
        'targets': {
            'decision_sla_hours': decision_hrs,
            'funding_sla_hours': funding_hrs,
            'compliance_rate_target_pct': round(compliance_target * 100, 1),
        },
        'data_source': data_source,
        'note': (
            'Full SLA tracking requires per-loan application_date + approval_date + disbursement_date '
            'from the origination system. Add those columns to unlock actual compliance measurement.'
        ),
    }
    if actual_median_hrs is not None:
        result['actual'] = {
            'median_app_to_disbursement_hours': actual_median_hrs,
            'within_funding_target': actual_median_hrs <= funding_hrs,
        }
    return result


def financing_rate_eir(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """
    Tasa de Financiamiento / EIR — rate charged BY Abaco TO clients.

    Weighted-average APR on the active portfolio (weighted by outstanding
    balance).  This is the client-facing EIR, not Abaco's cost of funding.
    """
    apr_col = _col(loans_df, ['interest_rate_apr', 'interest_rate', 'TasaInteres', 'fee_rate'])
    bal_col = _col(loans_df, ['outstanding_loan_value', 'outstanding_balance', 'principal_amount'])

    if apr_col is None:
        return {
            'status': 'insufficient_data',
            'weighted_apr_pct': None,
            'note': 'Requires interest_rate_apr column in loan tape.',
        }

    df = loans_df.copy()
    df['_apr'] = pd.to_numeric(df[apr_col], errors='coerce')
    df = df[df['_apr'].notna() & (df['_apr'] > 0)].copy()

    if df.empty:
        return {
            'status': 'no_valid_rates',
            'weighted_apr_pct': None,
            'note': f'Column {apr_col} found but all values are zero or null.',
        }

    total_bal = 0.0
    if bal_col:
        df['_bal'] = pd.to_numeric(df[bal_col], errors='coerce').fillna(0)
        total_bal = float(df['_bal'].sum())
        weighted_apr = (
            float((df['_apr'] * df['_bal']).sum() / total_bal)
            if total_bal > 0
            else float(df['_apr'].mean())
        )
    else:
        weighted_apr = float(df['_apr'].mean())

    try:
        from backend.python.config import settings
        target_min = settings.guardrails.target_apr_min
        target_max = settings.guardrails.target_apr_max
    except Exception:
        target_min = 0.34
        target_max = 0.40

    breach = weighted_apr < target_min or weighted_apr > target_max

    # Optional: observed portfolio yield from actual interest receipts
    portfolio_yield_pct: float | None = None
    yield_source: str | None = None
    if payments_df is not None and total_bal > 0:
        pay_int = _col(payments_df, ['true_interest_payment'])
        pay_fee = _col(payments_df, ['true_fee_payment'])
        if pay_int or pay_fee:
            total_receipts = 0.0
            if pay_int:
                total_receipts += float(pd.to_numeric(payments_df[pay_int], errors='coerce').fillna(0).sum())
            if pay_fee:
                total_receipts += float(pd.to_numeric(payments_df[pay_fee], errors='coerce').fillna(0).sum())
            if total_receipts > 0:
                portfolio_yield_pct = round(total_receipts / total_bal * 100, 2)
                yield_source = 'total_interest_fees_over_outstanding'

    return {
        'status': 'ok',
        'eir_type': 'rate_charged_to_clients',
        'weighted_apr_pct': round(weighted_apr * 100, 2),
        'min_apr_pct': round(float(df['_apr'].min()) * 100, 2),
        'max_apr_pct': round(float(df['_apr'].max()) * 100, 2),
        'target_range_pct': f'{round(target_min * 100):.0f}–{round(target_max * 100):.0f}%',
        'breach': breach,
        'total_outstanding_usd': round(total_bal, 2),
        'loan_count': int(len(df)),
        'portfolio_yield_pct': portfolio_yield_pct,
        'portfolio_yield_note': yield_source,
        'note': (
            'EIR = weighted-average APR charged by Abaco to factoring clients. '
            f'Target band {round(target_min * 100):.0f}–{round(target_max * 100):.0f}% '
            'from business_parameters.yml (target_apr_min / target_apr_max).'
        ),
    }


def cost_of_debt_dscr(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame | None = None,
    cost_of_debt_pct: float = 0.15,
) -> dict[str, Any]:
    """
    Costo de Deuda / DSCR proxy.

    DSCR = Annual Interest Income / Annual Debt Service
    Annual Debt Service = AUM × cost_of_debt_pct

    Uses 15 % proxy while EEFF are pending.  Replace cost_of_debt_pct with
    the actual weighted funding cost once financial statements are received.
    """
    try:
        from backend.python.config import settings
        min_dscr = settings.guardrails.min_dscr
        max_cod = settings.guardrails.max_cost_of_debt
    except Exception:
        min_dscr = 1.2
        max_cod = 0.13

    bal_col = _col(loans_df, ['outstanding_loan_value', 'outstanding_balance'])
    aum_usd = (
        float(pd.to_numeric(loans_df[bal_col], errors='coerce').fillna(0).sum())
        if bal_col
        else 0.0
    )

    annual_interest_income = 0.0
    income_source = 'not_computed'

    if payments_df is not None:
        pay_int = _col(payments_df, ['true_interest_payment'])
        pay_fee = _col(payments_df, ['true_fee_payment'])
        pay_tax = _col(payments_df, ['true_tax_payment'])
        pay_date_col = _col(payments_df, ['true_payment_date'])

        if pay_int or pay_fee:
            raw_income = 0.0
            if pay_int:
                raw_income += float(pd.to_numeric(payments_df[pay_int], errors='coerce').fillna(0).sum())
            if pay_fee:
                raw_income += float(pd.to_numeric(payments_df[pay_fee], errors='coerce').fillna(0).sum())
            if pay_tax:
                raw_income -= float(pd.to_numeric(payments_df[pay_tax], errors='coerce').fillna(0).sum())

            if pay_date_col:
                dates = pd.to_datetime(payments_df[pay_date_col], errors='coerce').dropna()
                if len(dates) > 1:
                    months_covered = max(1.0, (dates.max() - dates.min()).days / 30)
                    annual_interest_income = raw_income / months_covered * 12
                    income_source = f'payments_annualized_{round(months_covered, 1)}_months'
                else:
                    annual_interest_income = raw_income
                    income_source = 'payments_total_single_period'
            else:
                annual_interest_income = raw_income
                income_source = 'payments_total_no_date'

    # Fallback: AUM × avg APR estimate
    if annual_interest_income == 0 and aum_usd > 0:
        apr_col = _col(loans_df, ['interest_rate_apr', 'interest_rate'])
        if apr_col:
            apr_vals = pd.to_numeric(loans_df[apr_col], errors='coerce').dropna()
            if len(apr_vals) > 0:
                avg_apr = float(apr_vals.mean())
                annual_interest_income = aum_usd * avg_apr
                income_source = f'estimated_aum_x_avg_apr_{round(avg_apr * 100, 1)}pct'

    annual_debt_service = aum_usd * cost_of_debt_pct
    dscr = annual_interest_income / max(annual_debt_service, 1)

    return {
        'status': 'ok',
        'dscr': round(dscr, 3),
        'dscr_target_min': min_dscr,
        'dscr_breach': dscr < min_dscr,
        'cost_of_debt_pct_used': round(cost_of_debt_pct * 100, 1),
        'cost_of_debt_max_pct': round(max_cod * 100, 1),
        'annual_interest_income_usd': round(annual_interest_income, 2),
        'annual_debt_service_usd': round(annual_debt_service, 2),
        'aum_usd': round(aum_usd, 2),
        'income_source': income_source,
        'data_source': 'proxy',
        'note': (
            f'PROXY: {round(cost_of_debt_pct * 100, 1)}% cost of debt assumed until EEFF are received. '
            f'Config max_cost_of_debt = {round(max_cod * 100, 1)}%. '
            'Pass actual weighted funding cost via cost_of_debt_pct once EEFF are available.'
        ),
    }


def build_lending_kpi_report(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    customer_df: pd.DataFrame | None = None,
    cash_balance_usd: float | None = None,
    pending_disbursements_usd: float = 0.0,
    cost_of_debt_pct: float = 0.15,
) -> dict[str, Any]:
    cdr = cdr_by_cohort(loans_df)
    liq = liquidation_rate(loans_df, payments_df)
    ecl = lgd_ecl_by_segment(loans_df, customer_df)
    bs = balance_sheet_proxy(loans_df, payments_df)
    appr = approval_metrics(customer_df) if customer_df is not None else {'status': 'no_customer_data'}
    cure = cure_rate_by_period(payments_df)
    ptp = promise_to_pay_metrics(payments_df)
    mype = mype_approval_batch(loans_df, payments_df)
    treasury = (
        cash_balance_treasury(
            cash_balance_usd=cash_balance_usd,
            pending_disbursements_usd=pending_disbursements_usd,
            loans_df=loans_df,
        )
        if cash_balance_usd is not None
        else {'status': 'not_provided', 'note': 'Pass cash_balance_usd (daily bank balance) to activate treasury capacity view.'}
    )
    ce_6m = collection_efficiency_6m(loans_df, payments_df)
    sla = sla_targets(loans_df)
    eir = financing_rate_eir(loans_df, payments_df)
    dscr = cost_of_debt_dscr(loans_df, payments_df, cost_of_debt_pct=cost_of_debt_pct)
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'cdr_curves': cdr,
        'liquidation_rate': liq,
        'lgd_ecl': ecl,
        'balance_sheet': bs,
        'approval_metrics': appr,
        'cure_rate': cure,
        'promise_to_pay': ptp,
        'mype_decisions': mype,
        'treasury_capacity': treasury,
        'collection_efficiency_6m': ce_6m,
        'sla_targets': sla,
        'financing_rate_eir': eir,
        'cost_of_debt_dscr': dscr,
    }
