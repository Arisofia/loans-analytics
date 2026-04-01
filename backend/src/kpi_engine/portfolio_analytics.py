"""Portfolio analytics — line block segmentation, rotation analysis, churn,
default by segment, max mora, pricing engine, and income/revenue calculation.

Análisis de la cartera:
- Identificar clientes con líneas < $100K con rotación ≤ 30 días
- Dividir cartera en bloques de $100K
- Tasa por montos
- Clasificación de clientes
- Churn
- Default por segmento
- Máximos de mora
- Definir pricing (con comisión mínima para montos < $10K)
- Calcular ingreso y revenue
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ── configurable thresholds ────────────────────────────────────────────────────
_SMALL_LINE_THRESHOLD_USD: float = 100_000.0
_SHORT_ROTATION_DAYS: int = 30
_SMALL_LOAN_THRESHOLD_USD: float = 10_000.0
_DEFAULT_MIN_COMMISSION_USD: float = 500.0
_LINE_BLOCK_SIZE_USD: float = 100_000.0
_CHURN_INACTIVITY_DAYS: int = 90

# Amount-based rate tiers — insumo para pricing por tramo
_RATE_TIERS: List[Dict[str, Any]] = [
    {"label": "<$10K",       "min": 0,        "max": 10_000,  "min_commission_usd": _DEFAULT_MIN_COMMISSION_USD},
    {"label": "$10K-$25K",   "min": 10_000,   "max": 25_000,  "min_commission_usd": 0.0},
    {"label": "$25K-$50K",   "min": 25_000,   "max": 50_000,  "min_commission_usd": 0.0},
    {"label": "$50K-$100K",  "min": 50_000,   "max": 100_000, "min_commission_usd": 0.0},
    {"label": "$100K-$250K", "min": 100_000,  "max": 250_000, "min_commission_usd": 0.0},
    {"label": "$250K-$500K", "min": 250_000,  "max": 500_000, "min_commission_usd": 0.0},
    {"label": "$500K+",      "min": 500_000,  "max": None,    "min_commission_usd": 0.0},
]


# ── helpers ────────────────────────────────────────────────────────────────────

def _coerce_numeric(df: pd.DataFrame, *cols: str) -> pd.DataFrame:
    """Coerce given columns to float in-place, filling NaN with 0."""
    result = df.copy()
    for col in cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0)
    return result


# ── public functions ───────────────────────────────────────────────────────────

def analyze_small_line_rotation(
    portfolio: pd.DataFrame,
    line_col: str = "line_amount",
    term_days_col: str = "term_days",
    balance_col: str = "outstanding_balance",
    customer_col: str = "customer_id",
    loan_id_col: str = "loan_id",
    line_threshold: float = _SMALL_LINE_THRESHOLD_USD,
    rotation_days: int = _SHORT_ROTATION_DAYS,
) -> Dict[str, Any]:
    """Identify clients with credit lines < $100K and rotation ≤ 30 days.

    Análisis de la cartera: identificar los clientes con líneas menores de
    $100K con una rotación igual o menor a 30 días.

    Args:
        portfolio: DataFrame with loan data.
        line_col: Credit line size column.
        term_days_col: Loan term in days column.
        balance_col: Outstanding balance column.
        customer_col: Customer ID column.
        loan_id_col: Loan ID column.
        line_threshold: Maximum credit line amount (default $100K).
        rotation_days: Maximum term/rotation in days (default 30).

    Returns:
        Dict with criteria, summary statistics, and per-customer breakdown.
    """
    criteria = {"line_lt_usd": line_threshold, "rotation_lte_days": rotation_days}

    if portfolio.empty:
        return {**criteria, "total_clients": 0, "total_loans": 0,
                "total_balance_usd": 0.0, "avg_line_usd": 0.0, "clients": []}

    df = _coerce_numeric(portfolio, line_col, balance_col)

    mask = pd.Series(True, index=df.index)
    if line_col in df.columns:
        mask &= df[line_col] < line_threshold
    if term_days_col in df.columns:
        df[term_days_col] = pd.to_numeric(df[term_days_col], errors="coerce").fillna(9999)
        mask &= df[term_days_col] <= rotation_days

    filtered = df[mask].copy()

    if filtered.empty:
        return {
            "criteria": criteria,
            "total_clients": 0,
            "total_loans": 0,
            "total_balance_usd": 0.0,
            "avg_line_usd": 0.0,
            "clients": [],
        }

    # Build per-customer aggregation
    agg_spec: Dict[str, Any] = {}
    if loan_id_col in filtered.columns:
        agg_spec["loan_count"] = pd.NamedAgg(column=loan_id_col, aggfunc="count")
    if balance_col in filtered.columns:
        agg_spec["total_balance_usd"] = pd.NamedAgg(column=balance_col, aggfunc="sum")
    if line_col in filtered.columns:
        agg_spec["avg_line_usd"] = pd.NamedAgg(column=line_col, aggfunc="mean")
    if term_days_col in filtered.columns:
        agg_spec["avg_term_days"] = pd.NamedAgg(column=term_days_col, aggfunc="mean")

    if customer_col in filtered.columns and agg_spec:
        by_customer = (
            filtered.groupby(customer_col)
            .agg(**agg_spec)
            .reset_index()
        )
        sort_col = "total_balance_usd" if "total_balance_usd" in by_customer.columns else customer_col
        by_customer = by_customer.sort_values(sort_col, ascending=False).round(2)
        clients: List[Dict[str, Any]] = by_customer.to_dict("records")
    else:
        clients = []

    return {
        "criteria": criteria,
        "total_clients": int(filtered[customer_col].nunique()) if customer_col in filtered.columns else len(filtered),
        "total_loans": int(len(filtered)),
        "total_balance_usd": round(float(filtered[balance_col].sum()), 2) if balance_col in filtered.columns else 0.0,
        "avg_line_usd": round(float(filtered[line_col].mean()), 2) if line_col in filtered.columns else 0.0,
        "clients": clients,
    }


def segment_portfolio_by_line_blocks(
    portfolio: pd.DataFrame,
    line_col: str = "line_amount",
    balance_col: str = "outstanding_balance",
    loan_id_col: str = "loan_id",
    block_size: float = _LINE_BLOCK_SIZE_USD,
) -> List[Dict[str, Any]]:
    """Divide portfolio into blocks of $100K credit lines.

    Dividir cartera en bloques de líneas de $100K para analizar la
    distribución del portafolio y las tasas cobradas en cada segmento.

    Args:
        portfolio: DataFrame with loan data.
        line_col: Credit line amount column.
        balance_col: Outstanding balance column.
        loan_id_col: Loan ID column.
        block_size: Block size in USD (default $100K).

    Returns:
        List of dicts per block: block_label, line_min_usd, line_max_usd,
        loan_count, total_balance_usd, avg_balance_usd, share_pct.
    """
    if portfolio.empty or line_col not in portfolio.columns:
        return []

    df = _coerce_numeric(portfolio, line_col, balance_col)
    df["_block_idx"] = (df[line_col] // block_size).astype(int).clip(lower=0)

    def _label(idx: int) -> str:
        lo = int(idx * block_size)
        hi = int((idx + 1) * block_size)
        if lo >= 1_000_000:
            return f"${lo // 1_000_000}M+"
        return f"${lo // 1_000}K–${hi // 1_000}K"

    count_col = loan_id_col if loan_id_col in df.columns else "_block_idx"
    agg: Dict[str, Any] = {"loan_count": pd.NamedAgg(column=count_col, aggfunc="count")}
    if balance_col in df.columns:
        agg["total_balance_usd"] = pd.NamedAgg(column=balance_col, aggfunc="sum")
        agg["avg_balance_usd"] = pd.NamedAgg(column=balance_col, aggfunc="mean")

    grp = df.groupby("_block_idx").agg(**agg).reset_index()
    total_bal = float(grp["total_balance_usd"].sum()) if "total_balance_usd" in grp.columns else 1.0

    rows = []
    for _, row in grp.iterrows():
        idx = int(row["_block_idx"])
        total_b = float(row.get("total_balance_usd", 0))
        rows.append({
            "block_label": _label(idx),
            "line_min_usd": int(idx * block_size),
            "line_max_usd": int((idx + 1) * block_size),
            "loan_count": int(row["loan_count"]),
            "total_balance_usd": round(total_b, 2),
            "avg_balance_usd": round(float(row.get("avg_balance_usd", 0)), 2),
            "share_pct": round(total_b / total_bal * 100, 2) if total_bal > 0 else 0.0,
        })

    return sorted(rows, key=lambda x: x["line_min_usd"])


def compute_rate_by_amount_tiers(
    portfolio: pd.DataFrame,
    amount_col: str = "loan_amount",
    rate_col: str = "apr",
    balance_col: str = "outstanding_balance",
    loan_id_col: str = "loan_id",
    tiers: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Weighted average rate and statistics by loan amount tiers.

    Tasa por montos — permite visualizar cómo la tasa efectiva cambia según
    el monto del préstamo, insumo directo para el pricing por tramo.

    Args:
        portfolio: DataFrame with loan data.
        amount_col: Loan amount column.
        rate_col: Interest rate / APR column (decimal, e.g. 0.24 = 24%).
        balance_col: Outstanding balance (used as weight for rate average).
        loan_id_col: Loan ID column.
        tiers: Custom tier definitions. Defaults to _RATE_TIERS.

    Returns:
        List of dicts per tier: tier, amount_min/max, loan_count,
        total_balance_usd, avg_rate_pct, weighted_avg_rate_pct, min_commission_usd.
    """
    if portfolio.empty:
        return []

    tier_defs = tiers if tiers is not None else _RATE_TIERS
    df = _coerce_numeric(portfolio, amount_col, rate_col, balance_col)

    if amount_col not in df.columns:
        return []

    rows = []
    for tier in tier_defs:
        lo = float(tier["min"])
        hi = tier.get("max")
        label = tier["label"]
        min_commission = float(tier.get("min_commission_usd", 0.0))

        mask = df[amount_col] >= lo
        if hi is not None:
            mask &= df[amount_col] < float(hi)

        grp = df[mask]
        count = len(grp)

        if count == 0:
            rows.append({
                "tier": label,
                "amount_min_usd": lo,
                "amount_max_usd": hi,
                "loan_count": 0,
                "total_balance_usd": 0.0,
                "avg_rate_pct": 0.0,
                "weighted_avg_rate_pct": 0.0,
                "min_commission_usd": min_commission,
            })
            continue

        if rate_col in grp.columns:
            avg_rate = round(float(grp[rate_col].mean()) * 100, 4)
            if balance_col in grp.columns:
                weights = grp[balance_col]
                total_w = float(weights.sum())
                w_rate = (
                    round(float((grp[rate_col] * weights).sum() / total_w) * 100, 4)
                    if total_w > 0
                    else avg_rate
                )
            else:
                w_rate = avg_rate
        else:
            avg_rate = 0.0
            w_rate = 0.0

        rows.append({
            "tier": label,
            "amount_min_usd": lo,
            "amount_max_usd": hi,
            "loan_count": count,
            "total_balance_usd": round(float(grp[balance_col].sum()), 2) if balance_col in grp.columns else 0.0,
            "avg_rate_pct": avg_rate,
            "weighted_avg_rate_pct": w_rate,
            "min_commission_usd": min_commission,
        })

    return rows


