"""
Portfolio Analytics — 5 modules fully buildable from existing data
===================================================================

All modules use only data already in data/raw/:
  loan_data.csv, real_payment.csv, payment_schedule.csv,
  customer.csv (equifax_score, categorialineacredito, client_type),
  collateral.csv (collateral_original, collateral_current)

Module A — cohort_pancake_analysis()
    36-month stacked cohort revenue (pancake model).
    Shows retention, expansion, and the "pancake effect" of cumulative cohorts.

Module B — payment_behavior_clustering()
    Behavioral segmentation from true_payment_status (On Time / Late / Prepayment).
    Produces 4 client personas: Excellent, Reliable, Erratic, At Risk.
    Direct input for collections strategy and PD model features.

Module C — collection_efficiency_by_segment()
    Per-loan, per-KAM, per-category CE = actual_collected / scheduled.
    Uses real_payment vs payment_schedule join. CE <80% = early warning flag.

Module D — collateral_coverage()
    LTC (Loan-to-Collateral) ratio per loan and by segment.
    All 18,101 loans have account_receivable collateral. Computes coverage haircut.

Module E — equifax_vs_dpd_scatter()
    Internal DPD vs external Equifax score scatter (section 3.0).
    Identifies "underwriting alpha" — clients outperforming their Equifax score.
    Regression line + outlier flagging for CRO/CMO review.

Module F — credit_line_category_kpis()
    Full KPI breakdown by CategoriaLineaCredito (A–H buckets from strategy doc).
    Rotation, default rate, APR, avg term, PAR by bucket.

Entry point: build_portfolio_analytics_report()
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, cast

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


# ─────────────────────────────────────────────────────────────────────────────
# A. Cohort Pancake Analysis
# ─────────────────────────────────────────────────────────────────────────────

def cohort_pancake_analysis(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    max_age_months: int = 24,
) -> dict[str, Any]:
    """
    36-month stacked cohort revenue — the "pancake" growth model.

    Each disbursement month becomes a cohort. Revenue from that cohort is
    tracked at each subsequent age (months since first disbursement).

    Returns
    -------
    {
        "cohort_matrix":   [{cohort, age_0_rev, age_1_rev, ..., total_rev, client_count}],
        "cumulative_rev":  [{cohort, cumulative_rev_usd}],
        "retention":       [{cohort, retention_pct_m1, m3, m6, m12}],
        "ltv_by_cohort":   [{cohort, ltv_usd, avg_age_months}],
        "pancake_summary": {oldest_cohort_rev_usd, newest_cohort_rev_usd, growth_factor},
    }
    """
    disb_col = _col(loans_df, ["disbursement_date", "FechaDesembolso"])
    loan_id  = _col(loans_df, ["loan_id", "Loan ID"])
    cust_col = _col(loans_df, ["customer_id", "Customer ID"])
    pay_date = _col(payments_df, ["true_payment_date", "payment_date"])
    pay_amt  = _col(payments_df, ["true_total_payment", "payment_amount"])

    if not all([disb_col, loan_id, pay_date, pay_amt]):
        return {"status": "missing_columns"}

    # Ensure columns are strings for Mypy
    disb_col_s = str(disb_col)
    loan_id_s = str(loan_id)
    pay_date_s = str(pay_date)
    pay_amt_s = str(pay_amt)

    loans = loans_df[[loan_id_s, cust_col, disb_col_s]].copy() if cust_col else loans_df[[loan_id_s, disb_col_s]].copy()
    loans["_cohort"] = pd.to_datetime(loans[disb_col_s], errors="coerce").dt.to_period("M")

    pay = payments_df[[loan_id_s, pay_date_s, pay_amt_s]].copy()
    pay["_pay_month"] = pd.to_datetime(pay[pay_date_s], errors="coerce").dt.to_period("M")
    pay["_amt"] = _num(pay, pay_amt_s)

    merged = pay.merge(loans[[loan_id_s, "_cohort"]], on=loan_id_s, how="left").dropna(subset=["_cohort"])
    merged["_age"] = (merged["_pay_month"] - merged["_cohort"]).apply(
        lambda x: x.n if hasattr(x, "n") else 0
    ).clip(lower=0, upper=max_age_months)

    # Cohort revenue matrix
    matrix = merged.groupby(["_cohort", "_age"])["_amt"].sum().unstack(fill_value=0)
    matrix = matrix.sort_index()

    # Client count per cohort
    if cust_col in loans_df.columns:
        coh_clients = loans_df.groupby(
            pd.to_datetime(loans_df[disb_col_s], errors="coerce").dt.to_period("M")
        )[cust_col].nunique().rename("client_count")
    else:
        coh_clients = pd.Series(dtype=int)

    cohort_rows = []
    for cohort, row in matrix.iterrows():
        rev_by_age = {f"age_{int(a)}m_usd": round(float(v), 2) for a, v in row.items()}
        cohort_rows.append({
            "cohort":       str(cohort),
            "total_rev_usd": round(float(row.sum()), 2),
            "client_count": int(coh_clients.get(cohort, 0)),
            **rev_by_age,
        })

    # Retention: % of cohort still generating revenue at age M
    retention = []
    for cohort, row in matrix.iterrows():
        base = float(row.get(0, 0))
        if base == 0:
            continue
        retention.append({
            "cohort":         str(cohort),
            "retention_m1":   round(float(row.get(1, 0)) / base * 100, 1),
            "retention_m3":   round(float(row.get(3, 0)) / base * 100, 1),
            "retention_m6":   round(float(row.get(6, 0)) / base * 100, 1),
            "retention_m12":  round(float(row.get(12, 0)) / base * 100, 1),
        })

    # LTV by cohort
    ltv_rows = [
        {
            "cohort":       str(row["cohort"]),
            "ltv_usd":      round(float(cast(float, row["total_rev_usd"])) / max(int(cast(int, row["client_count"])), 1), 2),
            "total_rev_usd": float(cast(float, row["total_rev_usd"])),
        }
        for row in cohort_rows if int(cast(int, row["client_count"])) > 0
    ]

    # Pancake summary: first vs most recent non-zero cohort
    non_zero = [r for r in cohort_rows if float(cast(float, r["total_rev_usd"])) > 0]
    pancake_summary = {}
    if len(non_zero) >= 2:
        oldest_rev = float(cast(float, non_zero[0]["total_rev_usd"]))
        newest_rev = float(cast(float, non_zero[-1]["total_rev_usd"]))
        pancake_summary = {
            "oldest_cohort":      str(non_zero[0]["cohort"]),
            "oldest_rev_usd":     oldest_rev,
            "newest_cohort":      str(non_zero[-1]["cohort"]),
            "newest_rev_usd":     newest_rev,
            "growth_factor":      round(newest_rev / max(oldest_rev, 1.0), 2),
            "total_cohorts":      len(non_zero),
            "stacked_rev_total":  round(sum(float(cast(float, r["total_rev_usd"])) for r in non_zero), 2),
        }

    return {
        "status":          "ok",
        "cohort_matrix":   cohort_rows,
        "retention":       retention,
        "ltv_by_cohort":   ltv_rows,
        "pancake_summary": pancake_summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# B. Payment Behavior Clustering
# ─────────────────────────────────────────────────────────────────────────────

def payment_behavior_clustering(
    payments_df: pd.DataFrame,
    loans_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Rule-based behavioral segmentation from true_payment_status.

    Features per client:
        - late_rate:      % payments marked 'Late'
        - prepay_rate:    % payments marked 'Prepayment'
        - ontime_rate:    % payments 'On Time'
        - avg_dpd:        from days_in_default in loan_data
        - devolution_rate: % payments with true_devolution > 0

    Personas (rule-based, interpretable):
        EXCELLENT:   late_rate < 10% AND prepay_rate > 20%
        RELIABLE:    late_rate < 25% AND ontime_rate > 50%
        ERRATIC:     late_rate 25-60% (pays eventually but inconsistently)
        AT_RISK:     late_rate > 60% OR avg_dpd > 30

    Returns
    -------
    {
        "personas": [{customer_id, persona, late_rate, prepay_rate, ontime_rate, avg_dpd, op_count}],
        "persona_summary": {EXCELLENT: N, RELIABLE: N, ERRATIC: N, AT_RISK: N},
        "portfolio_balance_by_persona": {persona: usd},
        "collections_priority": [{customer_id, persona, balance_usd, late_rate}],
    }
    """
    cust_col  = _col(payments_df, ["customer_id", "CodCliente"])
    stat_col  = _col(payments_df, ["true_payment_status", "payment_status"])
    dev_col   = _col(payments_df, ["true_devolution", "devolution"])
    loan_cust = _col(loans_df, ["customer_id"])
    dpd_col   = _col(loans_df, ["days_in_default", "days_past_due", "dpd"])
    bal_col   = _col(loans_df, ["outstanding_loan_value", "outstanding_balance"])

    if not cust_col or not stat_col:
        return {"status": "missing_columns", "required": ["customer_id", "true_payment_status"]}

    pay = payments_df.copy()
    pay[stat_col] = pay[stat_col].astype(str).str.strip()
    if dev_col:
        pay["_dev"] = _num(pay, dev_col)

    # Per-client payment stats
    def _rates(grp: pd.DataFrame) -> pd.Series:
        n = len(grp)
        return pd.Series({
            "op_count":    n,
            "late_rate":   (grp[stat_col] == "Late").sum() / n,
            "prepay_rate": (grp[stat_col] == "Prepayment").sum() / n,
            "ontime_rate": (grp[stat_col] == "On Time").sum() / n,
            "dev_rate":    (grp["_dev"] > 0).sum() / n if dev_col in grp.columns else 0.0,
        })

    stats = pay.groupby(cust_col).apply(_rates).reset_index()
    stats.columns = [cust_col, "op_count", "late_rate", "prepay_rate", "ontime_rate", "dev_rate"]

    # Merge DPD from loan tape
    if loan_cust and dpd_col:
        avg_dpd = loans_df.groupby(loan_cust)[dpd_col].apply(
            lambda s: pd.to_numeric(s, errors="coerce").mean()
        ).rename("avg_dpd").reset_index()
        avg_dpd.columns = [cust_col, "avg_dpd"]
        stats = stats.merge(avg_dpd, on=cust_col, how="left")
        stats["avg_dpd"] = stats["avg_dpd"].fillna(0)
    else:
        stats["avg_dpd"] = 0.0

    # Persona assignment
    def _persona(row: pd.Series) -> str:
        if row["late_rate"] > 0.60 or row["avg_dpd"] > 30:
            return "AT_RISK"
        if row["late_rate"] < 0.10 and row["prepay_rate"] > 0.20:
            return "EXCELLENT"
        if row["late_rate"] < 0.25 and row["ontime_rate"] > 0.50:
            return "RELIABLE"
        return "ERRATIC"

    stats["persona"] = stats.apply(_persona, axis=1)

    # Balance by persona
    bal_by_persona: dict[str, float] = {}
    if loan_cust and bal_col:
        bal_map = loans_df.groupby(loan_cust)[bal_col].apply(
            lambda s: pd.to_numeric(s, errors="coerce").sum()
        ).to_dict()
        stats["_bal"] = stats[cust_col].map(bal_map).fillna(0)
        bal_by_persona = stats.groupby("persona")["_bal"].sum().round(2).to_dict()

    persona_summary = stats["persona"].value_counts().to_dict()

    # Collections priority: AT_RISK + ERRATIC sorted by balance
    priority = (
        stats[stats["persona"].isin(["AT_RISK", "ERRATIC"])]
        .sort_values("_bal" if "_bal" in stats.columns else "late_rate", ascending=False)
        [([cust_col, "persona", "_bal", "late_rate", "avg_dpd", "op_count"]
          if "_bal" in stats.columns
          else [cust_col, "persona", "late_rate", "avg_dpd", "op_count"])]
        .head(50)
    )
    if "_bal" in priority.columns:
        priority = priority.rename(columns={"_bal": "balance_usd"})

    personas_out = []
    for _, row in stats.iterrows():
        personas_out.append({
            "customer_id":  str(row[cust_col]),
            "persona":      row["persona"],
            "late_rate":    round(float(row["late_rate"]), 3),
            "prepay_rate":  round(float(row["prepay_rate"]), 3),
            "ontime_rate":  round(float(row["ontime_rate"]), 3),
            "avg_dpd":      round(float(row["avg_dpd"]), 1),
            "op_count":     int(row["op_count"]),
        })

    return {
        "status":                     "ok",
        "personas":                   sorted(personas_out, key=lambda x: x["late_rate"], reverse=True),
        "persona_summary":            persona_summary,
        "portfolio_balance_by_persona": {k: float(v) for k, v in bal_by_persona.items()},
        "collections_priority":       priority.to_dict("records"),
        "persona_definitions": {
            "EXCELLENT": "late_rate < 10% AND prepay_rate > 20%",
            "RELIABLE":  "late_rate < 25% AND ontime_rate > 50%",
            "ERRATIC":   "late_rate 25-60%, eventually pays",
            "AT_RISK":   "late_rate > 60% OR avg_dpd > 30",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# C. Collection Efficiency by Segment
# ─────────────────────────────────────────────────────────────────────────────

def collection_efficiency_by_segment(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    schedule_df: pd.DataFrame,
    customer_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """
    Collection Efficiency = actual_collected / scheduled_payment per loan.

    CE by: overall, CategoriaLineaCredito bucket, KAM/sales_agent, client_type.
    Flags loans with CE < 0.80 as early warning flag.
    """
    loan_id   = _col(loans_df, ["loan_id"])
    sched_amt = _col(schedule_df, ["total_payment", "payment_amount"])
    real_amt  = _col(payments_df, ["true_total_payment", "payment_amount"])
    cat_col   = _col(loans_df, ["categorialineacredito", "credit_line_category"])
    agent_col = _col(loans_df, ["sales_agent", "kam"]) or (
        _col(customer_df, ["sales_agent"]) if customer_df is not None else None
    )

    if not all([loan_id, sched_amt, real_amt]):
        return {"status": "missing_columns"}

    sched_agg = (schedule_df.groupby(loan_id)[sched_amt]
                 .apply(lambda s: pd.to_numeric(s, errors="coerce").fillna(0).sum())
                 .rename("sched"))
    real_agg  = (payments_df.groupby(loan_id)[real_amt]
                 .apply(lambda s: pd.to_numeric(s, errors="coerce").fillna(0).sum())
                 .rename("real"))

    ce = sched_agg.to_frame().join(real_agg, how="outer").fillna(0)
    ce["ce_ratio"] = ce["real"] / ce["sched"].replace(0, np.nan)

    meta_cols = [loan_id] + [c for c in [cat_col] if c]
    # only add agent_col if it exists in loans_df
    if agent_col and agent_col in loans_df.columns:
        meta_cols.append(agent_col)
    loans_meta = loans_df[meta_cols].copy()
    if customer_df is not None and agent_col and agent_col not in loans_meta.columns:
        if loan_id in customer_df.columns and agent_col in customer_df.columns:
            ag = customer_df[[loan_id, agent_col]].drop_duplicates(loan_id)
            loans_meta = loans_meta.merge(ag, on=loan_id, how="left")

    ce = ce.reset_index().merge(loans_meta, on=loan_id, how="left")

    overall = {
        "loans_with_ce_data": int(ce["ce_ratio"].notna().sum()),
        "ce_median":          round(float(ce["ce_ratio"].median()), 3),
        "ce_mean":            round(float(ce["ce_ratio"].mean()), 3),
        "ce_gte_1_pct":       round(float((ce["ce_ratio"] >= 1.0).mean() * 100), 1),
        "ce_lt_80_pct":       round(float((ce["ce_ratio"] < 0.80).mean() * 100), 1),
        "ce_lt_80_balance_usd": 0.0,
    }

    # Add balance to CE <0.80 flag
    if "outstanding_loan_value" in loans_df.columns:
        bal_map = loans_df.set_index(loan_id)["outstanding_loan_value"].to_dict()
        ce["_bal"] = ce[loan_id].map(bal_map).fillna(0)
        overall["ce_lt_80_balance_usd"] = round(
            float(ce.loc[ce["ce_ratio"] < 0.80, "_bal"].sum()), 2
        )

    # By category
    by_category: list[dict] = []
    if cat_col and cat_col in ce.columns:
        for cat, grp in ce.groupby(cat_col, dropna=False):
            by_category.append({
                "category":   str(cat),
                "ce_median":  round(float(grp["ce_ratio"].median()), 3),
                "ce_mean":    round(float(grp["ce_ratio"].mean()), 3),
                "loan_count": int(len(grp)),
                "ce_lt_80_n": int((grp["ce_ratio"] < 0.80).sum()),
            })
        by_category.sort(key=lambda x: x["ce_median"])

    # By KAM
    by_kam: list[dict] = []
    if agent_col and agent_col in ce.columns:
        for agent, grp in ce.groupby(agent_col, dropna=False):
            by_kam.append({
                "agent":       str(agent),
                "ce_median":   round(float(grp["ce_ratio"].median()), 3),
                "loan_count":  int(len(grp)),
            })
        by_kam.sort(key=lambda x: x["ce_median"])

    # Early warning list
    early_warning = (
        ce[ce["ce_ratio"] < 0.80]
        .sort_values("ce_ratio")
        [[loan_id, "sched", "real", "ce_ratio"] +
         ([cat_col] if cat_col and cat_col in ce.columns else []) +
         (["_bal"] if "_bal" in ce.columns else [])]
        .head(50)
        .rename(columns={"_bal": "outstanding_usd"})
        .round(3)
        .to_dict("records")
    )

    return {
        "status":         "ok",
        "overall":        overall,
        "by_category":    by_category,
        "by_kam":         by_kam,
        "early_warning":  early_warning,
    }


# ─────────────────────────────────────────────────────────────────────────────
# D. Collateral Coverage
# ─────────────────────────────────────────────────────────────────────────────

def collateral_coverage(
    loans_df: pd.DataFrame,
    collateral_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Loan-to-Collateral (LTC) coverage analysis.

    All 18,101 loans in Abaco have account_receivable collateral (the invoice itself).
    collateral_original = face value of invoice
    collateral_current  = current estimated value (post-haircut)

    LTC = outstanding_loan_value / collateral_current
    LTC > 1.0 = undercollateralized (risk flag)
    LTC < 0.9 = well-collateralized (buffer > 10%)
    """
    loan_id  = _col(loans_df, ["loan_id"])
    bal_col  = _col(loans_df, ["outstanding_loan_value"])
    cat_col  = _col(loans_df, ["categorialineacredito", "credit_line_category"])
    col_orig = _col(collateral_df, ["collateral_original"])
    col_curr = _col(collateral_df, ["collateral_current"])

    if not all([loan_id, bal_col, col_curr]):
        return {"status": "missing_columns"}

    coll_agg = (collateral_df.groupby(loan_id)
                [[col_orig, col_curr]]
                .sum()
                .rename(columns={col_orig: "coll_orig", col_curr: "coll_curr"}))

    df = loans_df[[loan_id] + [c for c in [bal_col, cat_col] if c]].copy()
    df["_bal"] = _num(df, str(bal_col))
    df = df.merge(coll_agg, on=loan_id, how="left").fillna(0)
    df["ltc_ratio"]     = df["_bal"] / df["coll_curr"].replace(0, np.nan)
    df["haircut_pct"]   = (1 - df["coll_curr"] / df["coll_orig"].replace(0, np.nan)) * 100
    df["overcollat_pct"]= (df["coll_curr"] / df["_bal"].replace(0, np.nan) - 1) * 100

    total_bal  = df["_bal"].sum()
    total_coll = df["coll_curr"].sum()

    overall = {
        "total_outstanding_usd":    round(float(total_bal), 2),
        "total_collateral_usd":     round(float(total_coll), 2),
        "portfolio_ltc_ratio":      round(float(total_bal / total_coll), 3) if total_coll > 0 else None,
        "portfolio_coverage_pct":   round(float(total_coll / total_bal * 100), 1) if total_bal > 0 else None,
        "ltc_gt_1_undercollat_n":   int((df["ltc_ratio"] > 1.0).sum()),
        "ltc_gt_1_balance_usd":     round(float(df.loc[df["ltc_ratio"] > 1.0, "_bal"].sum()), 2),
        "ltc_lt_0_9_wellcollat_n":  int((df["ltc_ratio"] < 0.90).sum()),
        "median_haircut_pct":       round(float(df["haircut_pct"].median()), 1),
        "collateral_type":          "account_receivable (invoice factoring)",
    }

    # By category
    by_cat: list[dict] = []
    if cat_col and cat_col in df.columns:
        cat_col_s = str(cat_col)
        for cat, grp in df.groupby(cat_col_s, dropna=False):
            by_cat.append({
                "category":          str(cat),
                "median_ltc_ratio":  round(float(grp["ltc_ratio"].median()), 3),
                "undercollat_n":     int((grp["ltc_ratio"] > 1.0).sum()),
                "loan_count":        int(len(grp)),
                "total_balance_usd": round(float(grp["_bal"].sum()), 2),
            })
        by_cat.sort(key=lambda x: float(x["median_ltc_ratio"]), reverse=True)

    return {
        "status":       "ok",
        "overall":      overall,
        "by_category":  by_cat,
    }


# ─────────────────────────────────────────────────────────────────────────────
# E. Equifax vs DPD Scatter (Underwriting Alpha — section 3.0)
# ─────────────────────────────────────────────────────────────────────────────

def equifax_vs_dpd_scatter(
    loans_df: pd.DataFrame,
    customer_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Scatter of external Equifax score vs internal DPD.
    Identifies "underwriting alpha" — clients with low DPD relative to their
    external score (outperforming Equifax prediction).

    Regression line: expected_dpd = a × equifax_score + b
    Clients significantly BELOW the line are alpha candidates (lower risk than
    Equifax predicts → potential for strategic expansion at current pricing).

    Returns
    -------
    {
        "scatter_data": [{customer_id, equifax_score, actual_dpd, expected_dpd, residual, alpha_flag}],
        "regression":   {slope, intercept, r_squared},
        "alpha_clients": [{...}],   # DPD < expected - 1.5σ (outperforming)
        "risk_clients":  [{...}],   # DPD > expected + 1.5σ (underperforming)
        "summary": {n_total, n_alpha, n_risk, alpha_balance_usd},
    }
    """
    cust_col = _col(customer_df, ["customer_id", "Customer ID"])
    eqfx_col = _col(customer_df, ["equifax_score", "external_credit_score"])
    loan_id  = _col(loans_df, ["loan_id"])
    dpd_col  = _col(loans_df, ["days_in_default", "days_past_due", "dpd"])
    bal_col  = _col(loans_df, ["outstanding_loan_value"])
    cust_loan= _col(loans_df, ["customer_id"])

    if not eqfx_col or not dpd_col:
        return {"status": "missing_columns", "required": ["equifax_score", "days_in_default"]}

    # Average DPD per customer
    dpd_by_cust = (
        loans_df.groupby(cust_loan)
        .agg(
            avg_dpd=(dpd_col, lambda s: pd.to_numeric(s, errors="coerce").mean()),
            max_dpd=(dpd_col, lambda s: pd.to_numeric(s, errors="coerce").max()),
            total_bal=(bal_col, lambda s: pd.to_numeric(s, errors="coerce").sum()) if bal_col else (dpd_col, "count"),
            op_count=(loan_id, "count"),
        )
        .reset_index()
        .rename(columns={cust_loan: cust_col})
    )

    # Merge Equifax
    eqfx = customer_df[[cust_col, eqfx_col]].dropna(subset=[eqfx_col]).drop_duplicates(cust_col)
    df   = eqfx.merge(dpd_by_cust, on=cust_col, how="inner")
    df   = df.dropna(subset=["avg_dpd"])
    df["_eq"] = pd.to_numeric(df[eqfx_col], errors="coerce")
    df["_dpd"]= pd.to_numeric(df["avg_dpd"], errors="coerce")
    df = df.dropna(subset=["_eq", "_dpd"])

    if len(df) < 10:
        return {"status": "insufficient_data", "n_rows": len(df)}

    # Linear regression: DPD ~ Equifax
    eq_vals  = df["_eq"].values
    dpd_vals = df["_dpd"].values
    slope, intercept = np.polyfit(eq_vals, dpd_vals, 1)
    y_pred   = slope * eq_vals + intercept
    ss_res   = float(np.sum((dpd_vals - y_pred) ** 2))
    ss_tot   = float(np.sum((dpd_vals - dpd_vals.mean()) ** 2))
    r_sq     = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    df["_expected_dpd"] = y_pred
    df["_expected_dpd"] = df["_expected_dpd"].clip(lower=0) # DPD can't be negative
    df["_residual"]     = df["_dpd"] - df["_expected_dpd"]
    residual_std = float(df["_residual"].std())

    # Alpha threshold: residual < -1.5σ (outperforming Equifax)
    df["_alpha_flag"] = df["_residual"] < -1.5 * residual_std
    df["_risk_flag"]  = df["_residual"] >  1.5 * residual_std

    scatter_data = []
    for _, row in df.iterrows():
        scatter_data.append({
            "customer_id":    str(row[cust_col]),
            "equifax_score":  round(float(row["_eq"]), 1),
            "actual_dpd":     round(float(row["_dpd"]), 1),
            "expected_dpd":   round(float(row["_expected_dpd"]), 1),
            "residual":       round(float(row["_residual"]), 1),
            "alpha_flag":     bool(row["_alpha_flag"]),
            "risk_flag":      bool(row["_risk_flag"]),
            "total_balance_usd": round(float(row.get("total_bal", 0)), 2),
        })

    alpha_clients = [s for s in scatter_data if s["alpha_flag"]]
    risk_clients  = [s for s in scatter_data if s["risk_flag"]]

    alpha_balance = sum(float(cast(float, s["total_balance_usd"])) for s in alpha_clients)

    return {
        "status": "ok",
        "scatter_data": scatter_data,
        "regression": {
            "slope":      round(float(slope), 6),
            "intercept":  round(float(intercept), 2),
            "r_squared":  round(float(r_sq), 4),
            "interpretation": (
                f"Each 1-point rise in Equifax score changes expected DPD by "
                f"{slope:+.3f} days. R²={r_sq:.3f} — "
                + ("weak" if r_sq < 0.1 else "moderate" if r_sq < 0.3 else "strong")
                + " predictive power."
            ),
        },
        "alpha_clients":  sorted(alpha_clients, key=lambda x: float(cast(float, x["residual"])))[:30],
        "risk_clients":   sorted(risk_clients,  key=lambda x: float(cast(float, x["residual"])), reverse=True)[:30],
        "summary": {
            "n_total":           len(scatter_data),
            "n_alpha":           len(alpha_clients),
            "n_risk":            len(risk_clients),
            "alpha_balance_usd": round(float(alpha_balance), 2),
            "alpha_pct_of_n":    round(len(alpha_clients) / max(len(scatter_data), 1) * 100, 1),
            "residual_std":      round(residual_std, 2),
            "threshold_used":    "residual < -1.5σ for alpha; > +1.5σ for risk",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# F. Credit Line Category KPIs (A–H buckets)
# ─────────────────────────────────────────────────────────────────────────────

def credit_line_category_kpis(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """
    Full KPI breakdown by CategoriaLineaCredito (A–H strategy doc buckets).

    Per bucket: N loans, AUM, avg ticket, avg term, APR, rotation, default rate,
    PAR30, PAR90, prepayment rate, revenue.
    """
    loan_id  = _col(loans_df, ["loan_id"])
    cat_col  = _col(loans_df, ["categorialineacredito", "credit_line_category"])
    bal_col  = _col(loans_df, ["outstanding_loan_value"])
    disb_col = _col(loans_df, ["disbursement_amount"])
    apr_col  = _col(loans_df, ["interest_rate_apr"])
    term_col = _col(loans_df, ["term"])
    dpd_col  = _col(loans_df, ["days_in_default", "days_past_due"])
    stat_col = _col(loans_df, ["loan_status"])
    tpv_col  = _col(loans_df, ["tpv", "TPV"])

    if not cat_col:
        return {"status": "no_category_column"}

    df = loans_df.copy()
    for c in [bal_col, disb_col, apr_col, term_col, dpd_col, tpv_col]:
        if c:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    if stat_col:
        df["_default"] = df[stat_col].astype(str).str.lower().str.contains(
            "default|defaulted", na=False
        ).astype(int)
    else:
        df["_default"] = 0

    # Revenue by loan from payments
    rev_by_loan: dict = {}
    if payments_df is not None:
        pay_lid = _col(payments_df, ["loan_id"])
        pay_amt = _col(payments_df, ["true_total_payment", "payment_amount"])
        if pay_lid and pay_amt:
            rev_by_loan = (
                payments_df.groupby(pay_lid)[pay_amt]
                .apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
                .to_dict()
            )
    if loan_id:
        df["_rev"] = df[loan_id].map(rev_by_loan).fillna(0)
    else:
        df["_rev"] = 0.0

    rows = []
    for cat, grp in df.groupby(cat_col, dropna=False):
        bal   = _num(grp, bal_col)  if bal_col  else pd.Series([0.0])
        disb  = _num(grp, disb_col) if disb_col else pd.Series([0.0])
        apr   = _num(grp, apr_col)  if apr_col  else pd.Series([0.0])
        term  = _num(grp, term_col) if term_col else pd.Series([0.0])
        dpd   = _num(grp, dpd_col)  if dpd_col  else pd.Series([0.0])
        total = float(bal.sum())

        rows.append({
            "category":           str(cat),
            "loan_count":         int(len(grp)),
            "aum_usd":            round(float(bal.sum()), 2),
            "avg_ticket_usd":     round(float(disb.mean()), 2),
            "median_ticket_usd":  round(float(disb.median()), 2),
            "apr_weighted":       round(float((apr * disb).sum() / max(disb.sum(), 1)), 4),
            "avg_term_days":      round(float(term.mean()), 1),
            "rotation_x":         round(365 / term.mean(), 1) if term.mean() > 0 else None,
            "default_rate_pct":   round(float(grp["_default"].mean() * 100), 2),
            "par30_pct":          round(float(bal[dpd >= 30].sum() / total * 100), 1) if total > 0 else 0.0,
            "par90_pct":          round(float(bal[dpd >= 90].sum() / total * 100), 1) if total > 0 else 0.0,
            "revenue_usd":        round(float(grp["_rev"].sum()), 2),
            "revenue_per_loan":   round(float(grp["_rev"].mean()), 2),
        })

    rows.sort(key=lambda x: float(cast(float, x["aum_usd"])), reverse=True)

    # Strategy doc benchmarks by bucket
    _STRATEGY_TARGETS: dict[str, dict[str, float]] = {
        ">$200K":    {"target_rotation": 4.9, "max_default": 1.8},
        "$150-200K": {"target_rotation": 5.1, "max_default": 2.5},
        "$100-150K": {"target_rotation": 5.4, "max_default": 3.1},
        "$75-100K":  {"target_rotation": 5.6, "max_default": 3.5},
        "$50-75K":   {"target_rotation": 6.0, "max_default": 3.8},
        "$25-50K":   {"target_rotation": 6.3, "max_default": 4.2},
        "$10-25K":   {"target_rotation": 6.6, "max_default": 4.5},
        "< $10K":    {"target_rotation": 7.0, "max_default": 4.9},
    }
    for row in rows:
        cat_s = str(row["category"])
        targets = _STRATEGY_TARGETS.get(cat_s, {})
        if targets:
            tgt_rot = targets.get("target_rotation", 0.0)
            max_def = targets.get("max_default", 99.0)
            act_rot = row.get("rotation_x")

            row["target_rotation"] = tgt_rot
            row["rotation_status"] = (
                "ok" if act_rot is not None and float(cast(float, act_rot)) >= tgt_rot
                else "below_target"
            )
            row["default_status"] = (
                "ok" if float(cast(float, row["default_rate_pct"])) <= max_def
                else "breach"
            )
        else:
            row["target_rotation"] = None
            row["rotation_status"] = None
            row["default_status"] = None

    return {
        "status":    "ok",
        "by_category": rows,
        "total_categories": len(rows),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Master Report
# ─────────────────────────────────────────────────────────────────────────────

def build_portfolio_analytics_report(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    schedule_df: pd.DataFrame,
    customer_df: pd.DataFrame,
    collateral_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Run all 6 portfolio analytics modules and return consolidated report.
    Merges into exports/complete_kpi_dashboard.json under 'portfolio_analytics'.
    """
    logger.info("Running portfolio_analytics: cohort, behavior, CE, collateral, equifax, credit_cat")

    cohort  = cohort_pancake_analysis(loans_df, payments_df)
    persona = payment_behavior_clustering(payments_df, loans_df)
    ce      = collection_efficiency_by_segment(loans_df, payments_df, schedule_df, customer_df)
    coll    = collateral_coverage(loans_df, collateral_df)
    scatter = equifax_vs_dpd_scatter(loans_df, customer_df)
    cat_kpi = credit_line_category_kpis(loans_df, payments_df)

    return {
        "generated_at":                datetime.now(timezone.utc).isoformat(),
        "cohort_pancake":              cohort,
        "payment_behavior_personas":   persona,
        "collection_efficiency":       ce,
        "collateral_coverage":         coll,
        "equifax_dpd_scatter":         scatter,
        "credit_line_category_kpis":   cat_kpi,
    }
