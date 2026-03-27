"""Data marts — decision-grade domain tables built from canonical portfolio DataFrame."""

from backend.src.marts import (  # noqa: F401 — re-export individual mart modules
    collections_mart,
    finance_mart,
    marketing_mart,
    portfolio_mart,
    sales_mart,
    treasury_mart,
)
from backend.src.marts.build_all_marts import build_all_marts  # noqa: F401
from backend.src.marts.builder import build_all_marts as build_all_marts_v2  # noqa: F401
