"""Business dimensions — standard analytical axes for slicing metrics.

Dimensions are the columns by which mart data can be grouped, filtered,
or drilled down.  Each dimension maps to one or more mart columns and
provides canonical labels for the frontend and agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Dimension:
    """One analytical dimension (e.g. sector, channel, dpd_bucket)."""

    dim_id: str
    label: str
    source_column: str
    mart: str
    description: str = ""
    allowed_values: Optional[List[str]] = field(default=None)


# ── Standard dimension catalogue ────────────────────────────────────────
DIMENSIONS: Dict[str, Dimension] = {
    "status": Dimension(
        dim_id="status",
        label="Loan Status",
        source_column="status",
        mart="portfolio_mart",
        allowed_values=["active", "delinquent", "defaulted", "closed"],
    ),
    "sector": Dimension(
        dim_id="sector",
        label="Government Sector",
        source_column="sector",
        mart="portfolio_mart",
    ),
    "credit_line": Dimension(
        dim_id="credit_line",
        label="Credit Line",
        source_column="credit_line",
        mart="sales_mart",
    ),
    "advisory_channel": Dimension(
        dim_id="advisory_channel",
        label="Advisory Channel",
        source_column="advisory_channel",
        mart="marketing_mart",
    ),
    "dpd_bucket": Dimension(
        dim_id="dpd_bucket",
        label="DPD Bucket",
        source_column="dpd",
        mart="portfolio_mart",
        description="Derived: 0, 1-30, 31-60, 61-90, 90+",
    ),
    "origination_month": Dimension(
        dim_id="origination_month",
        label="Origination Month",
        source_column="origination_date",
        mart="portfolio_mart",
        description="Derived: YYYY-MM from origination_date",
    ),
    "kam_hunter": Dimension(
        dim_id="kam_hunter",
        label="KAM Hunter",
        source_column="kam_hunter",
        mart="sales_mart",
    ),
    "kam_farmer": Dimension(
        dim_id="kam_farmer",
        label="KAM Farmer",
        source_column="kam_farmer",
        mart="sales_mart",
    ),
    "country": Dimension(
        dim_id="country",
        label="Country",
        source_column="country",
        mart="portfolio_mart",
        allowed_values=["SV"],
    ),
}


def get_dimension(dim_id: str) -> Optional[Dimension]:
    """Look up a dimension by ID."""
    return DIMENSIONS.get(dim_id)


def list_dimensions() -> List[Dimension]:
    """Return all registered dimensions."""
    return list(DIMENSIONS.values())