def compute_default_by_segment(
    portfolio: pd.DataFrame,
    segment_col: str = "segment",
    default_col: str = "default_flag",
    dpd_col: str = "days_past_due",
    balance_col: str = "outstanding_balance",
    loan_id_col: str = "loan_id",
    dpd_threshold: int = 90,
) -> List[Dict[str, Any]]:
    """Default rate and balance at risk grouped by customer segment.

    Default por segmento — agrupa las métricas de incumplimiento por segmento
    de cliente para priorizar colecciones y ajustar el pricing.

    Args:
        portfolio: DataFrame with loan data.
        segment_col: Segment column name (e.g. 'Nimal', 'Gob', 'OC', 'Top').
        default_col: Binary default flag (1/True = default). Falls back to
            dpd_col >= dpd_threshold if not present.
        dpd_col: Days past due column (fallback default proxy).
        balance_col: Outstanding balance column.
        loan_id_col: Loan ID column.
        dpd_threshold: DPD threshold to classify as default when default_col
            is absent (default 90).

    Returns:
        List of dicts per segment sorted by default_rate_pct descending:
        segment, total_loans, default_loans, default_rate_pct,
        total_balance_usd, balance_at_risk_usd, balance_at_risk_pct.
    """
    if portfolio.empty or segment_col not in portfolio.columns:
        return []

    df = _coerce_numeric(portfolio, balance_col)
    df[segment_col] = df[segment_col].fillna("Unassigned").astype(str)

    # Derive default flag
    if default_col in df.columns:
        df["_default"] = pd.to_numeric(df[default_col], errors="coerce").fillna(0).gt(0).astype(int)
    elif dpd_col in df.columns:
        df["_default"] = (pd.to_numeric(df[dpd_col], errors="coerce").fillna(0) >= dpd_threshold).astype(int)
    else:
        df["_default"] = 0

    rows = []
    for seg, grp in df.groupby(segment_col):
        total_loans = len(grp)
        default_loans = int(grp["_default"].sum())
        default_rate = round(default_loans / total_loans * 100, 2) if total_loans > 0 else 0.0
        total_balance = float(grp[balance_col].sum()) if balance_col in grp.columns else 0.0
        default_balance = float(grp.loc[grp["_default"] == 1, balance_col].sum()) if balance_col in grp.columns else 0.0

        rows.append({
            "segment": str(seg),
            "total_loans": total_loans,
            "default_loans": default_loans,
            "default_rate_pct": default_rate,
            "total_balance_usd": round(total_balance, 2),
            "balance_at_risk_usd": round(default_balance, 2),
            "balance_at_risk_pct": round(default_balance / total_balance * 100, 2) if total_balance > 0 else 0.0,
        })

    return sorted(rows, key=lambda x: x["default_rate_pct"], reverse=True)


