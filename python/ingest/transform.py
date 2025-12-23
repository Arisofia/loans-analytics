import pandas as pd
from datetime import datetime


def canonicalize_loan_tape(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recompute critical columns, normalize types, and validate.
    """
    df = df.rename(columns={c: c.strip() for c in df.columns})

    if "loan_id" not in df.columns:
        candidates = ["id", "loanId", "LoanID"]
        for candidate in candidates:
            if candidate in df.columns:
                df = df.rename(columns={candidate: "loan_id"})
                break

    if "balance" in df.columns:
        df["balance"] = pd.to_numeric(df["balance"], errors="coerce").fillna(0.0)
    else:
        df["balance"] = 0.0

    for col in ["origination_date", "maturity_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    if "days_past_due" not in df.columns:
        if "dpd" in df.columns:
            df["days_past_due"] = pd.to_numeric(df["dpd"], errors="coerce").fillna(0).astype(int)
        else:
            df["days_past_due"] = 0

    df["data_ingest_ts"] = datetime.utcnow()
    df = df[df["loan_id"].notna()]
    return df
