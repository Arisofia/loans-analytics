from __future__ import annotations
import logging
from datetime import date, datetime
from typing import Union
import numpy as np
import pandas as pd
logger = logging.getLogger(__name__)
_MAX_ITER = 200
_TOLERANCE = 1e-09
_INITIAL_GUESS = 0.1
_DateLike = Union[str, date, datetime, pd.Timestamp]

def xirr(cashflows: list[float], dates: list[_DateLike], guess: float=_INITIAL_GUESS) -> float:
    if len(cashflows) != len(dates):
        raise ValueError(f'cashflows ({len(cashflows)}) and dates ({len(dates)}) must have the same length')
    if len(cashflows) < 2:
        raise ValueError('At least two cash flows are required')
    cfs_raw = np.array(cashflows, dtype=float)
    parsed_dates = pd.to_datetime(pd.Series(dates), errors='coerce', format='mixed')
    valid_mask = parsed_dates.notna().to_numpy()
    cfs_raw = cfs_raw[valid_mask]
    parsed_dates = parsed_dates[valid_mask]
    if len(cfs_raw) < 2:
        raise ValueError('XIRR requires at least two cashflows with valid dates')
    order = np.argsort(np.array(parsed_dates, dtype='datetime64[D]'))
    cfs = cfs_raw[order]
    parsed_dates = parsed_dates.iloc[order].dt.date.tolist()
    t0 = parsed_dates[0]
    years = np.array([(d - t0).days / 365.0 for d in parsed_dates])
    if not (np.any(cfs > 0) and np.any(cfs < 0)):
        raise ValueError('cashflows must contain at least one positive and one negative value; XIRR has no solution when all flows have the same sign')

    def _npv(r: float) -> float:
        if r <= -1.0:
            return float('inf')
        return float(np.sum(cfs / (1.0 + r) ** years))

    def _dnpv(r: float) -> float:
        if r <= -1.0:
            return float('inf')
        return float(np.sum(-years * cfs / (1.0 + r) ** (years + 1.0)))
    for g in [guess, 0.0, -0.05, 0.5, -0.5, 1.0]:
        try:
            result = _newton_raphson(_npv, _dnpv, g)
            if result is not None:
                return result
        except (ZeroDivisionError, OverflowError, FloatingPointError) as exc:
            logger.debug('Newton-Raphson failed for starting guess %s due to numerical error: %s', g, exc)
    result = _bisect(_npv)
    if result is not None:
        return result
    logger.warning('XIRR did not converge - returning NaN (#NUM! equivalent)')
    return float('nan')

def xirr_dataframe(df: pd.DataFrame, *, cashflow_col: str='cashflow', date_col: str='date', guess: float=_INITIAL_GUESS) -> float:
    df = df.sort_values(date_col).reset_index(drop=True)
    return xirr(df[cashflow_col].tolist(), df[date_col].tolist(), guess=guess)

def contractual_apr(nominal_rate: float, payments_per_year: int=12) -> float:
    if payments_per_year <= 0:
        raise ValueError('payments_per_year must be > 0')
    return (1.0 + nominal_rate / payments_per_year) ** payments_per_year - 1.0

def loan_xirr(disbursements_df: pd.DataFrame, payments_df: pd.DataFrame, loan_id: str, *, loan_id_col: str='loan_id', disb_date_col: str='disbursement_date', disb_amount_col: str='original_principal', pay_date_col: str='payment_date', pay_amount_col: str='paid_total') -> float:
    loan_row = disbursements_df[disbursements_df[loan_id_col] == loan_id]
    if loan_row.empty:
        logger.warning("loan_xirr: loan_id '%s' not found in disbursements", loan_id)
        return float('nan')
    amount = float(loan_row[disb_amount_col].iloc[0])
    disb_date = loan_row[disb_date_col].iloc[0]
    pays = payments_df[payments_df[loan_id_col] == loan_id].copy()
    pays = pays.dropna(subset=[pay_date_col, pay_amount_col])
    pays = pays[pays[pay_amount_col] > 0]
    if pays.empty:
        logger.warning("loan_xirr: no payments found for loan_id '%s'", loan_id)
        return float('nan')
    cashflows = [-amount] + pays[pay_amount_col].tolist()
    dates = [disb_date] + pays[pay_date_col].tolist()
    try:
        return xirr(cashflows, dates)
    except ValueError as exc:
        logger.warning("loan_xirr: %s for loan_id '%s'", exc, loan_id)
        return float('nan')

def portfolio_xirr(disbursements_df: pd.DataFrame, payments_df: pd.DataFrame, *, loan_id_col: str='loan_id', disb_date_col: str='disbursement_date', disb_amount_col: str='original_principal', pay_date_col: str='payment_date', pay_amount_col: str='paid_total') -> pd.Series:
    results = {}
    for lid in disbursements_df[loan_id_col].unique():
        results[lid] = loan_xirr(disbursements_df, payments_df, lid, loan_id_col=loan_id_col, disb_date_col=disb_date_col, disb_amount_col=disb_amount_col, pay_date_col=pay_date_col, pay_amount_col=pay_amount_col)
    return pd.Series(results, name='xirr')

def _newton_raphson(f, df, x0: float, tol: float=_TOLERANCE, max_iter: int=_MAX_ITER):
    x = x0
    for _ in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            return x
        dfx = df(x)
        if abs(dfx) < 1e-15:
            return None
        x = x - fx / dfx
        if not np.isfinite(x) or x <= -1.0:
            return None
    return None

def _find_bracket(f, flo: float) -> float | None:
    for scale in [2.0, 5.0, 10.0, 50.0]:
        try:
            if flo * f(scale) < 0:
                return scale
        except (ZeroDivisionError, OverflowError):
            logger.debug('Numerical error when evaluating function at scale=%s; trying next candidate.', scale)
    return None

def _bisect(f, lo: float=-0.999, hi: float=10.0, tol: float=_TOLERANCE, max_iter: int=200):
    try:
        flo, fhi = (f(lo), f(hi))
    except (ZeroDivisionError, OverflowError):
        return None
    if flo * fhi > 0:
        new_hi = _find_bracket(f, flo)
        if new_hi is None:
            return None
        hi = new_hi
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        fmid = f(mid)
        if abs(fmid) < tol or (hi - lo) / 2.0 < tol:
            return mid
        if flo * fmid <= 0:
            hi = mid
        else:
            lo = mid
            flo = fmid
    return (lo + hi) / 2.0

def _to_date(d: _DateLike) -> date:
    if isinstance(d, pd.Timestamp):
        return d.date()
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return pd.to_datetime(str(d)).date()
