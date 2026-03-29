from __future__ import annotations

import logging
from typing import Any, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# DPD bucket definitions (inclusive lower, exclusive upper)
_DPD_BUCKET_LABELS: List[tuple] = [
    ("current", 0, 1),
    ("1_30", 1, 31),
    ("31_60", 31, 61),
    ("61_90", 61, 91),
    ("90_plus", 91, None),
]


def compute_par30(portfolio_mart: pd.DataFrame) -> float:
    if portfolio_mart.empty:
        return 0.0
    total = portfolio_mart["outstanding_principal"].fillna(0).sum()
    if total == 0:
        return 0.0
    overdue = portfolio_mart.loc[
        portfolio_mart["days_past_due"].fillna(0) >= 30,
        "outstanding_principal",
    ].sum()
    return float(overdue / total)


def compute_par60(portfolio_mart: pd.DataFrame) -> float:
    if portfolio_mart.empty:
        return 0.0
    total = portfolio_mart["outstanding_principal"].fillna(0).sum()
    if total == 0:
        return 0.0
    overdue = portfolio_mart.loc[
        portfolio_mart["days_past_due"].fillna(0) >= 60,
        "outstanding_principal",
    ].sum()
    return float(overdue / total)


def compute_par90(portfolio_mart: pd.DataFrame) -> float:
    if portfolio_mart.empty:
        return 0.0
    total = portfolio_mart["outstanding_principal"].fillna(0).sum()
    if total == 0:
        return 0.0
    overdue = portfolio_mart.loc[
        portfolio_mart["days_past_due"].fillna(0) >= 90,
        "outstanding_principal",
    ].sum()
    return float(overdue / total)


def compute_expected_loss(
    portfolio_mart: pd.DataFrame,
    scorecard_df: pd.DataFrame | None = None,
) -> float:
    df = portfolio_mart.copy()
    if scorecard_df is not None and "loan_id" in scorecard_df.columns and "loan_id" in df.columns:
        sc_cols = ["loan_id"]
        if "pd" in scorecard_df.columns:
            sc_cols.append("pd")
        if "lgd" in scorecard_df.columns:
            sc_cols.append("lgd")
        df = df.merge(scorecard_df[sc_cols], on="loan_id", how="left", suffixes=("", "_sc"))
        for col in ("pd", "lgd"):
            sc_col = f"{col}_sc"
            if sc_col in df.columns:
                df[col] = df[sc_col].fillna(df.get(col, pd.Series(dtype=float)))
                df.drop(columns=[sc_col], inplace=True)
    if "pd" not in df.columns:
        df["pd"] = 0.03
    else:
        df["pd"] = df["pd"].fillna(0.03)
    if "lgd" not in df.columns:
        df["lgd"] = 0.45
    else:
        df["lgd"] = df["lgd"].fillna(0.45)
    if "ead" not in df.columns:
        df["ead"] = df["outstanding_principal"].fillna(0)
    return float((df["pd"] * df["lgd"] * df["ead"]).sum())


def classify_dpd_buckets(
    df: pd.DataFrame,
    dpd_col: str = "days_past_due",
    output_col: str = "dpd_bucket",
) -> pd.DataFrame:
    """Classify loans into DPD buckets (current, 1_30, 31_60, 61_90, 90_plus).

    Args:
        df: DataFrame with loan data.
        dpd_col: Name of DPD column.
        output_col: Name of output bucket column.

    Returns:
        DataFrame with dpd_bucket column added.
    """
    result = df.copy()

    if dpd_col not in result.columns:
        result[output_col] = "current"
        return result

    dpd = pd.to_numeric(result[dpd_col], errors="coerce")
    bucket = pd.Series("unknown", index=dpd.index, dtype=str)
    valid_dpd = dpd.dropna().clip(lower=0)

    for label, lo, hi in _DPD_BUCKET_LABELS:
        if hi is None:
            mask = valid_dpd >= lo
        else:
            mask = (valid_dpd >= lo) & (valid_dpd < hi)
        bucket.loc[mask.index[mask]] = label

    result[output_col] = bucket
    return result


def segment_clients_by_exposure(
    df: pd.DataFrame,
    balance_col: str = "outstanding_balance",
    output_col: str = "exposure_segment",
) -> pd.DataFrame:
    """Segment clients into exposure tiers based on outstanding balance.

    Tiers:
        Inactive  — balance = 0
        Micro     — < $10K
        Small     — $10K – $50K
        Medium    — $50K – $100K
        Large     — $100K – $500K
        Major     — $500K+

    Args:
        df: DataFrame with loan/client data.
        balance_col: Name of outstanding balance column.
        output_col: Name of output segment column.

    Returns:
        DataFrame with exposure_segment column added.
    """
    result = df.copy()

    if balance_col not in result.columns:
        result[output_col] = "Unknown"
        return result

    balance = pd.to_numeric(result[balance_col], errors="coerce").fillna(0)

    def _tier(val: float) -> str:
        if val <= 0:
            return "Inactive"
        if val < 10_000:
            return "Micro"
        if val < 50_000:
            return "Small"
        if val < 100_000:
            return "Medium"
        if val < 500_000:
            return "Large"
        return "Major"

    result[output_col] = balance.apply(_tier)
    return result