def compute_max_mora_by_segment(
    portfolio: pd.DataFrame,
    segment_col: str = "segment",
    dpd_col: str = "days_past_due",
    balance_col: str = "outstanding_balance",
    loan_id_col: str = "loan_id",
    customer_col: str = "customer_id",
) -> List[Dict[str, Any]]:
    """Maximum delinquency (mora) metrics grouped by segment.

    Máximos de mora — reporta el DPD máximo, percentil 95 y promedio por
    segmento, junto con el préstamo más moroso como señal de alerta.

    Args:
        portfolio: DataFrame with loan data.
        segment_col: Segment column name.
        dpd_col: Days past due column.
        balance_col: Outstanding balance column.
        loan_id_col: Loan ID column.
        customer_col: Customer ID column.

    Returns:
        List of dicts per segment sorted by max_dpd descending:
        segment, max_dpd, p95_dpd, avg_dpd, worst_loan_id, worst_customer,
        worst_balance_usd, dpd_buckets.
    """
    if portfolio.empty or segment_col not in portfolio.columns or dpd_col not in portfolio.columns:
        return []

    df = _coerce_numeric(portfolio, dpd_col, balance_col)
    df[segment_col] = df[segment_col].fillna("Unassigned").astype(str)

    rows = []
    for seg, grp in df.groupby(segment_col):
        dpd_vals = grp[dpd_col]
        max_dpd = int(dpd_vals.max())
        worst_idx = dpd_vals.idxmax()

        rows.append({
            "segment": str(seg),
            "max_dpd": max_dpd,
            "p95_dpd": round(float(dpd_vals.quantile(0.95)), 1),
            "avg_dpd": round(float(dpd_vals.mean()), 2),
            "worst_loan_id": str(grp.loc[worst_idx, loan_id_col]) if loan_id_col in grp.columns else None,
            "worst_customer": str(grp.loc[worst_idx, customer_col]) if customer_col in grp.columns else None,
            "worst_balance_usd": round(float(grp.loc[worst_idx, balance_col]), 2) if balance_col in grp.columns else None,
            "dpd_buckets": {
                "current":  int((dpd_vals == 0).sum()),
                "1_30":     int(((dpd_vals > 0)  & (dpd_vals <= 30)).sum()),
                "31_60":    int(((dpd_vals > 30) & (dpd_vals <= 60)).sum()),
                "61_90":    int(((dpd_vals > 60) & (dpd_vals <= 90)).sum()),
                "90_plus":  int((dpd_vals > 90).sum()),
            },
        })

    return sorted(rows, key=lambda x: x["max_dpd"], reverse=True)


