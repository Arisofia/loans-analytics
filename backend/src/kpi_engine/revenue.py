from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

import pandas as pd


def compute_net_yield(finance_mart: pd.DataFrame) -> float:
    if finance_mart.empty:
        return 0.0
    income = finance_mart["interest_income"].sum() + finance_mart["fee_income"].sum()
    debt = finance_mart["debt_balance"].mean()
    if debt == 0:
        return 0.0
    return float(income / debt)


def compute_spread(finance_mart: pd.DataFrame) -> float:
    if finance_mart.empty:
        return 0.0
    income = finance_mart["interest_income"].sum() + finance_mart["fee_income"].sum()
    cost = finance_mart["funding_cost"].sum()
    debt = finance_mart["debt_balance"].mean()
    if debt == 0:
        return 0.0
    return float((income - cost) / debt)


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
