from __future__ import annotations

from typing import Any

import pandas as pd

from backend.src.marts.builder import build_all_marts as _build_from_df
from backend.src.marts.finance_mart import build_finance_mart
from backend.src.marts.portfolio_mart import build_portfolio_mart
from backend.src.marts.sales_mart import build_sales_mart


def build_all_marts(canonical_bundle: dict[str, Any]) -> dict[str, Any]:
    """Build all domain marts from the canonical bundle.

    If the bundle contains a pre-built canonical DataFrame (key ``"df"``),
    delegates to the comprehensive ``builder.build_all_marts`` which produces
    all 6 marts.  Otherwise falls back to building from individual collections.
    """
    # New path: unified DataFrame from transformation phase
    if "df" in canonical_bundle and isinstance(canonical_bundle["df"], pd.DataFrame):
        return _build_from_df(canonical_bundle["df"])

    # Legacy path: individual collections (loans, leads, etc.)
    portfolio_mart = build_portfolio_mart(canonical_bundle["loans"])
    finance_mart = build_finance_mart(portfolio_mart)
    sales_mart = build_sales_mart(canonical_bundle["leads"])

    return {
        "portfolio_mart": portfolio_mart,
        "finance_mart": finance_mart,
        "sales_mart": sales_mart,
    }
