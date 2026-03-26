from __future__ import annotations

import pandas as pd


def find_missing_required_ids(loans_df: pd.DataFrame) -> list[str]:
    required = ["loan_id", "customer_id"]
    missing: list[str] = []
    for col in required:
        if col not in loans_df.columns:
            missing.append(col)
        else:
            nulls = int(loans_df[col].isna().sum())
            if nulls > 0:
                missing.append(f"{col}_nulls:{nulls}")
    return missing


def find_duplicate_loans(loans_df: pd.DataFrame) -> int:
    if "loan_id" not in loans_df.columns:
        return 0
    return int(loans_df["loan_id"].duplicated().sum())


def find_impossible_dpd(loans_df: pd.DataFrame) -> int:
    if "days_past_due" not in loans_df.columns:
        return 0
    return int((loans_df["days_past_due"] < 0).sum())
