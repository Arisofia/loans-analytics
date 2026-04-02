from __future__ import annotations

from typing import Any

import pandas as pd

from backend.loans_analytics.multi_agent.feature_store.customer_features import (
    build_customer_features,
)
from backend.loans_analytics.multi_agent.feature_store.segment_features import (
    build_segment_features,
)


def build_feature_store(
    marts: dict[str, pd.DataFrame],
    metrics: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    portfolio = marts.get("portfolio_mart", pd.DataFrame())

    customer_feat = build_customer_features(portfolio)
    segment_feat = build_segment_features(portfolio)

    return {
        "customer_features": customer_feat,
        "segment_features": segment_feat,
    }
