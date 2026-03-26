from __future__ import annotations

from typing import Any

from backend.src.marts.finance_mart import build_finance_mart
from backend.src.marts.portfolio_mart import build_portfolio_mart
from backend.src.marts.sales_mart import build_sales_mart


def build_all_marts(canonical_bundle: dict[str, Any]) -> dict[str, Any]:
    portfolio_mart = build_portfolio_mart(canonical_bundle["loans"])
    finance_mart = build_finance_mart(portfolio_mart)
    sales_mart = build_sales_mart(canonical_bundle["leads"])

    return {
        "portfolio_mart": portfolio_mart,
        "finance_mart": finance_mart,
        "sales_mart": sales_mart,
    }
