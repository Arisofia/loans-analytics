from __future__ import annotations

import pandas as pd


def build_sales_mart(leads_df: pd.DataFrame) -> pd.DataFrame:
    df = leads_df.copy()

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    if "closed_at" in df.columns:
        df["closed_at"] = pd.to_datetime(df["closed_at"], errors="coerce")
        df["days_to_close"] = (df["closed_at"] - df["created_at"]).dt.days
    else:
        df["days_to_close"] = None

    required_columns = [
        "lead_id",
        "created_at",
        "owner",
        "stage",
        "source_channel",
        "sector",
        "country",
        "requested_ticket",
        "approved_ticket",
        "funded_flag",
        "days_to_close",
    ]
    for column in required_columns:
        if column not in df.columns:
            df[column] = None

    renamed = df.rename(columns={"created_at": "lead_created_at"})
    return renamed[[
        "lead_id",
        "lead_created_at",
        "owner",
        "stage",
        "source_channel",
        "sector",
        "country",
        "requested_ticket",
        "approved_ticket",
        "funded_flag",
        "days_to_close",
    ]].drop_duplicates(subset=["lead_id"])


build = build_sales_mart
