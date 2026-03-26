"""Mart assembly — delegates to individual mart modules and returns the full bundle."""

from __future__ import annotations

import logging
from typing import Dict

import pandas as pd

from backend.src.marts import (
    collections_mart,
    finance_mart,
    marketing_mart,
    portfolio_mart,
    sales_mart,
    treasury_mart,
)

logger = logging.getLogger(__name__)

_REQUIRED_COLUMNS = {"loan_id", "borrower_id", "amount", "status"}


def build_all_marts(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Build all domain marts from the canonical transformed DataFrame."""
    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Canonical DataFrame missing required columns: {missing}")

    logger.info("Building data marts from %d records, %d columns", len(df), len(df.columns))

    marts = {
        "portfolio_mart": portfolio_mart.build(df),
        "finance_mart": finance_mart.build(df),
        "sales_mart": sales_mart.build(df),
        "collections_mart": collections_mart.build(df),
        "treasury_mart": treasury_mart.build(df),
        "marketing_mart": marketing_mart.build(df),
    }

    for name, mart_df in marts.items():
        logger.info("  %s: %d rows, %d columns", name, len(mart_df), len(mart_df.columns))

    return marts
