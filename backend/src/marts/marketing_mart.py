"""Marketing mart — acquisition channel performance and cohort analysis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from backend.src.marts.builder import _col_or_none, _col_or_zero, _safe_decimal


def build(df: pd.DataFrame) -> pd.DataFrame:
    """Build marketing mart from canonical transformed DataFrame."""
    cols = {
        "loan_id": df["loan_id"],
        "borrower_id": df["borrower_id"],
        "amount": _safe_decimal(df["amount"]),
        "status": df["status"],
        "origination_date": _col_or_none(df, "origination_date"),
        "advisory_channel": _col_or_none(df, "advisory_channel"),
        "kam_hunter": _col_or_none(df, "kam_hunter"),
        "credit_line": _col_or_none(df, "credit_line"),
        "dpd": _col_or_zero(df, "dpd").astype(int),
        "interest_rate": _col_or_zero(df, "interest_rate"),
        "tpv": _col_or_zero(df, "tpv"),
    }
    return pd.DataFrame(cols)


def build_with_ad_spend(
    pipeline_df: pd.DataFrame,
    ad_spend_df: Optional[pd.DataFrame],
) -> pd.DataFrame:
    """Build marketing mart enriched with Meta Ads spend data.

    Joins the canonical pipeline mart with a daily Meta Ads spend DataFrame
    (produced by ``MetaAdsAdapter.fetch_insights()``) on origination month.
    When ``ad_spend_df`` is None or empty, the mart is built without ad spend
    columns so the pipeline can still run without Meta Ads credentials.

    Parameters
    ----------
    pipeline_df:
        Canonical transformed DataFrame (same input as ``build()``).
    ad_spend_df:
        DataFrame of ``CanonicalAdSpendRecord`` rows (or None).
        Must contain at minimum: ``date_start``, ``spend``, ``leads``,
        ``impressions``, ``clicks``, ``campaign_name``.

    Returns
    -------
    pd.DataFrame
        Marketing mart with optional ad spend KPI columns:
        ``meta_spend``, ``meta_leads``, ``meta_impressions``,
        ``meta_clicks``, ``meta_cpl``, ``meta_ctr``.
    """
    mart = build(pipeline_df)

    if ad_spend_df is None or ad_spend_df.empty:
        return mart

    # Aggregate Meta Ads data to monthly level for joining
    ad = ad_spend_df.copy()
    ad["date_start"] = pd.to_datetime(ad["date_start"], errors="coerce")
    ad["origination_month"] = ad["date_start"].dt.to_period("M").astype(str)

    monthly_spend = (
        ad.groupby("origination_month")
        .agg(
            meta_spend=("spend", "sum"),
            meta_leads=("leads", "sum"),
            meta_impressions=("impressions", "sum"),
            meta_clicks=("clicks", "sum"),
        )
        .reset_index()
    )

    monthly_spend["meta_cpl"] = monthly_spend.apply(
        lambda r: r["meta_spend"] / r["meta_leads"] if r["meta_leads"] > 0 else None,
        axis=1,
    )
    monthly_spend["meta_ctr"] = monthly_spend.apply(
        lambda r: r["meta_clicks"] / r["meta_impressions"]
        if r["meta_impressions"] > 0
        else None,
        axis=1,
    )

    # Derive origination_month on the mart side for the join
    mart["origination_month"] = pd.to_datetime(
        mart["origination_date"], errors="coerce"
    ).dt.to_period("M").astype(str)

    enriched = mart.merge(monthly_spend, on="origination_month", how="left")
    enriched.drop(columns=["origination_month"], inplace=True)
    return enriched


def build_marketing_treemap_data(
    portfolio: pd.DataFrame,
    segment_col: str = "segment",
    channel_col: str = "advisory_channel",
    kam_col: str = "kam_hunter",
    balance_col: str = "outstanding_principal",
    loan_id_col: str = "loan_id",
) -> List[Dict[str, Any]]:
    """Build a flat hierarchical dataset suitable for a Plotly treemap.

    The hierarchy is:  **Segment → Channel → KAM**

    Each leaf row represents a unique (segment, channel, KAM) combination and
    carries the balance value and loan count.  Plotly's ``px.treemap`` accepts
    a flat list where each level is a column::

        fig = px.treemap(
            pd.DataFrame(build_marketing_treemap_data(portfolio)),
            path=["segment", "channel", "kam"],
            values="balance_usd",
            color="loan_count",
        )

    Parameters
    ----------
    portfolio:
        Portfolio mart DataFrame (output of ``build_portfolio_mart()`` or
        ``build()``).  Columns that are absent are filled with ``"Unknown"``.
    segment_col, channel_col, kam_col:
        Column names for the three hierarchy levels.
    balance_col:
        Numeric column to use as the leaf value (outstanding balance).
    loan_id_col:
        Column used to count distinct loans per leaf.

    Returns
    -------
    List of dicts with keys: ``segment``, ``channel``, ``kam``,
    ``balance_usd``, ``loan_count``, ``share_pct``.
    """
    if portfolio.empty:
        return []

    df = portfolio.copy()

    # Fill missing hierarchy columns gracefully
    for col, default in [(segment_col, "Unknown"), (channel_col, "Unknown"), (kam_col, "Unknown")]:
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default).astype(str)

    if balance_col in df.columns:
        df[balance_col] = pd.to_numeric(df[balance_col], errors="coerce").fillna(0)
    else:
        df[balance_col] = 0.0

    count_col = loan_id_col if loan_id_col in df.columns else None

    group_cols = [segment_col, channel_col, kam_col]
    agg: Dict[str, Any] = {balance_col: "sum"}
    if count_col:
        agg[count_col] = "count"

    grouped = df.groupby(group_cols).agg(agg).reset_index()

    total_balance = float(grouped[balance_col].sum()) or 1.0

    rows: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        bal = float(row[balance_col])
        rows.append({
            "segment": str(row[segment_col]),
            "channel": str(row[channel_col]),
            "kam": str(row[kam_col]),
            "balance_usd": round(bal, 2),
            "loan_count": int(row[count_col]) if count_col else 0,
            "share_pct": round(bal / total_balance * 100, 2),
        })

    return sorted(rows, key=lambda r: r["balance_usd"], reverse=True)

