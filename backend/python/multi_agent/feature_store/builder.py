"""Feature builder — orchestrates feature construction from marts.

Single entry point for the pipeline to build *all* features in one call.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from backend.python.multi_agent.feature_store.loan_features import (
    build_loan_features,
    get_feature_summary,
)
from backend.python.multi_agent.feature_store.customer_features import (
    build_customer_features,
)
from backend.python.multi_agent.feature_store.segment_features import (
    build_segment_features,
)


def build_all_features(marts: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Build all feature layers from marts.

    Parameters
    ----------
    marts : dict
        Output of ``backend.src.marts.builder.build_all_marts``.
        Expected keys: ``portfolio_mart``, ``sales_mart``, etc.

    Returns
    -------
    dict with keys:
        - ``loan_features``: DataFrame with loan-level derived columns
        - ``loan_summary``: dict with aggregate feature stats
        - ``customer_features``: DataFrame one row per borrower
        - ``segment_profiles``: dict with segment metadata
    """
    portfolio = marts.get("portfolio_mart", pd.DataFrame())

    loan_feat = build_loan_features(portfolio)
    cust_feat = build_customer_features(portfolio)
    seg_feat = build_segment_features(cust_feat)

    return {
        "loan_features": loan_feat,
        "loan_summary": get_feature_summary(loan_feat),
        "customer_features": cust_feat,
        "segment_profiles": seg_feat,
    }
