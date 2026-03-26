"""Segment-level features — build from customer features.

Produces segment profiles used by the segmentation, pricing, and
marketing agents to drive differentiated strategy.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def build_segment_features(customer_df: pd.DataFrame) -> Dict[str, Any]:
    """Segment customers and return segment profiles.

    Segmentation axes:
    * By ticket size: micro / small / medium / large
    * By behaviour: repeat vs first-time
    * By risk: current vs delinquent vs defaulted
    """
    if customer_df.empty:
        return {"segments": [], "total_customers": 0}

    segments: List[Dict[str, Any]] = []

    # ── Ticket-size segments ────────────────────────────────────────────
    if "avg_ticket" in customer_df.columns:
        bins = [0, 5_000, 25_000, 100_000, float("inf")]
        labels = ["micro", "small", "medium", "large"]
        customer_df = customer_df.copy()
        customer_df["size_segment"] = pd.cut(
            pd.to_numeric(customer_df["avg_ticket"], errors="coerce").fillna(0),
            bins=bins, labels=labels,
        )
        for seg in labels:
            subset = customer_df[customer_df["size_segment"] == seg]
            if subset.empty:
                continue
            segments.append({
                "segment": f"ticket_{seg}",
                "count": int(len(subset)),
                "total_exposure": float(subset["total_exposure"].sum()) if "total_exposure" in subset.columns else 0,
                "avg_ticket": float(subset["avg_ticket"].mean()),
                "repeat_pct": float(subset["is_repeat"].mean()) if "is_repeat" in subset.columns else 0,
            })

    # ── Risk segments ───────────────────────────────────────────────────
    if "worst_status" in customer_df.columns:
        for status in ["active", "delinquent", "defaulted", "closed"]:
            subset = customer_df[customer_df["worst_status"] == status]
            if subset.empty:
                continue
            segments.append({
                "segment": f"risk_{status}",
                "count": int(len(subset)),
                "total_exposure": float(subset["total_exposure"].sum()) if "total_exposure" in subset.columns else 0,
                "avg_dpd": float(subset["avg_dpd"].mean()) if "avg_dpd" in subset.columns else 0,
            })

    return {
        "segments": segments,
        "total_customers": int(len(customer_df)),
    }
