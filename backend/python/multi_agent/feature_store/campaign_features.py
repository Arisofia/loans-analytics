"""Campaign features derived from marketing mart.

Builds features for marketing/acquisition performance analysis by agents.
"""

from __future__ import annotations

import pandas as pd


def build_campaign_features(marketing: pd.DataFrame) -> pd.DataFrame:
    """Add derived campaign-level columns from the marketing mart.

    Returns a *copy* — the original mart is not mutated.
    """
    df = marketing.copy()

    # Channel group (collapse variations)
    if "advisory_channel" in df.columns:
        df["channel_group"] = (
            df["advisory_channel"]
            .fillna("unknown")
            .str.strip()
            .str.lower()
            .replace({"": "unknown"})
        )
    else:
        df["channel_group"] = "unknown"

    # Origination month cohort
    if "origination_date" in df.columns:
        orig = pd.to_datetime(df["origination_date"], errors="coerce")
        df["origination_month"] = orig.dt.to_period("M").astype(str)
    else:
        df["origination_month"] = "unknown"

    # Average ticket by channel
    if "amount" in df.columns and "advisory_channel" in df.columns:
        amt = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        channel_avg = amt.groupby(df["advisory_channel"]).transform("mean")
        df["channel_avg_ticket"] = channel_avg
    else:
        df["channel_avg_ticket"] = 0.0

    # Conversion proxy: active vs total by channel
    if "status" in df.columns:
        df["is_active"] = (df["status"].str.lower() == "active").astype(int)
    else:
        df["is_active"] = 0

    # TPV per loan
    if "tpv" in df.columns and "amount" in df.columns:
        tpv = pd.to_numeric(df["tpv"], errors="coerce").fillna(0)
        amt = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["tpv_ratio"] = (tpv / amt.replace(0, float("nan"))).fillna(0)
    else:
        df["tpv_ratio"] = 0.0

    return df