def compute_churn_analysis(
    portfolio: pd.DataFrame,
    customer_col: str = "customer_id",
    date_col: str = "origination_date",
    snapshot_date: Optional[Any] = None,
    inactivity_days: int = _CHURN_INACTIVITY_DAYS,
    segment_col: Optional[str] = "segment",
) -> Dict[str, Any]:
    """Churn analysis — identify customers who stopped borrowing.

    Clasifica a los clientes como Active, AtRisk o Churned según su última
    actividad respecto al snapshot_date:
        Active   — última actividad ≤ 30 días
        AtRisk   — última actividad 31 – inactivity_days días
        Churned  — última actividad > inactivity_days días (default 90)

    Args:
        portfolio: DataFrame with loan origination data.
        customer_col: Customer ID column.
        date_col: Origination date column.
        snapshot_date: Reference date. Defaults to the latest date in the data.
        inactivity_days: Days without activity to be classified as Churned.
        segment_col: Optional segment column for breakdown.

    Returns:
        Dict with snapshot_date, total_customers, active_count, at_risk_count,
        churned_count, churn_rate_pct, and by_segment breakdown.
    """
    _empty = {
        "snapshot_date": str(snapshot_date or ""),
        "inactivity_threshold_days": inactivity_days,
        "total_customers": 0,
        "active_count": 0,
        "at_risk_count": 0,
        "churned_count": 0,
        "churn_rate_pct": 0.0,
        "by_segment": [],
    }

    if portfolio.empty or customer_col not in portfolio.columns or date_col not in portfolio.columns:
        return _empty

    seg_cols = [segment_col] if segment_col and segment_col in portfolio.columns else []
    df = portfolio[[customer_col, date_col, *seg_cols]].copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
    df = df.dropna(subset=[date_col])

    if df.empty:
        return _empty

    snap = pd.Timestamp(snapshot_date) if snapshot_date is not None else df[date_col].max()

    last_activity = df.groupby(customer_col)[date_col].max().reset_index()
    last_activity["days_since_last"] = (snap - last_activity[date_col]).dt.days.clip(lower=0)

    def _status(days: int) -> str:
        if days <= 30:
            return "Active"
        if days <= inactivity_days:
            return "AtRisk"
        return "Churned"

    last_activity["churn_status"] = last_activity["days_since_last"].apply(_status)

    total = len(last_activity)
    counts = last_activity["churn_status"].value_counts().to_dict()
    churned = int(counts.get("Churned", 0))
    at_risk = int(counts.get("AtRisk", 0))
    active = int(counts.get("Active", 0))

    # Segment breakdown
    by_segment: List[Dict[str, Any]] = []
    if seg_cols:
        last_seg = (
            df.sort_values(date_col)
            .groupby(customer_col)[segment_col]
            .last()
            .reset_index()
        )
        merged = last_activity.merge(last_seg, on=customer_col, how="left")
        merged[segment_col] = merged[segment_col].fillna("Unassigned")

        seg_pivot = (
            merged.groupby([segment_col, "churn_status"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        for _, row in seg_pivot.iterrows():
            seg_ch = int(row.get("Churned", 0))
            seg_tot = int(row.get("Active", 0)) + int(row.get("AtRisk", 0)) + seg_ch
            by_segment.append({
                "segment": str(row[segment_col]),
                "active": int(row.get("Active", 0)),
                "at_risk": int(row.get("AtRisk", 0)),
                "churned": seg_ch,
                "churn_rate_pct": round(seg_ch / seg_tot * 100, 2) if seg_tot > 0 else 0.0,
            })
        by_segment.sort(key=lambda x: x["churn_rate_pct"], reverse=True)

    return {
        "snapshot_date": snap.strftime("%Y-%m-%d"),
        "inactivity_threshold_days": inactivity_days,
        "total_customers": total,
        "active_count": active,
        "at_risk_count": at_risk,
        "churned_count": churned,
        "churn_rate_pct": round(churned / total * 100, 2) if total > 0 else 0.0,
        "by_segment": by_segment,
    }


def compute_pricing_recommendations(
    portfolio: pd.DataFrame,
    amount_col: str = "loan_amount",
    apr_col: str = "apr",
    balance_col: str = "outstanding_balance",
    dpd_col: str = "days_past_due",
    segment_col: str = "segment",
    min_commission_usd: float = _DEFAULT_MIN_COMMISSION_USD,
    small_loan_threshold: float = _SMALL_LOAN_THRESHOLD_USD,
    tiers: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Pricing recommendations by loan amount tier, including minimum commission.

    Definir pricing — para préstamos menores a $10K se establece una comisión
    mínima independientemente del porcentaje de tasa pactado, garantizando que
    el costo operativo sea cubierto.

    Fórmula comisión efectiva (ajustada al plazo):
        commission_usd = MAX(loan_amount × apr × term_months / 12, min_commission_usd)
    Si term_months no está disponible se usa apr anual directamente.

    Args:
        portfolio: DataFrame with loan data.
        amount_col: Loan amount column.
        apr_col: APR / interest rate column (decimal, e.g. 0.24 = 24%).
        balance_col: Outstanding balance (for weighting rates).
        dpd_col: DPD column (for risk-adjusted context per segment).
        segment_col: Segment column.
        min_commission_usd: Minimum commission for small loans (default $500).
        small_loan_threshold: Amount below which min commission applies ($10K).
        tiers: Custom tier definitions. Defaults to _RATE_TIERS.

    Returns:
        Dict with tier_analysis, min_commission_policy, and segment_pricing.
    """
    _empty: Dict[str, Any] = {
        "tier_analysis": [],
        "min_commission_policy": {
            "threshold_usd": small_loan_threshold,
            "min_commission_usd": min_commission_usd,
            "loans_affected": 0,
            "total_commission_uplift_usd": 0.0,
            "description": "",
        },
        "segment_pricing": [],
    }

    if portfolio.empty:
        return _empty

    term_months_col = "term_months"
    df = _coerce_numeric(portfolio, amount_col, apr_col, balance_col, dpd_col, term_months_col)

    # Tier rate analysis
    tier_analysis = compute_rate_by_amount_tiers(
        df,
        amount_col=amount_col,
        rate_col=apr_col,
        balance_col=balance_col,
        tiers=tiers,
    )

    # Min commission policy impact
    loans_affected = 0
    total_uplift = 0.0

    if amount_col in df.columns and apr_col in df.columns:
        small = df[df[amount_col] < small_loan_threshold].copy()
        if not small.empty:
            if term_months_col in small.columns:
                small["_rate_commission"] = (
                    small[amount_col] * small[apr_col] * small[term_months_col] / 12.0
                )
            else:
                small["_rate_commission"] = small[amount_col] * small[apr_col]
            small["_shortfall"] = (min_commission_usd - small["_rate_commission"]).clip(lower=0)
            total_uplift = round(float(small["_shortfall"].sum()), 2)
            loans_affected = int((small["_rate_commission"] < min_commission_usd).sum())

    min_commission_policy: Dict[str, Any] = {
        "threshold_usd": small_loan_threshold,
        "min_commission_usd": min_commission_usd,
        "loans_affected": loans_affected,
        "total_commission_uplift_usd": total_uplift,
        "description": (
            f"Para préstamos < ${small_loan_threshold:,.0f}, la comisión mínima es "
            f"${min_commission_usd:,.0f} independientemente del % de tasa. "
            f"Fórmula: comisión = MAX(monto × tasa, ${min_commission_usd:,.0f})"
        ),
    }

    # Segment-level pricing
    segment_pricing: List[Dict[str, Any]] = []
    if segment_col in df.columns and apr_col in df.columns:
        for seg, grp in df.groupby(segment_col):
            if balance_col in grp.columns:
                total_w = float(grp[balance_col].sum())
                w_rate = (
                    round(float((grp[apr_col] * grp[balance_col]).sum() / total_w) * 100, 4)
                    if total_w > 0
                    else round(float(grp[apr_col].mean()) * 100, 4)
                )
            else:
                w_rate = round(float(grp[apr_col].mean()) * 100, 4)

            segment_pricing.append({
                "segment": str(seg),
                "loan_count": len(grp),
                "weighted_avg_apr_pct": w_rate,
                "avg_dpd": round(float(grp[dpd_col].mean()), 2) if dpd_col in grp.columns else 0.0,
                "total_balance_usd": round(float(grp[balance_col].sum()), 2) if balance_col in grp.columns else 0.0,
            })

    return {
        "tier_analysis": tier_analysis,
        "min_commission_policy": min_commission_policy,
        "segment_pricing": sorted(segment_pricing, key=lambda x: x["weighted_avg_apr_pct"], reverse=True),
    }


def compute_income_and_revenue(
    portfolio: pd.DataFrame,
    amount_col: str = "loan_amount",
    balance_col: str = "outstanding_balance",
    apr_col: str = "apr",
    term_months_col: str = "term_months",
    fee_rate_col: str = "origination_fee_rate",
    segment_col: str = "segment",
) -> Dict[str, Any]:
    """Compute income and revenue components from the portfolio.

    Calcular ingreso y revenue — desglosa los componentes de ingresos:
        - Interest income   : balance × (apr / 12)  [mensual]
        - Fee income        : loan_amount × origination_fee_rate
        - Total revenue     : interest + fees
        - Net yield %       : total_revenue / total_balance

    Args:
        portfolio: DataFrame with loan data.
        amount_col: Original loan amount column.
        balance_col: Outstanding balance column.
        apr_col: Annual rate column (decimal, e.g. 0.24 for 24%).
        term_months_col: Term in months column.
        fee_rate_col: Origination fee rate column (decimal).
        segment_col: Segment column for breakdown.

    Returns:
        Dict with interest_income_usd, fee_income_usd, total_revenue_usd,
        net_yield_pct, total_portfolio_usd, revenue_by_segment.
    """
    _empty: Dict[str, Any] = {
        "interest_income_usd": 0.0,
        "fee_income_usd": 0.0,
        "total_revenue_usd": 0.0,
        "net_yield_pct": 0.0,
        "total_portfolio_usd": 0.0,
        "revenue_by_segment": [],
    }

    if portfolio.empty:
        return _empty

    df = _coerce_numeric(portfolio, amount_col, balance_col, apr_col, term_months_col, fee_rate_col)

    # Monthly interest income = balance × (apr / 12)
    if balance_col in df.columns and apr_col in df.columns:
        df["_interest"] = df[balance_col] * (df[apr_col] / 12)
    else:
        df["_interest"] = 0.0

    # Origination fee income
    if amount_col in df.columns and fee_rate_col in df.columns:
        df["_fee"] = df[amount_col] * df[fee_rate_col]
    else:
        df["_fee"] = 0.0

    total_interest = round(float(df["_interest"].sum()), 2)
    total_fees = round(float(df["_fee"].sum()), 2)
    total_revenue = round(total_interest + total_fees, 2)
    total_balance = round(float(df[balance_col].sum()), 2) if balance_col in df.columns else 0.0
    net_yield_pct = round(total_revenue / total_balance * 100, 4) if total_balance > 0 else 0.0

    # Revenue by segment
    revenue_by_segment: List[Dict[str, Any]] = []
    if segment_col in df.columns:
        for seg, grp in df.groupby(segment_col):
            seg_int = round(float(grp["_interest"].sum()), 2)
            seg_fee = round(float(grp["_fee"].sum()), 2)
            seg_total = round(seg_int + seg_fee, 2)
            seg_bal = round(float(grp[balance_col].sum()), 2) if balance_col in grp.columns else 0.0
            revenue_by_segment.append({
                "segment": str(seg),
                "interest_income_usd": seg_int,
                "fee_income_usd": seg_fee,
                "total_revenue_usd": seg_total,
                "portfolio_balance_usd": seg_bal,
                "net_yield_pct": round(seg_total / seg_bal * 100, 4) if seg_bal > 0 else 0.0,
                "revenue_share_pct": round(seg_total / total_revenue * 100, 2) if total_revenue > 0 else 0.0,
            })

    return {
        "interest_income_usd": total_interest,
        "fee_income_usd": total_fees,
        "total_revenue_usd": total_revenue,
        "net_yield_pct": net_yield_pct,
        "total_portfolio_usd": total_balance,
        "revenue_by_segment": sorted(revenue_by_segment, key=lambda x: x["total_revenue_usd"], reverse=True),
    }
