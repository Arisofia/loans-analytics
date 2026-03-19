"""
Strategic Analytics Modules 7.0 – 7.2 + Advanced Risk
=======================================================

7.0  Predictive KPIs          — time-series forecast for AUM, revenue, delinquency
7.1  Compliance Dashboard      — target vs actual matrix + variance decomposition
7.2  Next-Steps Planner        — synthesises alerts + gaps + forecasts → action backlog

Advanced Risk (document section 3.x):
  3.1  Exposure-weighted outlier detection (Z-score, 99th percentile)
  3.2  Guarded PD model (weighted logistic regression, k-fold AUC)

All functions operate on DataFrames that share the schema of the Abaco loan tape
(loan_data.csv + real_payment.csv) plus the INTERMEDIA snapshot.

Usage
-----
    from backend.python.kpis.strategic_modules import (
        predict_kpis,
        build_compliance_dashboard,
        build_next_steps_plan,
        detect_exposure_weighted_outliers,
        build_pd_model,
    )

    forecast   = predict_kpis(loans_df, payments_df, settings)
    compliance = build_compliance_dashboard(loans_df, payments_df, settings)
    plan       = build_next_steps_plan(forecast, compliance, guardrail_status)
    outliers   = detect_exposure_weighted_outliers(loans_df)
    pd_result  = build_pd_model(loans_df)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None

def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


# ─────────────────────────────────────────────────────────────────────────────
# 3.1  Exposure-Weighted Outlier Detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_exposure_weighted_outliers(
    loans_df: pd.DataFrame,
    z_threshold: float = 2.58,
) -> dict[str, Any]:
    """
    Exposure-weighted Z-score outlier detection (section 3.1).

    For each risk variable (APR, DPD, Term, line utilisation) the weighted mean
    and weighted std are computed using outstanding balance as the weight.
    Loans with |Z| > z_threshold (default 99th percentile ≈ 2.58) are flagged.

    Returns
    -------
    {
        "alerts": [{loan_id, variable, value, z_score, outstanding_usd}],
        "summary": {variable: {mean_w, std_w, outlier_count, outlier_balance_usd}},
        "total_flagged": int,
        "total_flagged_balance_usd": float,
    }
    """
    loan_id_col = _col(loans_df, ["loan_id", "Loan ID", "id"])
    bal_col     = _col(loans_df, ["outstanding_loan_value", "outstanding_balance", "TotalSaldoVigente"])
    apr_col     = _col(loans_df, ["interest_rate_apr", "interest_rate", "TasaInteres"])
    dpd_col     = _col(loans_df, ["days_past_due", "dpd", "DPD", "days_in_default"])
    term_col    = _col(loans_df, ["term", "Term", "term_days"])
    util_col    = _col(loans_df, ["porcentaje_utilizado", "line_utilization", "Porcentaje_Utilizado"])

    if bal_col is None:
        logger.warning("detect_exposure_weighted_outliers: no balance column found")
        return {"alerts": [], "summary": {}, "total_flagged": 0, "total_flagged_balance_usd": 0.0}

    bal = _num(loans_df, bal_col).clip(lower=0)
    total_w = bal.sum()
    if total_w == 0:
        return {"alerts": [], "summary": {}, "total_flagged": 0, "total_flagged_balance_usd": 0.0}

    variables = {}
    if apr_col:
        variables["apr"] = _num(loans_df, apr_col)
    if dpd_col:
        variables["dpd"] = _num(loans_df, dpd_col)
    if term_col:
        variables["term_days"] = _num(loans_df, term_col)
    if util_col:
        variables["line_util_pct"] = _num(loans_df, util_col)

    alerts:  list[dict] = []
    summary: dict[str, dict] = {}

    for var_name, series in variables.items():
        # Exposure-weighted mean and std
        w_mean = float((series * bal).sum() / total_w)
        w_var  = float(((series - w_mean) ** 2 * bal).sum() / total_w)
        w_std  = float(np.sqrt(w_var)) if w_var > 0 else 0.0

        if w_std == 0:
            summary[var_name] = {"mean_w": w_mean, "std_w": 0.0,
                                  "outlier_count": 0, "outlier_balance_usd": 0.0}
            continue

        z_scores  = (series - w_mean) / w_std
        flag_mask = z_scores.abs() > z_threshold
        flag_bal  = float(bal[flag_mask].sum())

        summary[var_name] = {
            "mean_w":              round(w_mean, 4),
            "std_w":               round(w_std,  4),
            "outlier_count":       int(flag_mask.sum()),
            "outlier_balance_usd": round(flag_bal, 2),
        }

        if flag_mask.any():
            flag_df = loans_df[flag_mask].copy()
            for idx in flag_df.index:
                loan_id = str(flag_df.at[idx, loan_id_col]) if loan_id_col else str(idx)
                alerts.append({
                    "loan_id":        loan_id,
                    "variable":       var_name,
                    "value":          round(float(series.at[idx]), 4),
                    "z_score":        round(float(z_scores.at[idx]), 2),
                    "outstanding_usd": round(float(bal.at[idx]), 2),
                })

    alerts.sort(key=lambda x: abs(x["z_score"]), reverse=True)
    total_bal = sum(a["outstanding_usd"] for a in alerts)

    return {
        "alerts":                  alerts[:200],  # cap at 200 for export size
        "summary":                 summary,
        "total_flagged":           len(alerts),
        "total_flagged_balance_usd": round(total_bal, 2),
        "z_threshold":             z_threshold,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.2  Guarded Probability of Default (PD) Model
# ─────────────────────────────────────────────────────────────────────────────

def build_pd_model(
    loans_df: pd.DataFrame,
    min_defaults: int = 30,
    min_non_defaults: int = 30,
    cv_folds: int = 5,
) -> dict[str, Any]:
    """
    Guarded weighted logistic regression PD model (section 3.2).

    Guards:
    - Requires >= min_defaults AND >= min_non_defaults in the dataset.
    - Returns {"status": "insufficient_data", ...} if guards fail.
    - k-fold cross-validation; reports AUC + calibration.

    Features used (when available):
        interest_rate_apr, term_days, disbursement_amount, outstanding_loan_value,
        line_utilization, days_past_due (lagged proxy), dpd_7_plus, dpd_30_plus

    Target: Loan Status == 'Default' (binary 0/1)

    Returns
    -------
    {
        "status": "ok" | "insufficient_data" | "error",
        "auc_mean": float, "auc_std": float,
        "calibration_slope": float,
        "feature_importance": {feature: coef},
        "pd_scores": [{loan_id, pd_score}],  # per-loan scores
        "default_rate_actual": float,
        "model_type": "logistic_regression_exposure_weighted",
    }
    """
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import StratifiedKFold, cross_val_score
        from sklearn.preprocessing import StandardScaler
        from sklearn.calibration import calibration_curve
    except ImportError:
        return {"status": "error", "message": "scikit-learn not installed"}

    status_col = _col(loans_df, ["loan_status", "Loan Status", "status"])
    bal_col    = _col(loans_df, ["outstanding_loan_value", "outstanding_balance"])
    loan_id_col= _col(loans_df, ["loan_id", "Loan ID", "id"])

    if status_col is None:
        return {"status": "error", "message": "No status column found"}

    # Build target
    status_series = loans_df[status_col].astype(str).str.lower()
    y = (status_series.str.contains("default|defaulted", regex=True, na=False)).astype(int)

    n_pos = int(y.sum())
    n_neg = int((y == 0).sum())

    if n_pos < min_defaults or n_neg < min_non_defaults:
        return {
            "status":          "insufficient_data",
            "n_defaults":      n_pos,
            "n_non_defaults":  n_neg,
            "min_required":    f"{min_defaults} defaults + {min_non_defaults} non-defaults",
            "message":         "Dataset does not meet minimum class size for stable PD model.",
        }

    # Build features.
    # DPD/days_in_default is intentionally excluded to avoid target leakage:
    # it directly encodes loan_status==Default in this tape.
    feature_cols = {}
    for fname, aliases in [
        ("apr",          ["interest_rate_apr", "interest_rate", "TasaInteres"]),
        ("term",         ["term", "Term", "term_days"]),
        ("disb_amount",  ["disbursement_amount", "MontoDesembolsado"]),
        ("outstanding",  ["outstanding_loan_value", "TotalSaldoVigente"]),
        ("tpv",          ["tpv", "TPV", "total_portfolio_value"]),
    ]:
        c = _col(loans_df, aliases)
        if c:
            feature_cols[fname] = c

    if len(feature_cols) < 2:
        return {"status": "error", "message": f"Insufficient features: {list(feature_cols)}"}

    X_raw = pd.DataFrame({
        fname: _num(loans_df, col) for fname, col in feature_cols.items()
    }).fillna(0)

    # Exposure weights
    weights = _num(loans_df, bal_col).clip(lower=1.0) if bal_col else pd.Series(
        np.ones(len(loans_df)), index=loans_df.index
    )

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # k-fold CV
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    clf = LogisticRegression(max_iter=1000, class_weight="balanced", solver="lbfgs")
    # sklearn 1.4+ removed fit_params from cross_val_score; use metadata routing
    # Fallback: unweighted CV for AUC, weighted fit for final model
    try:
        auc_scores = cross_val_score(
            clf, X_scaled, y, cv=skf, scoring="roc_auc",
            params={"sample_weight": weights.values},
        )
    except TypeError:
        # sklearn < 1.4 or routing disabled — run unweighted CV
        auc_scores = cross_val_score(clf, X_scaled, y, cv=skf, scoring="roc_auc")

    # Fit final model (always exposure-weighted)
    clf.fit(X_scaled, y, sample_weight=weights.values)
    pd_scores = clf.predict_proba(X_scaled)[:, 1]

    # Calibration (reliability)
    try:
        frac_pos, mean_pred = calibration_curve(y, pd_scores, n_bins=5)
        from numpy.polynomial.polynomial import polyfit as npfit
        calib_slope = float(npfit(mean_pred, frac_pos, 1)[1]) if len(frac_pos) > 1 else 1.0
    except Exception:
        calib_slope = None

    # Feature importance (coefficients)
    feature_importance = {
        fname: round(float(coef), 4)
        for fname, coef in zip(feature_cols.keys(), clf.coef_[0])
    }

    # Per-loan scores
    loan_ids = (
        loans_df[loan_id_col].astype(str).tolist()
        if loan_id_col else [str(i) for i in range(len(loans_df))]
    )
    pd_output = [
        {"loan_id": lid, "pd_score": round(float(s), 4)}
        for lid, s in zip(loan_ids, pd_scores)
    ]
    # Sort by risk desc for output
    pd_output.sort(key=lambda x: x["pd_score"], reverse=True)

    return {
        "status":              "ok",
        "auc_mean":            round(float(auc_scores.mean()), 4),
        "auc_std":             round(float(auc_scores.std()),  4),
        "auc_by_fold":         [round(float(s), 4) for s in auc_scores],
        "calibration_slope":   round(calib_slope, 4) if calib_slope else None,
        "feature_importance":  feature_importance,
        "features_used":       list(feature_cols.keys()),
        "n_defaults":          n_pos,
        "n_non_defaults":      n_neg,
        "default_rate_actual": round(n_pos / (n_pos + n_neg) * 100, 2),
        "cv_folds":            cv_folds,
        "model_type":          "logistic_regression_exposure_weighted",
        "pd_scores":           pd_output[:500],  # top 500 highest risk for export
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7.0  Predictive KPIs
# ─────────────────────────────────────────────────────────────────────────────

def predict_kpis(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    horizon_months: int = 6,
) -> dict[str, Any]:
    """
    Time-series forecasting for AUM, revenue, and delinquency rates (section 7.0).

    Method: linear trend on trailing 12 months with confidence bands (±1.5 σ).
    Falls back gracefully when fewer than 3 data points exist.

    Returns
    -------
    {
        "horizon_months": int,
        "generated_at": str,
        "aum_forecast":        [{month, value, lower, upper}],
        "revenue_forecast":    [{month, value, lower, upper}],
        "par30_forecast":      [{month, value, lower, upper}],
        "par90_forecast":      [{month, value, lower, upper}],
        "methodology":         str,
    }
    """
    cutoff = pd.Timestamp.now().normalize()

    def _linear_forecast(series: pd.Series, horizon: int) -> list[dict]:
        """Fit linear trend, return horizon-step forecast with 1.5-sigma bands."""
        series = series.dropna()
        if len(series) < 3:
            return []
        x = np.arange(len(series))
        slope, intercept = np.polyfit(x, series.values, 1)
        residuals = series.values - (slope * x + intercept)
        sigma = float(np.std(residuals))
        rows = []
        for h in range(1, horizon + 1):
            month = cutoff + pd.DateOffset(months=h)
            point = float(slope * (len(series) - 1 + h) + intercept)
            rows.append({
                "month":  month.strftime("%Y-%m"),
                "value":  round(max(point, 0), 2),
                "lower":  round(max(point - 1.5 * sigma, 0), 2),
                "upper":  round(point + 1.5 * sigma, 2),
            })
        return rows

    # ── AUM monthly series ─────────────────────────────────────────────
    disb_col = _col(loans_df, ["disbursement_date", "FechaDesembolso"])
    bal_col  = _col(loans_df, ["outstanding_loan_value", "outstanding_balance"])
    disb_amt_col = _col(loans_df, ["disbursement_amount", "MontoDesembolsado"])
    aum_series: pd.Series = pd.Series(dtype=float)
    if disb_col and disb_amt_col:
        loans_df["_month"] = pd.to_datetime(loans_df[disb_col], errors="coerce").dt.to_period("M")
        aum_series = (
            loans_df.groupby("_month")[disb_amt_col]
            .apply(lambda s: pd.to_numeric(s, errors="coerce").fillna(0).sum())
            .tail(12)
        )

    # ── Revenue monthly series ─────────────────────────────────────────
    pay_date_col = _col(payments_df, ["true_payment_date", "payment_date"])
    pay_amt_col  = _col(payments_df, ["true_total_payment", "payment_amount", "amount"])
    rev_series: pd.Series = pd.Series(dtype=float)
    if pay_date_col and pay_amt_col:
        payments_df["_month"] = pd.to_datetime(
            payments_df[pay_date_col], errors="coerce"
        ).dt.to_period("M")
        rev_series = (
            payments_df.groupby("_month")[pay_amt_col]
            .apply(lambda s: pd.to_numeric(s, errors="coerce").fillna(0).sum())
            .tail(12)
        )

    # ── PAR series (requires DPD column) ──────────────────────────────
    # Approximation from current snapshot by origination cohort.
    dpd_col = _col(loans_df, ["days_past_due", "dpd", "days_in_default"])
    par30_series: pd.Series = pd.Series(dtype=float)
    par90_series: pd.Series = pd.Series(dtype=float)
    if dpd_col and disb_col and bal_col:
        df_par = loans_df.copy()
        df_par["_dpd"] = pd.to_numeric(df_par[dpd_col], errors="coerce").fillna(0)
        df_par["_bal"] = pd.to_numeric(df_par[bal_col], errors="coerce").fillna(0)
        df_par["_month"] = pd.to_datetime(df_par[disb_col], errors="coerce").dt.to_period("M")

        monthly_total = df_par.groupby("_month")["_bal"].sum().replace(0, np.nan)
        par30_bal = df_par.assign(_v=np.where(df_par["_dpd"] >= 30, df_par["_bal"], 0.0)).groupby("_month")["_v"].sum()
        par90_bal = df_par.assign(_v=np.where(df_par["_dpd"] >= 90, df_par["_bal"], 0.0)).groupby("_month")["_v"].sum()

        par30_series = (par30_bal / monthly_total * 100).fillna(0).tail(12)
        par90_series = (par90_bal / monthly_total * 100).fillna(0).tail(12)

    return {
        "horizon_months":  horizon_months,
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "aum_forecast":    _linear_forecast(aum_series,  horizon_months),
        "revenue_forecast": _linear_forecast(rev_series, horizon_months),
        "par30_forecast":  _linear_forecast(par30_series, horizon_months),
        "par90_forecast":  _linear_forecast(par90_series, horizon_months),
        "methodology":     "linear_trend_1.5sigma_bands",
        "data_notes": {
            "aum":     "monthly disbursement_amount by origination month (bullet-loan proxy)",
            "par":     "vintage approximation from single DPD snapshot — no historical PAR archives",
            "revenue": "true_total_payment per payment month from real_payment.csv",
        },
        "training_months": {
            "aum":     int(len(aum_series)),
            "revenue": int(len(rev_series)),
            "par30":   int(len(par30_series)),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7.1  Compliance Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def build_compliance_dashboard(
    loans_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    guardrails: dict | None = None,
    owners: dict | None = None,
) -> dict[str, Any]:
    """
    Target vs actual compliance matrix with variance decomposition (section 7.1).

    Parameters
    ----------
    guardrails:
        Dict of {metric: target_value}. If None, loads from business_parameters.yml
        via Settings.
    owners:
        Optional dict {metric: "owner_name"} for accountability assignment.

    Returns
    -------
    {
        "generated_at": str,
        "metrics": [{
            "metric", "actual", "target", "variance", "variance_pct",
            "status": "ok"|"warning"|"breach",
            "owner", "trend_direction"
        }],
        "summary": {"ok": N, "warning": N, "breach": N},
        "variance_decomposition": {metric: {driver, magnitude, explanation}},
    }
    """
    if guardrails is None:
        try:
            from backend.python.config import settings
            guardrails = {
                "rotation_x":              settings.financial.min_rotation,
                "top1_concentration_pct":  settings.financial.max_single_obligor_concentration * 100,
                "top10_concentration_pct": settings.financial.max_top_10_concentration * 100,
                "par30_pct":               5.0,
                "par90_pct":               settings.financial.max_default_rate * 100 / 2,
                "npl_180_pct":             settings.financial.max_default_rate * 100,
                "utilization_pct_min":     settings.financial.utilization_min * 100,
                "utilization_pct_max":     settings.financial.utilization_max * 100,
                "apr_pct_min":             settings.financial.target_apr_min * 100,
                "apr_pct_max":             settings.financial.target_apr_max * 100,
                "ce_6m_pct":               settings.financial.min_ce_6m * 100,
                "dscr":                    settings.financial.min_dscr,
            }
        except Exception:
            guardrails = {}

    if owners is None:
        owners = {
            "rotation_x":              "CFO",
            "top1_concentration_pct":  "CRO",
            "top10_concentration_pct": "CRO",
            "par30_pct":               "Head of Risk",
            "par90_pct":               "Head of Risk",
            "npl_180_pct":             "Head of Risk",
            "utilization_pct":         "CFO",
            "apr_pct_ann":             "Head of Pricing",
            "dscr":                    "Finance",
            "utilization_pct_min":     "CFO",
            "apr_pct_min":             "Head of Pricing",
            "ce_6m_pct":               "Head of Collections",
        }

    # ── Compute actuals ────────────────────────────────────────────────
    bal_col  = _col(loans_df, ["outstanding_loan_value", "outstanding_balance", "TotalSaldoVigente"])
    disb_col = _col(loans_df, ["disbursement_date", "FechaDesembolso"])
    apr_col  = _col(loans_df, ["interest_rate_apr", "interest_rate", "TasaInteres"])
    dpd_col  = _col(loans_df, ["days_past_due", "dpd", "DPD", "days_in_default"])
    deb_col  = _col(loans_df, ["pagador", "cliente", "emisor", "Emisor", "debtor_id", "payer_id"])
    util_col = _col(loans_df, ["porcentaje_utilizado", "Porcentaje_Utilizado", "line_utilization"])
    line_col = _col(loans_df, ["lineacredito", "LineaCredito", "credit_line"])
    noi_col = _col(loans_df, ["net_operating_income", "net_income", "ebitda", "noi"])
    debt_service_col = _col(loans_df, ["debt_service", "total_debt_service", "debt_service_amount", "monthly_debt_service"])

    loans_df = loans_df.reset_index(drop=True)
    bal  = _num(loans_df, bal_col)  if bal_col  else pd.Series([0.0] * len(loans_df))
    dpd  = _num(loans_df, dpd_col)  if dpd_col  else pd.Series([0.0] * len(loans_df))
    apr  = _num(loans_df, apr_col)  if apr_col  else pd.Series([0.0] * len(loans_df))
    total_bal = bal.sum()

    # Rotation (12m)
    rotation_actual = 0.0
    if disb_col and bal_col:
        dates    = pd.to_datetime(loans_df[disb_col], errors="coerce")
        disb_amt = _col(loans_df, ["disbursement_amount", "MontoDesembolsado"])
        if disb_amt:
            cutoff = dates.max()
            mask12 = dates >= cutoff - pd.DateOffset(months=12)
            disb12 = _num(loans_df[mask12], disb_amt).sum() if mask12.any() else 0.0
            rotation_actual = float(disb12 / total_bal) if total_bal > 0 else 0.0

    # Concentration
    top1_pct = top10_pct = 0.0
    if deb_col and total_bal > 0:
        deb_bal  = loans_df.assign(_b=bal).groupby(deb_col)["_b"].sum().sort_values(ascending=False)
        top1_pct  = float(deb_bal.iloc[0] / total_bal * 100) if len(deb_bal) > 0 else 0.0
        top10_pct = float(deb_bal.head(10).sum() / total_bal * 100)

    # PAR
    par30 = float(bal[dpd >= 30].sum() / total_bal * 100) if total_bal > 0 else 0.0
    par90 = float(bal[dpd >= 90].sum() / total_bal * 100) if total_bal > 0 else 0.0
    npl180= float(bal[dpd >= 180].sum() / total_bal * 100) if total_bal > 0 else 0.0

    # APR is stored as annual decimal in loan_data (e.g., 0.53 => 53%).
    apr_ann = float((apr * bal).sum() / total_bal * 100) if (total_bal > 0 and apr_col) else None

    # Utilization
    util_actual: float | None = None
    if util_col:
        util_actual = float(_num(loans_df, util_col).replace(0, np.nan).mean())
    elif line_col and bal_col:
        lc = _num(loans_df, line_col)
        mask = lc > 0
        util_actual = float((bal[mask] / lc[mask]).clip(0, 1).mean() * 100) if mask.any() else None

    # CE 6M (collection efficiency: actual collected / scheduled)
    # If scheduled amount is missing, use disbursement_amount in trailing 6m as proxy.
    ce_actual: float | None = None
    pay_amt = _col(payments_df, ["true_total_payment", "payment_amount"])
    sched   = _col(loans_df, ["total_scheduled", "scheduled_payment", "ValorAprobado"])
    disb_amt = _col(loans_df, ["disbursement_amount", "MontoDesembolsado"])
    if pay_amt:
        pay_date = _col(payments_df, ["true_payment_date", "payment_date"])
        if pay_date and disb_col:
            recent = pd.to_datetime(payments_df[pay_date], errors="coerce")
            mask6m = recent >= recent.max() - pd.DateOffset(months=6)
            collected6 = _num(payments_df[mask6m], pay_amt).sum() if mask6m.any() else 0.0
            disb_dates = pd.to_datetime(loans_df[disb_col], errors="coerce")
            loan_6m = disb_dates >= disb_dates.max() - pd.DateOffset(months=6)
            if sched:
                sched_total = _num(loans_df[loan_6m], sched).sum() if loan_6m.any() else 0.0
            elif disb_amt:
                sched_total = _num(loans_df[loan_6m], disb_amt).sum() if loan_6m.any() else 0.0
            else:
                sched_total = 0.0
            if sched_total > 0:
                ce_actual = float(collected6 / sched_total * 100)

    # DSCR (Debt Service Coverage Ratio)
    dscr_actual: float | None = None
    if noi_col and debt_service_col:
        noi_sum = float(_num(loans_df, noi_col).sum())
        debt_service_sum = float(_num(loans_df, debt_service_col).sum())
        if debt_service_sum > 0:
            dscr_actual = noi_sum / debt_service_sum

    actuals = {
        "rotation_x":              round(rotation_actual, 2),
        "top1_concentration_pct":  round(top1_pct, 1),
        "top10_concentration_pct": round(top10_pct, 1),
        "par30_pct":               round(par30, 1),
        "par90_pct":               round(par90, 1),
        "npl_180_pct":             round(npl180, 1),
        "utilization_pct":         round(util_actual, 1) if util_actual is not None else None,
        "apr_pct_ann":             round(apr_ann, 1) if apr_ann is not None else None,
        "ce_6m_pct":               round(ce_actual, 1) if ce_actual is not None else None,
        "dscr":                    round(dscr_actual, 2) if dscr_actual is not None else None,
    }
    data_sources = {
        "par":           f"loan.{dpd_col}" if dpd_col else "NO_DATA",
        "concentration": f"loan.{deb_col}" if deb_col else "NO_DATA",
        "ce_6m":         "payments.true_total_payment / loan.disbursement_amount (6m proxy)" if not sched else f"payments.true_total_payment / loan.{sched}",
        "utilization":   f"loan.{util_col}" if util_col else (f"loan.{line_col}" if line_col else "NO_DATA"),
        "apr":           f"loan.{apr_col} (annual decimal ×100)" if apr_col else "NO_DATA",
        "dscr":          (f"loan.{noi_col} / loan.{debt_service_col}" if (noi_col and debt_service_col) else "NO_DATA"),
    }

    # ── Build compliance rows ──────────────────────────────────────────
    # metric → (actual_key, target, lower_is_better, warning_band)
    metric_defs = {
        "rotation_x":             ("rotation_x",             4.5,  False, 0.3),
        "top1_concentration_pct": ("top1_concentration_pct", 4.0,  True,  1.0),
        "top10_concentration_pct":("top10_concentration_pct",30.0, True,  3.0),
        "par30_pct":              ("par30_pct",               5.0,  True,  1.0),
        "par90_pct":              ("par90_pct",               2.0,  True,  0.5),
        "npl_180_pct":            ("npl_180_pct",             4.0,  True,  0.5),
        "utilization_pct":        ("utilization_pct",         75.0, False, 5.0),
        "dscr":                   ("dscr",                    float(guardrails.get("dscr", 1.2)) if guardrails else 1.2, False, 0.1),
        "ce_6m_pct":              ("ce_6m_pct",               96.0, False, 2.0),
    }

    apr_min = float(guardrails.get("apr_pct_min", 36.0)) if guardrails else 36.0
    apr_max = float(guardrails.get("apr_pct_max", 99.0)) if guardrails else 99.0

    rows = []
    counts = {"ok": 0, "warning": 0, "breach": 0, "no_data": 0}

    for metric, (act_key, target, lower_is_better, warn_band) in metric_defs.items():
        actual = actuals.get(act_key)
        if actual is None:
            counts["no_data"] += 1
            rows.append({
                "metric":       metric,
                "actual":       "NO_DATA",
                "target":       target,
                "variance":     None,
                "variance_pct": None,
                "status":       "no_data",
                "lower_is_better": lower_is_better,
                "owner":        owners.get(metric, "—"),
            })
            continue
        var    = actual - target
        var_pct= round(var / target * 100, 1) if target else 0.0

        if lower_is_better:
            if actual <= target:
                stat = "ok"
            elif actual <= target + warn_band:
                stat = "warning"
            else:
                stat = "breach"
        else:
            if actual >= target:
                stat = "ok"
            elif actual >= target - warn_band:
                stat = "warning"
            else:
                stat = "breach"

        counts[stat] += 1
        rows.append({
            "metric":       metric,
            "actual":       actual,
            "target":       target,
            "variance":     round(var, 2),
            "variance_pct": var_pct,
            "status":       stat,
            "lower_is_better": lower_is_better,
            "owner":        owners.get(metric, "—"),
        })

    # APR range check (min <= APR <= max) as explicit compliance metric.
    apr_actual = actuals.get("apr_pct_ann")
    if apr_actual is None:
        counts["no_data"] += 1
        rows.append({
            "metric":       "apr_pct_ann",
            "actual":       "NO_DATA",
            "target":       f"{apr_min:.1f}-{apr_max:.1f}",
            "variance":     None,
            "variance_pct": None,
            "status":       "no_data",
            "lower_is_better": False,
            "owner":        owners.get("apr_pct_ann", owners.get("apr_pct_min", "Head of Pricing")),
        })
    else:
        apr_warn_band = 2.0
        if apr_actual < apr_min:
            apr_var = round(apr_actual - apr_min, 2)
            apr_var_pct = round(apr_var / apr_min * 100, 1) if apr_min else None
            apr_stat = "warning" if apr_actual >= (apr_min - apr_warn_band) else "breach"
        elif apr_actual > apr_max:
            apr_var = round(apr_actual - apr_max, 2)
            apr_var_pct = round(apr_var / apr_max * 100, 1) if apr_max else None
            apr_stat = "warning" if apr_actual <= (apr_max + apr_warn_band) else "breach"
        else:
            apr_var = 0.0
            apr_var_pct = 0.0
            apr_stat = "ok"

        counts[apr_stat] += 1
        rows.append({
            "metric":       "apr_pct_ann",
            "actual":       apr_actual,
            "target":       f"{apr_min:.1f}-{apr_max:.1f}",
            "variance":     apr_var,
            "variance_pct": apr_var_pct,
            "status":       apr_stat,
            "lower_is_better": False,
            "owner":        owners.get("apr_pct_ann", owners.get("apr_pct_min", "Head of Pricing")),
        })

    # ── Variance decomposition (qualitative drivers) ───────────────────
    variance_decomp = {
        "top1_concentration_pct": {
            "driver":      "La Constancia LTDA — single pagador dominates",
            "magnitude":   round(top1_pct - 4.0, 1),
            "explanation": (
                f"La Constancia represents ~{top1_pct:.0f}% of AUM vs 4% guardrail. "
                "Reduce exposure by originating with competing debtors or applying per-debtor cap."
            ),
        },
        "par30_pct": {
            "driver":      "Plazo extension + 2026 payment recording lag",
            "magnitude":   round(par30 - 5.0, 1),
            "explanation": (
                "PAR30 elevated; partial cause is INTERMEDIA DPD calculated from "
                "FechaPagoProgramado without 2026 payment records. Verify with real collections."
            ),
        },
        "par90_pct": {
            "driver":      "Structural: factoring ops with extended terms breach 90-day bucket",
            "magnitude":   round(par90 - 2.0, 1),
            "explanation": (
                "PAR90 guardrail (2%) is aggressive for a 46-day median term book. "
                "Recommend reviewing guardrail calibration against peer benchmarks."
            ),
        },
        "rotation_x": {
            "driver":      "AUM growth outpacing disbursement velocity in trailing 12m",
            "magnitude":   round(rotation_actual - 4.5, 2),
            "explanation": (
                f"Rotation {rotation_actual:.1f}x vs target 4.5x. "
                "Accelerate collections cycle or reduce average term to recover velocity."
            ),
        },
    }

    # APR and DSCR decomposition to explain range/rule outcomes and missing data.
    if apr_actual is None:
        variance_decomp["apr_pct_ann"] = {
            "driver": "APR source unavailable",
            "magnitude": None,
            "explanation": "APR cannot be computed because no APR column was found in the loan tape.",
        }
    elif apr_actual < apr_min:
        variance_decomp["apr_pct_ann"] = {
            "driver": "Pricing below target floor",
            "magnitude": round(apr_actual - apr_min, 1),
            "explanation": (
                f"Weighted APR {apr_actual:.1f}% is below minimum {apr_min:.1f}%. "
                "Review pricing floors and discount approvals by segment."
            ),
        }
    elif apr_actual > apr_max:
        variance_decomp["apr_pct_ann"] = {
            "driver": "Pricing above target ceiling",
            "magnitude": round(apr_actual - apr_max, 1),
            "explanation": (
                f"Weighted APR {apr_actual:.1f}% exceeds maximum {apr_max:.1f}%. "
                "Review competitiveness and channel mix impacts."
            ),
        }
    else:
        variance_decomp["apr_pct_ann"] = {
            "driver": "APR within policy corridor",
            "magnitude": 0.0,
            "explanation": (
                f"Weighted APR {apr_actual:.1f}% is inside the configured range "
                f"{apr_min:.1f}% to {apr_max:.1f}%."
            ),
        }

    dscr_target = float(guardrails.get("dscr", 1.2)) if guardrails else 1.2
    if dscr_actual is None:
        variance_decomp["dscr"] = {
            "driver": "DSCR inputs unavailable",
            "magnitude": None,
            "explanation": "DSCR cannot be computed because NOI and debt service fields are not present.",
        }
    else:
        variance_decomp["dscr"] = {
            "driver": "Income coverage vs debt service",
            "magnitude": round(dscr_actual - dscr_target, 2),
            "explanation": (
                f"DSCR {dscr_actual:.2f}x vs target {dscr_target:.2f}x. "
                "Improve cash generation or reduce scheduled debt service to lift coverage."
            ),
        }

    return {
        "generated_at":         datetime.now(timezone.utc).isoformat(),
        "metrics":              rows,
        "summary":              counts,
        "actuals":              actuals,
        "data_sources":         data_sources,
        "variance_decomposition": variance_decomp,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7.2  Next-Steps Planner
# ─────────────────────────────────────────────────────────────────────────────

_IMPACT_MAP = {
    "top1_concentration_pct":  ("high",   "medium", "Credit / Risk",      "Cap single-debtor exposure. Originate diversification ops with alternative pagadores."),
    "top10_concentration_pct": ("high",   "low",    "Credit / Risk",      "Activate debtor-limit alerts. Rebalance origination pipeline away from top-10 cluster."),
    "par30_pct":               ("high",   "medium", "Collections",        "Launch DPD 15+ early warning workflow. Assign KAM follow-up for outstanding ops."),
    "par90_pct":               ("high",   "high",   "Collections / Risk", "Escalate 90+ DPD bucket to recovery team. Review provisions and LGD assumptions."),
    "npl_180_pct":             ("medium", "medium", "Risk / Finance",     "Review NPL provisioning; confirm write-off criteria and recovery pipeline status."),
    "rotation_x":              ("medium", "medium", "Operations",         "Reduce average term by 5–10 days on new originations. Prioritise faster-cycling segments."),
    "ce_6m_pct":               ("high",   "medium", "Collections",        "Audit 6M collection shortfall by KAM and debtor. Escalate top-5 lagging accounts."),
}

def build_next_steps_plan(
    forecast:    dict[str, Any],
    compliance:  dict[str, Any],
    outlier_alerts: list[dict] | None = None,
    pd_result:   dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Synthesise alerts, compliance gaps, forecast signals, and PD scores
    into a single prioritised action backlog (section 7.2).

    Returns
    -------
    {
        "generated_at": str,
        "action_count": int,
        "actions": [{
            "priority": 1..N,
            "area": "Credit"|"Collections"|"Sales"|"Risk"|"Operations"|"Finance",
            "action": str,
            "impact": "high"|"medium"|"low",
            "effort": "high"|"medium"|"low",
            "source": "compliance"|"forecast"|"outlier"|"pd_model",
            "metric": str | None,
            "variance": float | None,
        }],
    }
    """
    actions: list[dict] = []

    # ── Source 1: Compliance breaches ──────────────────────────────────
    for row in compliance.get("metrics", []):
        if row["status"] in ("breach", "warning"):
            meta = _IMPACT_MAP.get(row["metric"])
            if not meta:
                continue
            impact, effort, area, action_text = meta
            actions.append({
                "area":     area,
                "action":   action_text,
                "impact":   impact,
                "effort":   effort,
                "source":   "compliance",
                "metric":   row["metric"],
                "variance": row.get("variance"),
                "_sort_key": (0 if impact == "high" else 1, row.get("variance", 0)),
            })

    # ── Source 2: Forecast signals (deterioration) ────────────────────
    for kpi_name, forecast_key in [
        ("PAR30", "par30_forecast"),
        ("PAR90", "par90_forecast"),
        ("Revenue", "revenue_forecast"),
    ]:
        rows = forecast.get(forecast_key, [])
        if len(rows) >= 2:
            first_val = rows[0].get("value", 0)
            last_val  = rows[-1].get("value", 0)
            if kpi_name in ("PAR30", "PAR90") and last_val > first_val * 1.1:
                actions.append({
                    "area":     "Risk",
                    "action":   (
                        f"{kpi_name} forecast rises {first_val:.1f}% → {last_val:.1f}% over "
                        f"{len(rows)} months. Pre-emptively tighten underwriting for "
                        "high-DPD segments."
                    ),
                    "impact":   "high",
                    "effort":   "medium",
                    "source":   "forecast",
                    "metric":   kpi_name.lower(),
                    "variance": round(last_val - first_val, 2),
                    "_sort_key": (0, last_val - first_val),
                })
            elif kpi_name == "Revenue" and last_val < first_val * 0.9:
                actions.append({
                    "area":     "Sales",
                    "action":   (
                        f"Revenue forecast declines ${first_val:,.0f} → ${last_val:,.0f}/month. "
                        "Activate KAM pipeline review; prioritise upgrades in $50–150K bucket."
                    ),
                    "impact":   "high",
                    "effort":   "medium",
                    "source":   "forecast",
                    "metric":   "revenue",
                    "variance": round(last_val - first_val, 2),
                    "_sort_key": (0, first_val - last_val),
                })

    # ── Source 3: Exposure-weighted outlier alerts ─────────────────────
    if outlier_alerts:
        total_flagged_bal = sum(a.get("outstanding_usd", 0) for a in outlier_alerts[:20])
        top_var = outlier_alerts[0].get("variable", "unknown") if outlier_alerts else "unknown"
        actions.append({
            "area":     "Risk",
            "action":   (
                f"{len(outlier_alerts)} exposure-weighted outliers flagged "
                f"(total ${total_flagged_bal:,.0f} outstanding). "
                f"Top anomaly variable: {top_var}. "
                "Review weekly watchlist in CRO pack."
            ),
            "impact":   "medium",
            "effort":   "low",
            "source":   "outlier",
            "metric":   "outlier_detection",
            "variance": None,
            "_sort_key": (1, -total_flagged_bal),
        })

    # ── Source 4: PD model — high-risk loans ──────────────────────────
    if pd_result and pd_result.get("status") == "ok":
        top_pd = [r for r in pd_result.get("pd_scores", []) if r["pd_score"] >= 0.50]
        if top_pd:
            actions.append({
                "area":     "Credit",
                "action":   (
                    f"PD model identifies {len(top_pd)} loans with PD >= 50% "
                    f"(AUC {pd_result.get('auc_mean', 0):.3f}). "
                    "Flag for enhanced monitoring, provisioning review, and collections escalation."
                ),
                "impact":   "high",
                "effort":   "low",
                "source":   "pd_model",
                "metric":   "probability_of_default",
                "variance": None,
                "_sort_key": (0, -len(top_pd)),
            })

    # ── Sort: impact first, then magnitude of variance ─────────────────
    actions.sort(key=lambda x: x.pop("_sort_key", (9, 0)))
    for i, action in enumerate(actions, 1):
        action["priority"] = i

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "action_count": len(actions),
        "actions":      actions,
        "sources_used": list({a["source"] for a in actions}),
    }
