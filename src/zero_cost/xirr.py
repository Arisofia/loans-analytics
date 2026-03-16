"""
XIRR and APR calculations for loan portfolio analytics.

XIRR
----
Computes the Internal Rate of Return for irregular cash flows using the
Newton-Raphson method, falling back to bisection for robustness.

Contractual APR
---------------
Derived from the nominal annual rate stored in dim_loan, adjusted to an
Effective Annual Rate (EAR) using the compounding frequency.

Usage
-----
    from src.zero_cost.xirr import xirr, contractual_apr, loan_xirr

    # Standalone XIRR
    rate = xirr([-1000, 500, 600], ["2025-01-01", "2025-07-01", "2026-01-01"])

    # DataFrame-level XIRR for a loan
    rate = loan_xirr(disbursement_df, payments_df, loan_id="L-001")
"""

from __future__ import annotations

import logging
import warnings
from datetime import date, datetime
from typing import Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Numeric guard constants
_MAX_ITER = 200
_TOLERANCE = 1e-9
_INITIAL_GUESS = 0.10  # 10 %

# Type alias for dates accepted as input
_DateLike = Union[str, date, datetime, pd.Timestamp]


# =============================================================================
# Core XIRR function
# =============================================================================


def xirr(
    cashflows: list[float],
    dates: list[_DateLike],
    guess: float = _INITIAL_GUESS,
) -> float:
    """Compute the XIRR for irregular cash flows.

    The sign convention follows Excel XIRR:
      - Negative values represent outflows (disbursements, fees paid).
      - Positive values represent inflows (repayments received).

    Parameters
    ----------
    cashflows:
        List of cash-flow amounts.  Must contain at least one positive and one
        negative value; otherwise raises :exc:`ValueError`.
    dates:
        List of dates corresponding to *cashflows*.  Accepts ``str``,
        ``datetime``, ``date``, or ``pd.Timestamp``.  Must have the same
        length as *cashflows*.
    guess:
        Initial rate guess (default 10 %).  The solver tries multiple starting
        points if the first attempt fails.

    Returns
    -------
    float
        Annual rate of return (e.g., 0.25 = 25 %).  Returns ``float('nan')``
        when convergence fails (equivalent to Excel #NUM!).

    Raises
    ------
    ValueError
        If *cashflows* and *dates* have different lengths, or if all cash
        flows have the same sign (no solution exists).
    """
    if len(cashflows) != len(dates):
        raise ValueError(
            f"cashflows ({len(cashflows)}) and dates ({len(dates)}) must have the same length"
        )
    if len(cashflows) < 2:
        raise ValueError("At least two cash flows are required")

    cfs = np.array(cashflows, dtype=float)
    parsed_dates = [_to_date(d) for d in dates]
    t0 = parsed_dates[0]
    # Fractional years from t0
    years = np.array([(d - t0).days / 365.0 for d in parsed_dates])

    # Guard: must have at least one positive and one negative value
    if not (np.any(cfs > 0) and np.any(cfs < 0)):
        raise ValueError(
            "cashflows must contain at least one positive and one negative value; "
            "XIRR has no solution when all flows have the same sign"
        )

    # NPV function:  NPV(r) = Σ CF_i / (1+r)^t_i
    def _npv(r: float) -> float:
        if r <= -1.0:
            return float("inf")
        return float(np.sum(cfs / (1.0 + r) ** years))

    # NPV derivative:  dNPV/dr = Σ -t_i * CF_i / (1+r)^(t_i+1)
    def _dnpv(r: float) -> float:
        if r <= -1.0:
            return float("inf")
        return float(np.sum(-years * cfs / (1.0 + r) ** (years + 1.0)))

    # Try Newton-Raphson from several starting points
    for g in [guess, 0.0, -0.05, 0.50, -0.50, 1.0]:
        try:
            result = _newton_raphson(_npv, _dnpv, g)
            if result is not None:
                return result
        except (ZeroDivisionError, OverflowError, FloatingPointError):
            pass

    # Bisection fallback
    result = _bisect(_npv)
    if result is not None:
        return result

    logger.warning("XIRR did not converge - returning NaN (#NUM! equivalent)")
    return float("nan")


def xirr_dataframe(
    df: pd.DataFrame,
    *,
    cashflow_col: str = "cashflow",
    date_col: str = "date",
    guess: float = _INITIAL_GUESS,
) -> float:
    """Compute XIRR from a DataFrame with cash-flow and date columns.

    Parameters
    ----------
    df:
        DataFrame with at least *cashflow_col* and *date_col* columns.
    cashflow_col:
        Column containing cash-flow amounts.
    date_col:
        Column containing dates.
    guess:
        Initial rate guess.
    """
    df = df.sort_values(date_col).reset_index(drop=True)
    return xirr(df[cashflow_col].tolist(), df[date_col].tolist(), guess=guess)


