from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ComparableDecimal(Decimal):
    def __new__(cls, value: str | int | float | Decimal = "0") -> "ComparableDecimal":
        return super().__new__(cls, value)

    def __sub__(self, other: Any):
        # FIXED: Never mix float and Decimal — preserve decimal precision
        if isinstance(other, float):
            other = Decimal(str(other))
        return Decimal(self) - other

    def __rsub__(self, other: Any):
        # FIXED: Never mix float and Decimal — preserve decimal precision
        if isinstance(other, float):
            other = Decimal(str(other))
        return other - Decimal(self)

_LGD_FLOOR = Decimal("0.40")
_LGD_CEIL  = Decimal("0.95")

# DPD bucket definitions (inclusive lower, exclusive upper)
_DPD_BUCKET_LABELS: List[tuple] = [
    ("current", 0, 1),
    ("1_30", 1, 31),
    ("31_60", 31, 61),
    ("61_90", 61, 91),
    ("90_plus", 91, None),
]


def _first_existing_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> Optional[str]:
    return next((column for column in candidates if column in df.columns), None)


def _numeric_series(df: pd.DataFrame, candidates: tuple[str, ...]) -> pd.Series:
    column = _first_existing_column(df, candidates)
    if column is None:
        return pd.Series(0, index=df.index, dtype="float64")
    return pd.to_numeric(df[column], errors="coerce").fillna(0)


def _status_series(df: pd.DataFrame) -> pd.Series:
    column = _first_existing_column(df, ("status", "loan_status", "estado"))
    if column is None:
        return pd.Series("", index=df.index, dtype="string")
    return df[column].astype("string").str.lower().fillna("")


def _defaulted_mask(df: pd.DataFrame) -> pd.Series:
    if "default_flag" in df.columns:
        return df["default_flag"].fillna(False).astype(bool)
    return _status_series(df).eq("defaulted")


def _active_loan_mask(df: pd.DataFrame) -> pd.Series:
    status = _status_series(df)
    if status.eq("").all():
        return pd.Series(True, index=df.index, dtype=bool)
    return ~status.eq("closed")


