from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

import pandas as pd


def _first_existing_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> Optional[str]:
    return next((column for column in candidates if column in df.columns), None)


def compute_net_yield(finance_mart: pd.DataFrame) -> Decimal:
    if finance_mart.empty:
        return Decimal("0.0")
    income = Decimal(str(finance_mart["interest_income"].sum())) + Decimal(str(finance_mart["fee_income"].sum()))
    debt = Decimal(str(finance_mart["debt_balance"].mean()))
    if debt == 0:
        return Decimal("0.0")
    return (income / debt).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_spread(finance_mart: pd.DataFrame) -> Decimal:
    if finance_mart.empty:
        return Decimal("0.0")
    income = Decimal(str(finance_mart["interest_income"].sum())) + Decimal(str(finance_mart["fee_income"].sum()))
    cost = Decimal(str(finance_mart["funding_cost"].sum()))
    debt = Decimal(str(finance_mart["debt_balance"].mean()))
    if debt == 0:
        return Decimal("0.0")
    return ((income - cost) / debt).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_eir(portfolio_mart: pd.DataFrame) -> Decimal:
    """
    Compute Effective Interest Rate (EIR).
    Formula: ((1 + APR / 365) ^ 365) - 1 (Compounded Daily)
    """
    if portfolio_mart.empty:
        return Decimal("0.0")
    
    avg_apr = Decimal(str(portfolio_mart["apr"].fillna(0).mean()))
    if avg_apr == 0:
        return Decimal("0.0")
        
    eir = (Decimal("1") + avg_apr / Decimal("365")) ** 365 - Decimal("1")
    return eir.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_portfolio_yield(portfolio_mart: pd.DataFrame) -> Decimal:
    if portfolio_mart.empty:
        return Decimal("0.0")

    rate_col = _first_existing_column(portfolio_mart, ("interest_rate", "apr", "interest_rate_apr"))
    balance_col = _first_existing_column(
        portfolio_mart,
        ("outstanding_principal", "outstanding_balance", "principal_balance", "current_balance", "amount"),
    )
    if rate_col is None:
        return Decimal("0.0")

    rate_series = pd.to_numeric(portfolio_mart[rate_col], errors="coerce").fillna(0)
    if balance_col is None:
        avg_rate = Decimal(str(rate_series.mean()))
        return (avg_rate * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    balance_series = pd.to_numeric(portfolio_mart[balance_col], errors="coerce").fillna(0)
    total_balance = Decimal(str(balance_series.sum()))
    if total_balance == 0:
        return Decimal("0.0")
    weighted_rate_sum = Decimal(str((rate_series * balance_series).sum()))
    return ((weighted_rate_sum / total_balance) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_portfolio_irr(finance_mart: pd.DataFrame) -> Decimal:
    """Backward-compatible alias for the explicit proxy implementation."""
    return compute_portfolio_irr_proxy(finance_mart)


def compute_portfolio_irr_proxy(finance_mart: pd.DataFrame) -> Decimal:
    """
    Compute portfolio IRR proxy from finance balances.
    Formula: (Interest Income + Fee Income) / Average Debt Balance
    """
    if finance_mart.empty:
        return Decimal("0.0")

    income = Decimal(str(finance_mart["interest_income"].sum())) + Decimal(str(finance_mart["fee_income"].sum()))
    avg_debt = Decimal(str(finance_mart["debt_balance"].mean()))
    if avg_debt == 0:
        return Decimal("0.0")
    return (income / avg_debt).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_portfolio_irr_true(disbursements_df: pd.DataFrame, payments_df: pd.DataFrame) -> Optional[Decimal]:
    """Compute true portfolio IRR from dated cashflows when available."""
    if disbursements_df.empty or payments_df.empty:
        return None

    disb_date_col = next((c for c in ("disbursement_date", "origination_date", "funded_at") if c in disbursements_df.columns), None)
    disb_amt_col = next((c for c in ("original_principal", "principal_amount", "funded_amount", "amount", "outstanding_principal") if c in disbursements_df.columns), None)
    pay_date_col = next((c for c in ("payment_date", "paid_at", "date") if c in payments_df.columns), None)
    pay_amt_col = next((c for c in ("paid_total", "payment_amount", "amount", "last_payment_amount") if c in payments_df.columns), None)

    if not all([disb_date_col, disb_amt_col, pay_date_col, pay_amt_col]):
        return None

    disb = disbursements_df[[disb_date_col, disb_amt_col]].copy()
    disb[disb_amt_col] = pd.to_numeric(disb[disb_amt_col], errors="coerce").fillna(0)
    disb = disb[disb[disb_amt_col] > 0]

    pays = payments_df[[pay_date_col, pay_amt_col]].copy()
    pays[pay_amt_col] = pd.to_numeric(pays[pay_amt_col], errors="coerce").fillna(0)
    pays = pays[pays[pay_amt_col] > 0]

    if disb.empty or pays.empty:
        return None

    cashflows: list[float] = [-float(v) for v in disb[disb_amt_col].tolist()] + [float(v) for v in pays[pay_amt_col].tolist()]
    dates = disb[disb_date_col].tolist() + pays[pay_date_col].tolist()

    # Import lazily to avoid adding XIRR dependency to unrelated code paths.
    from backend.src.zero_cost.xirr import xirr

    irr_value = xirr(cashflows, dates)
    if pd.isna(irr_value):
        return None
    return Decimal(str(irr_value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_growth_vs_targets(
    portfolio: pd.DataFrame,
    targets: Dict[str, float],
    period_col: str = "origination_month",
    balance_col: str = "outstanding_principal",
) -> List[Dict[str, Any]]:
    """Compare actual monthly portfolio balance against pre-set targets.

    Reads the portfolio mart, aggregates outstanding balance by month, then
    aligns each month against the ``targets`` dictionary to produce a gap
    analysis table suitable for a KPI dashboard or chart.

    Parameters
    ----------
    portfolio:
        Portfolio mart DataFrame.  Must contain ``period_col`` (month string
        in "YYYY-MM" format) and ``balance_col`` (numeric outstanding balance).
    targets:
        Monthly targets keyed by "YYYY-MM" strings, e.g.::

            {"2026-01": 8_500_000, "2026-02": 8_800_000, ...}

        Mirrors the ``portfolio_targets_2026`` block inside
        ``config/business_parameters.yml``.
    period_col:
        Column with the month period label.  Defaults to ``origination_month``.
    balance_col:
        Column with the loan balance to aggregate.

    Returns
    -------
    List of dicts, one per month that appears in either ``portfolio`` or
    ``targets``, sorted chronologically::

        {
            "month": "2026-01",
            "actual_usd": 8_200_000.00,
            "target_usd": 8_500_000.00,
            "gap_usd": -300_000.00,
            "gap_pct": -3.53,
            "status": "AT_RISK",          # ON_TRACK | WATCH | AT_RISK | NO_DATA
        }

    Status thresholds:
    - ``ON_TRACK``  ≥ 95 % of target
    - ``WATCH``     90 – 95 % of target
    - ``AT_RISK``   < 90 % of target
    - ``NO_DATA``   month not yet in portfolio
    """
    if portfolio.empty and not targets:
        return []

    # Aggregate actual balance by month
    if not portfolio.empty and period_col in portfolio.columns and balance_col in portfolio.columns:
        df = portfolio[[period_col, balance_col]].copy()
        df[balance_col] = pd.to_numeric(df[balance_col], errors="coerce").fillna(0)
        df[period_col] = df[period_col].astype(str).str[:7]  # normalise to YYYY-MM
        actual_by_month: Dict[str, float] = (
            df.groupby(period_col)[balance_col].sum().to_dict()
        )
    else:
        actual_by_month = {}

    all_months = sorted(set(targets.keys()) | set(actual_by_month.keys()))

    rows: List[Dict[str, Any]] = []
    for month in all_months:
        target_val = float(targets.get(month, 0.0))
        actual_val = float(actual_by_month.get(month, 0.0))

        if month not in actual_by_month:
            status = "NO_DATA"
            gap_usd = 0.0
            gap_pct = 0.0
        elif target_val == 0:
            status = "ON_TRACK"
            gap_usd = 0.0
            gap_pct = 0.0
        else:
            gap_usd = round(actual_val - target_val, 2)
            gap_pct = round(gap_usd / target_val * 100, 2)
            attainment = actual_val / target_val
            if attainment >= 0.95:
                status = "ON_TRACK"
            elif attainment >= 0.90:
                status = "WATCH"
            else:
                status = "AT_RISK"

        rows.append({
            "month": month,
            "actual_usd": round(actual_val, 2),
            "target_usd": round(target_val, 2),
            "gap_usd": gap_usd,
            "gap_pct": gap_pct,
            "status": status,
        })

    return rows


def compute_nim_proxy(
    avg_interest_rate: Decimal,
    config_path: Optional[str] = None,
) -> Decimal:
    """Net Interest Margin proxy: (avg_interest_rate - funding_cost_rate) * 100.

    Reads ``funding_cost_rate`` from ``config/business_parameters.yml``
    (or ``config_path`` if provided) so it is never hardcoded.

    Parameters
    ----------
    avg_interest_rate:
        Weighted average interest rate as a fraction (e.g. 0.18 for 18%).
    config_path:
        Path to the YAML config file. Defaults to ``config/business_parameters.yml``.

    Returns
    -------
    Decimal — NIM as a percentage (e.g. 8.00 for 8%), rounded to 2dp ROUND_HALF_UP.
    """
    import yaml  # local import to avoid adding yaml as top-level dep where not needed
    import os

    resolved_path = config_path or os.environ.get(
        "BUSINESS_PARAMS_PATH", "config/business_parameters.yml"
    )
    with open(resolved_path) as fh:
        params = yaml.safe_load(fh)

    funding_cost_rate = Decimal(
        str(params["financial_assumptions"]["funding_cost_rate"])
    )
    nim = (avg_interest_rate - funding_cost_rate) * Decimal("100")
    return nim.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