def compute_customer_dpd_stats(
    merged_df: pd.DataFrame,
    customer_id_field: str = "customer_id",
    dpd_col: str = "days_past_due",
) -> pd.DataFrame:
    """Group by customer and calculate DPD statistics.

    Args:
        merged_df: DataFrame with loan and customer data (pre-merged).
        customer_id_field: Name of customer ID column.
        dpd_col: Name of days-past-due column.

    Returns:
        DataFrame with dpd_mean, dpd_median, dpd_max, dpd_min, dpd_count per customer.
    """
    _EMPTY_COLS = [customer_id_field, "dpd_mean", "dpd_median", "dpd_max", "dpd_min", "dpd_count"]

    if merged_df.empty or customer_id_field not in merged_df.columns:
        return pd.DataFrame(columns=_EMPTY_COLS)

    df = merged_df[[customer_id_field, dpd_col]].copy() if dpd_col in merged_df.columns else merged_df[[customer_id_field]].copy()

    if dpd_col not in df.columns:
        df[dpd_col] = 0

    df[dpd_col] = pd.to_numeric(df[dpd_col], errors="coerce").fillna(0)

    # Group by customer and calculate statistics
    customer_dpd_stats = (
        df.groupby(customer_id_field)
        .agg(
            dpd_mean=(dpd_col, "mean"),
            dpd_median=(dpd_col, "median"),
            dpd_max=(dpd_col, "max"),
            dpd_min=(dpd_col, "min"),
            dpd_count=(dpd_col, "count"),
        )
        .reset_index()
    )

    customer_dpd_stats["dpd_mean"] = customer_dpd_stats["dpd_mean"].round(2)
    customer_dpd_stats["dpd_median"] = customer_dpd_stats["dpd_median"].round(1)

    return customer_dpd_stats


def build_feature_engineering_pipeline(
    result: pd.DataFrame,
    classify_client_type_fn: Optional[Any] = None,
) -> pd.DataFrame:
    """Run the full feature engineering pipeline on a loan DataFrame.

    Executes in order:
        1. Validate required columns (loan_id, customer_id, outstanding_balance).
        2. DPD bucket classification.
        3. Client segmentation by exposure.
        4. Client type classification (Nuevo/Recurrente/Recuperado).
        5. Line utilization.
        6. Z-scores for key metrics (apr, term, days_past_due, outstanding_balance,
           line_utilization).

    Args:
        result: Input DataFrame with loan data.
        classify_client_type_fn: Optional callable(df) -> df for client type tagging.

    Returns:
        DataFrame with all engineered features added.
    """
    # 1. Verificar si tenemos las columnas necesarias
    required_columns = ["loan_id", "customer_id", "outstanding_balance"]
    missing_columns = [col for col in required_columns if col not in result.columns]

    if missing_columns:
        logger.error(
            "Faltan columnas requeridas para la ingeniería de características: %s",
            missing_columns,
        )
        return result

    # 2. Añadir buckets DPD
    if "days_past_due" in result.columns:
        result = classify_dpd_buckets(result)
        logger.info("Agregada clasificación de buckets DPD")

    # 3. Añadir segmentos de cliente
    if "outstanding_balance" in result.columns:
        result = segment_clients_by_exposure(result)
        logger.info("Agregada segmentación de clientes por exposición")

    # 4. Añadir tipos de cliente
    if (
        classify_client_type_fn is not None
        and all(col in result.columns for col in ["customer_id", "loan_count", "last_active_date"])
    ):
        result = classify_client_type_fn(result)
        logger.info("Agregada clasificación de tipo de cliente")

    # 5. Calcular utilización de línea
    if all(col in result.columns for col in ["outstanding_balance", "line_amount"]):
        from backend.src.kpi_engine.unit_economics import calculate_line_utilization
        result = calculate_line_utilization(
            result,
            credit_line_field="line_amount",
            loan_amount_field="outstanding_balance",
        )
        logger.info("Calculada utilización de línea")

    # 6. Agregar Z-scores para variables clave
    key_metrics = ["apr", "term", "days_past_due", "outstanding_balance", "line_utilization"]
    for metric in key_metrics:
        if metric in result.columns:
            col_vals = pd.to_numeric(result[metric], errors="coerce")
            std = col_vals.std()
            if std and std > 0:
                result[f"{metric}_zscore"] = ((col_vals - col_vals.mean()) / std).round(4)
                logger.info("Calculado Z-score para %s", metric)

    return result