def _quantize_ratio(value: Decimal) -> ComparableDecimal:
    return ComparableDecimal(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def compute_default_rate_by_count(portfolio_mart: pd.DataFrame) -> Decimal:
    if portfolio_mart.empty:
        raise ValueError(
            "CRITICAL: default_rate_by_count() received empty portfolio. "
            "Provide at least one valid loan record."
        )
    active_mask = _active_loan_mask(portfolio_mart)
    active_count = int(active_mask.sum())
    if active_count == 0:
        return ComparableDecimal("0.0")
    defaulted_count = int((_defaulted_mask(portfolio_mart) & active_mask).sum())
    return _quantize_ratio(Decimal(defaulted_count) / Decimal(active_count))


def compute_default_rate_by_balance(portfolio_mart: pd.DataFrame) -> Decimal:
    if portfolio_mart.empty:
        raise ValueError(
            "CRITICAL: default_rate_by_balance() received empty portfolio. "
            "Provide at least one valid loan record."
        )
    balance = _numeric_series(portfolio_mart, ("outstanding_principal", "outstanding_balance", "principal_balance", "current_balance", "amount"))
    active_mask = _active_loan_mask(portfolio_mart)
    total_balance = Decimal(str(balance.loc[active_mask].sum()))
    if total_balance == 0:
        return ComparableDecimal("0.0")
    defaulted_balance = Decimal(str(balance.loc[_defaulted_mask(portfolio_mart) & active_mask].sum()))
    return _quantize_ratio(defaulted_balance / total_balance)


def compute_npl_ratio(portfolio_mart: pd.DataFrame) -> Decimal:
    if portfolio_mart.empty:
        raise ValueError(
            "CRITICAL: npl_ratio() received empty portfolio. "
            "Provide at least one valid loan record."
        )
    balance = _numeric_series(portfolio_mart, ("outstanding_principal", "outstanding_balance", "principal_balance", "current_balance", "amount"))
    dpd = _numeric_series(portfolio_mart, ("days_past_due", "dpd", "dpd_adjusted"))
    active_mask = _active_loan_mask(portfolio_mart)
    total_balance = Decimal(str(balance.loc[active_mask].sum()))
    if total_balance == 0:
        return ComparableDecimal("0.0")
    npl_mask = ((dpd >= 90) | _defaulted_mask(portfolio_mart)) & active_mask
    npl_balance = Decimal(str(balance.loc[npl_mask].sum()))
    return _quantize_ratio(npl_balance / total_balance)


def compute_delinquency_rate_by_balance(portfolio_mart: pd.DataFrame) -> Decimal:
    if portfolio_mart.empty:
        return ComparableDecimal("0.0")
    balance = _numeric_series(portfolio_mart, ("outstanding_principal", "outstanding_balance", "principal_balance", "current_balance", "amount"))
    total_balance = Decimal(str(balance.sum()))
    if total_balance == 0:
        return ComparableDecimal("0.0")
    delinquent_balance = Decimal(str(balance.loc[_status_series(portfolio_mart).eq("delinquent")].sum()))
    return _quantize_ratio(delinquent_balance / total_balance)


def compute_par30(portfolio_mart: pd.DataFrame) -> Decimal:
    if portfolio_mart.empty:
        raise ValueError(
            "CRITICAL: par30() received empty portfolio. "
            "Provide at least one valid loan record."
        )
    total = Decimal(str(portfolio_mart["outstanding_principal"].fillna(0).sum()))
    if total == 0:
        return ComparableDecimal("0.0")
    overdue = Decimal(str(portfolio_mart.loc[
        portfolio_mart["days_past_due"].fillna(0) >= 30,
        "outstanding_principal",
    ].sum()))
    return ComparableDecimal((overdue / total).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def compute_par60(portfolio_mart: pd.DataFrame) -> Decimal:
    if portfolio_mart.empty:
        raise ValueError(
            "CRITICAL: par60() received empty portfolio. "
            "Provide at least one valid loan record."
        )
    total = Decimal(str(portfolio_mart["outstanding_principal"].fillna(0).sum()))
    if total == 0:
        return ComparableDecimal("0.0")
    overdue = Decimal(str(portfolio_mart.loc[
        portfolio_mart["days_past_due"].fillna(0) >= 60,
        "outstanding_principal",
    ].sum()))
    return ComparableDecimal((overdue / total).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def compute_par90(portfolio_mart: pd.DataFrame) -> Decimal:
    if portfolio_mart.empty:
        raise ValueError(
            "CRITICAL: par90() received empty portfolio. "
            "Provide at least one valid loan record."
        )
    total = Decimal(str(portfolio_mart["outstanding_principal"].fillna(0).sum()))
    if total == 0:
        return ComparableDecimal("0.0")
    overdue = Decimal(str(portfolio_mart.loc[
        portfolio_mart["days_past_due"].fillna(0) >= 90,
        "outstanding_principal",
    ].sum()))
    return ComparableDecimal((overdue / total).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def compute_provision_coverage_ratio(
    portfolio_mart: pd.DataFrame,
    finance_mart: pd.DataFrame,
) -> Decimal:
    """
    Compute Provision Coverage Ratio.
    Formula: SUM(provision_expense) / SUM(outstanding_principal WHERE dpd >= 90 OR default_flag = True)
    
    FIXED: Fail-fast on empty input or zero NPL balance.
    Returns Decimal("[0.0, 999.9]" representing coverage %. Never returns nonsensical 100% when NPL=0.
    """
    if portfolio_mart.empty or finance_mart.empty:
        raise ValueError(
            "CRITICAL: provision_coverage_ratio() received empty portfolio or finance data. "
            "Provide complete portfolio and finance datasets."
        )

    provision_col = "provision_expense" if "provision_expense" in finance_mart.columns else None
    total_provisions = Decimal(str(finance_mart[provision_col].fillna(0).sum())) if provision_col else Decimal("0.0")

    balance = _numeric_series(
        portfolio_mart,
        ("outstanding_principal", "outstanding_balance", "principal_balance", "current_balance", "amount"),
    )
    dpd = _numeric_series(portfolio_mart, ("days_past_due", "dpd", "dpd_adjusted"))
    npl_balance = Decimal(str(balance.loc[(dpd >= 90) | _defaulted_mask(portfolio_mart)].sum()))

    if npl_balance <= 0:
        raise ValueError(
            f"CRITICAL: NPL balance must be > 0 to compute provision coverage. "
            f"Got NPL balance = {npl_balance}. This suggests no non-performing loans exist."
        )

    return (total_provisions / npl_balance).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_lgd(
    total_disbursed: Decimal,
    total_recovered: Optional[Decimal],
    method: str,
    fixed_rate: Decimal = Decimal("0.90"),
    floor: Decimal = _LGD_FLOOR,
    ceil: Decimal = _LGD_CEIL,
) -> Decimal:
    """
    Compute Loss Given Default.

    Parameters
    ----------
    method : "empirical" | "fixed"
        "empirical" requires total_recovered to be non-None and > 0.
        Falls back to fixed_rate if empirical inputs are unavailable.

    Returns
    -------
    Decimal — LGD in [LGD_FLOOR, LGD_CEIL], ROUND_HALF_UP, 4dp.
    Never returns a float. Never silently returns 0.
    """
    if method == "empirical" and total_recovered is not None and total_disbursed > 0:
        recovery_rate = (total_recovered / total_disbursed).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        lgd = (Decimal("1") - recovery_rate).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        lgd = max(floor, min(ceil, lgd))
        logger.info(
            "lgd_computed method=empirical recovery_rate=%s lgd=%s",
            recovery_rate, lgd,
        )
        return lgd

    if method == "empirical":
        logger.warning(
            "lgd_fallback: empirical method requested but recovery data unavailable. "
            "Falling back to fixed_rate=%s. Audit this run.",
            fixed_rate,
        )

    lgd = fixed_rate.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    lgd = max(floor, min(ceil, lgd))
    return lgd


def compute_pd(
    df: pd.DataFrame,
    assignment_config: Dict[str, Any],
    scorecard_pd_col: str = "pd_scorecard",
) -> pd.Series:
    """
    Assign Probability of Default based on configuration.

    Parameters
    ----------
    df : pd.DataFrame
        Loan data containing 'days_past_due' and optionally status.
    assignment_config : dict
        Content of 'pd_assignment' from business_parameters.yml.
    scorecard_pd_col : str
        Name of the column containing scorecard-predicted PD.

    Returns
    -------
    pd.Series : PD values as Decimal.
    """
    source = assignment_config.get("source", "dpd_bucket")
    buckets = assignment_config.get("dpd_buckets", {})

    # Default mapping logic for buckets
    def _map_bucket_pd(dpd: float, status: str = "") -> Decimal:
        if status == "defaulted":
            return Decimal(str(buckets.get("defaulted", 1.0)))
        if dpd >= 180:
            return Decimal(str(buckets.get("dpd_180", 0.70)))
        if dpd >= 90:
            return Decimal(str(buckets.get("dpd_90", 0.35)))
        if dpd >= 60:
            return Decimal(str(buckets.get("dpd_60", 0.15)))
        if dpd >= 30:
            return Decimal(str(buckets.get("dpd_30", 0.05)))
        return Decimal(str(buckets.get("current", 0.005)))

    dpd_pd = df.apply(
        lambda x: _map_bucket_pd(
            float(x.get("days_past_due", 0)), str(x.get("status", ""))
        ),
        axis=1,
    )

    if source == "dpd_bucket" or scorecard_pd_col not in df.columns:
        return dpd_pd

    if scorecard_pd_col in df.columns:
        scorecard_values = df[scorecard_pd_col]
    else:
        scorecard_values = pd.Series(index=df.index, dtype=float)
    sc_pd = pd.to_numeric(scorecard_values, errors="coerce").fillna(dpd_pd.apply(float)).apply(lambda x: Decimal(str(x)))

    if source == "scorecard":
        return sc_pd

    if source == "blend":
        w_sc = Decimal(str(assignment_config.get("blend_weight_scorecard", 0.7)))
        w_dpd = Decimal(str(assignment_config.get("blend_weight_dpd", 0.3)))
        return (sc_pd * w_sc) + (dpd_pd * w_dpd)

    return dpd_pd


def compute_expected_loss(
    portfolio_mart: pd.DataFrame,
    scorecard_df: pd.DataFrame | None = None,
    business_params: Dict[str, Any] | None = None,
) -> Decimal:
    """
    Compute Expected Loss (EL = PD * LGD * EAD).

    Refined version for Phase 3:
    - PD assigned via compute_pd (scorecard vs buckets).
    - LGD computed via compute_lgd (empirical vs fixed).
    """
    df = portfolio_mart.copy()

    if df.empty:
        return Decimal("0.0")

    if business_params is None and scorecard_df is None:
        ead = pd.to_numeric(df.get("outstanding_principal"), errors="coerce").fillna(0).sum()
        logger.warning(
            "compute_expected_loss: no business_params and no scorecard_df provided. "
            "Falling back to hardcoded PD=0.03, LGD=0.45. "
            "Pass business_params from config/business_parameters.yml or a scorecard_df "
            "to obtain an auditable expected-loss estimate. Run ID unknown at this call site."
        )
        return Decimal(str(ead)) * Decimal("0.03") * Decimal("0.45")

    if scorecard_df is not None and {"loan_id", "pd", "lgd"}.issubset(scorecard_df.columns) and "loan_id" in df.columns:
        merged = df.merge(scorecard_df[["loan_id", "pd", "lgd"]], on="loan_id", how="left")
        ead = pd.to_numeric(merged.get("outstanding_principal"), errors="coerce").fillna(0.0).apply(lambda x: Decimal(str(x)))
        pd_values = pd.to_numeric(merged.get("pd"), errors="coerce").fillna(0.0).apply(lambda x: Decimal(str(x)))
        lgd_values = pd.to_numeric(merged.get("lgd"), errors="coerce").fillna(0.45).apply(lambda x: Decimal(str(x)))
        return (ead * pd_values * lgd_values).sum()

    # Load business parameters if not provided
    if business_params is None:
        try:
            from backend.src.pipeline.config import load_business_parameters
            business_params = load_business_parameters()
        except Exception as _bp_exc:
            logger.warning(
                "compute_expected_loss: failed to load business_parameters.yml (%s). "
                "PD bucket defaults will be used (current=0.5%%, dpd_30=5%%, dpd_60=15%%, "
                "dpd_90=35%%, dpd_180=70%%, defaulted=100%%) — EL output is NOT auditable "
                "against production configuration. Investigate config availability.",
                _bp_exc,
            )
            business_params = {}

    fin_params = business_params.get("financial_assumptions", {})
    pd_params = business_params.get("pd_assignment", {})

    # Scorecard integration
    if scorecard_df is not None and "loan_id" in scorecard_df.columns and "loan_id" in df.columns:
        sc_cols = ["loan_id"]
        if "pd_scorecard" in scorecard_df.columns:
            sc_cols.append("pd_scorecard")
        elif "pd" in scorecard_df.columns:
            sc_cols.append("pd")
        df = df.merge(scorecard_df[sc_cols], on="loan_id", how="left", suffixes=("", "_scorecard"))
        if "pd_scorecard" not in df.columns and "pd" in sc_cols:
            df["pd_scorecard"] = pd.to_numeric(df.get("pd"), errors="coerce")

    # Assign PD
    df["pd_final"] = compute_pd(df, pd_params, scorecard_pd_col="pd_scorecard").apply(lambda x: Decimal(str(x)))

    # Assign LGD
    method = fin_params.get("lgd_method", "fixed")
    fixed_rate = Decimal(str(fin_params.get("lgd_fixed_rate", "0.90")))
    lgd_floor = Decimal(str(fin_params.get("lgd_floor", str(_LGD_FLOOR))))
    lgd_ceil = Decimal(str(fin_params.get("lgd_ceil", str(_LGD_CEIL))))

    disbursed_col = (
        "principal_amount"
        if "principal_amount" in df.columns
        else ("original_principal" if "original_principal" in df.columns else "outstanding_principal")
    )
    recovered_col = (
        "recovery_amount"
        if "recovery_amount" in df.columns
        else ("recovered_amount" if "recovered_amount" in df.columns else "last_payment_amount")
    )

    disbursed_vals = pd.to_numeric(df[disbursed_col], errors="coerce") if disbursed_col in df.columns else pd.Series(0, index=df.index)
    recovered_vals = pd.to_numeric(df[recovered_col], errors="coerce") if recovered_col in df.columns else pd.Series(0, index=df.index)

    total_disbursed = Decimal(str(disbursed_vals.fillna(0).sum()))
    total_recovered = Decimal(str(recovered_vals.fillna(0).sum()))
    recovered_input = total_recovered if method == "empirical" else None

    # Use a single global LGD per run to ensure deterministic EL and auditability.
    global_lgd = compute_lgd(
        total_disbursed=total_disbursed,
        total_recovered=recovered_input,
        method=method,
        fixed_rate=fixed_rate,
        floor=lgd_floor,
        ceil=lgd_ceil,
    )
    df["lgd_final"] = global_lgd

    if "ead" not in df.columns:
        df["ead"] = df["outstanding_principal"].fillna(0).apply(lambda x: Decimal(str(x)))
    else:
        df["ead"] = df["ead"].apply(lambda x: Decimal(str(x)))

    return (df["pd_final"] * df["lgd_final"] * df["ead"]).sum()


def compute_dpd_risk_summary(portfolio_mart: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate DPD bucket risk summary with recommended actions.

    Legacy: calculate_dpd_migration_risk
    """
    if portfolio_mart.empty:
        return []

    balance = _numeric_series(
        portfolio_mart,
        ("outstanding_principal", "outstanding_balance", "principal_balance", "current_balance", "amount"),
    )
    dpd = _numeric_series(portfolio_mart, ("days_past_due", "dpd", "dpd_adjusted"))
    total_balance = Decimal(str(balance.sum()))

    # Bucket definitions with risk levels and actions
    buckets_def = [
        ("current", dpd <= 0, "low", "Monitor – no immediate action"),
        (
            "dpd_1_30",
            (dpd > 0) & (dpd <= 30),
            "medium",
            "Trigger early collection contact (SMS / call)",
        ),
        (
            "dpd_31_60",
            (dpd > 30) & (dpd <= 60),
            "high",
            "Escalate collection intensity – send formal notice",
        ),
        (
            "dpd_61_90",
            (dpd > 60) & (dpd <= 90),
            "critical",
            "Activate legal / field team and restructure review",
        ),
        (
            "dpd_90_plus",
            dpd > 90,
            "critical",
            "Full provision write-off candidate – activate recovery workflow",
        ),
    ]

    rows: List[Dict[str, Any]] = []
    for bucket_name, mask, risk_level, recommended_action in buckets_def:
        bucket_balance = Decimal(str(balance[mask].sum()))
        share = (
            (bucket_balance / total_balance * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if total_balance > 0
            else Decimal("0.00")
        )

        rows.append(
            {
                "bucket": bucket_name,
                "loan_count": int(mask.sum()),
                "balance": float(bucket_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "balance_share_pct": float(share),
                "risk_level": risk_level,
                "recommended_action": recommended_action,
            }
        )
    return rows


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


def compute_credit_quality_index(portfolio_mart: pd.DataFrame) -> Decimal:
    """Compute normalized credit quality index based on scores.

    Formula: (avg_score - 300) / 550 * 100
    Range: [0, 100]
    """
    if portfolio_mart.empty:
        return Decimal("0.0")

    score_col = _first_existing_column(portfolio_mart, ("credit_score", "equifax_score", "score"))
    if not score_col:
        return Decimal("0.0")

    scores = pd.to_numeric(portfolio_mart[score_col], errors="coerce").dropna()
    scores = scores[scores > 0]

    if scores.empty:
        return Decimal("0.0")

    avg_score = Decimal(str(scores.mean()))
    quality = (avg_score - Decimal("300")) / Decimal("550") * Decimal("100")

    return max(Decimal("0"), min(Decimal("100"), quality)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