# =============================================================================
# Contractual APR
# =============================================================================


def contractual_apr(
    nominal_rate: float,
    payments_per_year: int = 12,
) -> float:
    """Convert a nominal annual rate to an Effective Annual Rate (EAR).

    Formula:  EAR = (1 + nominal / n)^n − 1

    Parameters
    ----------
    nominal_rate:
        Nominal annual interest rate (e.g., 0.24 for 24 %).
    payments_per_year:
        Number of compounding periods per year.  Defaults to 12 (monthly).

    Returns
    -------
    float
        Effective Annual Rate.
    """
    if payments_per_year <= 0:
        raise ValueError("payments_per_year must be > 0")
    return (1.0 + nominal_rate / payments_per_year) ** payments_per_year - 1.0


def loan_xirr(
    disbursements_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    loan_id: str,
    *,
    loan_id_col: str = "loan_id",
    disb_date_col: str = "disbursement_date",
    disb_amount_col: str = "original_principal",
    pay_date_col: str = "payment_date",
    pay_amount_col: str = "paid_total",
) -> float:
    """Compute XIRR for a single loan.

    Parameters
    ----------
    disbursements_df:
        dim_loan DataFrame (one row per loan).
    payments_df:
        fact_real_payment DataFrame (one row per payment).
    loan_id:
        Identifier of the loan to compute XIRR for.

    Returns
    -------
    float
        XIRR (annual rate) or ``float('nan')`` if not computable.
    """
    loan_row = disbursements_df[disbursements_df[loan_id_col] == loan_id]
    if loan_row.empty:
        logger.warning("loan_xirr: loan_id '%s' not found in disbursements", loan_id)
        return float("nan")

    amount = float(loan_row[disb_amount_col].iloc[0])
    disb_date = loan_row[disb_date_col].iloc[0]

    pays = payments_df[payments_df[loan_id_col] == loan_id].copy()
    pays = pays.dropna(subset=[pay_date_col, pay_amount_col])
    pays = pays[pays[pay_amount_col] > 0]

    if pays.empty:
        logger.warning("loan_xirr: no payments found for loan_id '%s'", loan_id)
        return float("nan")

    cashflows = [-amount] + pays[pay_amount_col].tolist()
    dates = [disb_date] + pays[pay_date_col].tolist()

    try:
        return xirr(cashflows, dates)
    except ValueError as exc:
        logger.warning("loan_xirr: %s for loan_id '%s'", exc, loan_id)
        return float("nan")


def portfolio_xirr(
    disbursements_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    *,
    loan_id_col: str = "loan_id",
    disb_date_col: str = "disbursement_date",
    disb_amount_col: str = "original_principal",
    pay_date_col: str = "payment_date",
    pay_amount_col: str = "paid_total",
) -> pd.Series:
    """Compute XIRR for every loan in *disbursements_df*.

    Returns
    -------
    pd.Series
        Index = loan_id, values = XIRR rate.
    """
    results = {}
    for lid in disbursements_df[loan_id_col].unique():
        results[lid] = loan_xirr(
            disbursements_df,
            payments_df,
            lid,
            loan_id_col=loan_id_col,
            disb_date_col=disb_date_col,
            disb_amount_col=disb_amount_col,
            pay_date_col=pay_date_col,
            pay_amount_col=pay_amount_col,
        )
    return pd.Series(results, name="xirr")


# =============================================================================
# Solver internals
# =============================================================================


def _newton_raphson(f, df, x0: float, tol: float = _TOLERANCE, max_iter: int = _MAX_ITER):
    """Newton-Raphson solver.  Returns root or ``None`` on failure."""
    x = x0
    for _ in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            return x
        dfx = df(x)
        if abs(dfx) < 1e-15:
            return None  # flat derivative — switch method
        x = x - fx / dfx
        if not np.isfinite(x) or x <= -1.0:
            return None
    return None


def _bisect(f, lo: float = -0.999, hi: float = 10.0, tol: float = _TOLERANCE, max_iter: int = 200):
    """Bisection method on [lo, hi].  Returns root or ``None``."""
    try:
        flo, fhi = f(lo), f(hi)
    except (ZeroDivisionError, OverflowError):
        return None
    if flo * fhi > 0:
        # No sign change in [lo, hi] — try to find a bracket
        for scale in [2.0, 5.0, 10.0, 50.0]:
            try:
                fhi = f(scale)
                if flo * fhi < 0:
                    hi = scale
                    break
            except (ZeroDivisionError, OverflowError):
                pass
        else:
            return None

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
    """Convert various date representations to :class:`datetime.date`."""
    if isinstance(d, pd.Timestamp):
        return d.date()
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return pd.to_datetime(str(d)).date()
