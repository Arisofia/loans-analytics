"""
CSV File Upload Interface for ABACO Loans Analytics.

This uploader accepts partial source tables (loan data, customer, collateral, schedules,
INTERMEDIA exports), normalizes aliases into pipeline canonical columns, and can process
either a single prepared file or a consolidated multi-file dataset.
"""

from __future__ import annotations

import re
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# Import pipeline components
from backend.src.pipeline.calculation import CalculationPhase
from backend.src.pipeline.config import PipelineConfig, load_business_rules, load_kpi_definitions
from backend.src.pipeline.ingestion import IngestionPhase
from backend.src.pipeline.output import OutputPhase
from backend.src.pipeline.transformation import TransformationPhase

PIPELINE_REQUIRED_COLUMNS = ["loan_id", "amount", "status"]

# Priority order for resolving borrower identity when classifying duplicate loan_id rows.
# Checked in order; the first column present in the DataFrame is used.
# This list is shared by _classify_loan_id_duplicates (csv_upload) and the Dashboard.
BORROWER_ID_COLS: tuple[str, ...] = (
    "borrower_id",
    "client_code",
    "client_name",
    "borrower_name",
)

ALIAS_MAP: dict[str, list[str]] = {
    "loan_id": [
        "id_loan",
        "idprestamo",
        "prestamo_id",
        "new_loan_id",
        "old_loan_id",
        "application_id",
        "numero_desembolso",
        "codigo_desembolso",
        "correlativo_de_operaciones",
        "nrc",
        "id",
    ],
    "borrower_id": [
        "customer_id",
        "customer_id_cust",
        "codcliente",
        "codcliente_",
        "codcliente_2",
        "codcliente1",
        "cliente_id",
        "borrower_id",
    ],
    "amount": [
        "loan_amount",
        "principal_amount",
        "principal_balance",
        "outstanding_balance",
        "current_balance",
        "saldo",
        "saldo_capital",
        "capital_pendiente",
        "monto_vigente",
        "monto_actual",
        "monto_total",
        "monto_del_desembolso",
        "monto_financiado_real_por_desembolso",
        "monto_total_aprobado_por_desembolso",
        "monto_financiado_real",
        "monto_total_aprobado",
        "monto",
        "monto_prestamo",
        "monto_financiado",
        "valor_financiado",
        "valor_factura",
        "importe",
        "capital",
    ],
    "outstanding_balance": [
        "outstanding_balance",
        "current_balance",
        "principal_balance",
        "totalsaldovigente",
        "saldo_vigente",
        "saldo_pendiente",
        "capital_pendiente",
        "saldo",
        "saldo_capital",
    ],
    "current_balance": [
        "current_balance",
        "outstanding_balance",
        "principal_balance",
        "totalsaldovigente",
        "saldo_vigente",
        "saldo_pendiente",
        "capital_pendiente",
        "saldo",
        "saldo_capital",
    ],
    "principal_amount": [
        "principal_amount",
        "loan_amount",
        "monto_del_desembolso",
        "monto_financiado_real_por_desembolso",
        "monto_total_aprobado_por_desembolso",
        "monto_financiado_real",
        "monto_total_aprobado",
        "montodesembolsado",
        "amount",
    ],
    "status": ["loan_status", "current_status", "estado", "estado_actual"],
    "days_past_due": [
        "dpd",
        "dias_mora",
        "dias_de_mora",
        "dias_en_mora",
        "dias_vencido",
        "mora_en_dias",
        "diias_mora_m",
        "dias_mora_m",
        "dias_atraso",
        "days_overdue",
    ],
    "origination_date": [
        "disbursement_date",
        "fecha_desembolso",
        "fechadesembolso",
        "fecha_de_desembolso",
        "fecha_originacion",
    ],
    "interest_rate": [
        "interest_rate_apr",
        "apr",
        "rate",
        "tasa",
        "tasainteres",
        "tasa_interes",
        "tasa_de_interes",
        "tasa_anual",
    ],
    "due_date": [
        "due_date",
        "fechapagoprogramado",
        "fecha_vencimiento",
        "fecha_de_vencimiento",
        "fecha_vto",
    ],
    "last_payment_date": [
        "last_payment_date",
        "payment_date",
        "fecha_de_pago",
        "fechacobro",
        "fecha_pago",
    ],
    "total_scheduled": [
        "scheduled_amount",
        "total_due",
        "monto_programado",
        "monto_cuota",
        "cuota",
        "valorcuota",
    ],
    "last_payment_amount": [
        "payment_amount",
        "monto_pagado",
        "ultimo_pago",
        "last_real_payment",
        "_pagado",
    ],
    "recovery_value": ["recovery_value_", "recovery_value", "recovery_amount"],
    "client_code": ["codcliente", "codcliente_", "codcliente_2", "codcliente1"],
    "client_name": [
        "cliente",
        "cliente_",
        "cliente1",
        "nombre_cliente",
        "nombre_del_cliente",
        "nombrecliente",
        "razon_social",
    ],
    "issuer_code": ["codemisor"],
    "issuer_name": ["emisor"],
    "company": ["company", "empresa", "compania"],
    "credit_line": ["lineacredito"],
    "kam_hunter": [
        "cod_kam_hunter",
        "cod_kam_hunter_",
        "cod_kam_hunter1",
        "cod_kam_hunter_1",
        "kam_hunter",
    ],
    "kam_farmer": [
        "cod_kam_farmer",
        "cod_kam_farmer_",
        "cod_kam_farmer1",
        "cod_kam_farmer_1",
        "kam_farmer",
    ],
    "advisory_channel": ["asesoriadigital"],
    "application_date": ["fechasolicitado"],
    "term_months": ["term_months", "plazo", "plazo_meses", "term_max", "term_ponderado"],
    "payment_frequency": ["payment_frequency", "frecuencia_pago", "tipo_pago"],
    "tpv": ["tpv", "ingreso_total_por_desembolso", "montototalabonado"],
    "utilization_pct": ["porcentaje_utilizado"],
    "collections_eligible": ["procede_a_cobrar"],
    "delinquency_definition": ["definicion_m"],
    "delinquency_bucket_raw": ["rango_m"],
    "credit_line_range": ["rango_de_la_linea"],
    "ministry": ["ministerio"],
    "government_sector": ["goes"],
    "capital_collected": ["capitalcobrado"],
    "total_payment_received": ["montototalabonado"],
    "mdsc_posted": ["mdscposteado"],
    "negotiation_days": ["diasnegociacion", "dias_negociacion"],
    "days_to_pay": ["dias_en_pagar"],
    "disbursement_count": ["numerodesembolsos"],
    "approved_value": ["valoraprobado"],
    "negotiation_income": ["ingreso_total_por_desembolso", "ingreso_pagadopendiente"],
    "commission_code": ["comision_cobrada"],
    "pending_income": ["ingresos_pendiente"],
}


def render_csv_upload() -> None:
    """Render CSV upload interface with validation and processing."""
    st.header("📤 CSV Data Upload")
    st.markdown("""
    Upload loan data files to process through the analytics pipeline.

    **Supported file types:** CSV, Excel (.xlsx, .xls)
    **Max file size:** 200 MB
    **Pipeline required columns after mapping:** loan_id, amount, status
    """)

    uploaded_files = st.file_uploader(
        "Choose CSV/Excel file(s)",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        help=(
            "You can upload one consolidated file or multiple source tables. "
            "The uploader maps aliases automatically."
        ),
    )

    if not uploaded_files:
        st.info("👆 Upload file(s) to get started")
        return

    st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")

    prepared_frames: list[tuple[str, pd.DataFrame]] = []
    for idx, uploaded_file in enumerate(uploaded_files, 1):
        raw_df = _read_uploaded_file(uploaded_file)
        prepared_df = _prepare_dataframe(raw_df)
        prepared_frames.append((uploaded_file.name, prepared_df))

        with st.expander(
            f"📄 {uploaded_file.name} ({_format_file_size(uploaded_file.size)})",
            expanded=(idx == 1),
        ):
            st.write(f"**Rows:** {len(raw_df):,} | **Columns:** {len(raw_df.columns)}")
            st.subheader("📊 Data Preview")
            st.dataframe(_to_arrow_safe_display_df(raw_df.head(10)), width="stretch")

            with st.expander("📋 Column Information"):
                col_info = pd.DataFrame(
                    {
                        "Column": raw_df.columns,
                        "Type": raw_df.dtypes.astype(str),
                        "Non-Null": raw_df.notna().sum(),
                        "Null": raw_df.isna().sum(),
                        "Null %": (raw_df.isna().sum() / len(raw_df) * 100).round(2),
                    }
                )
                st.dataframe(_to_arrow_safe_display_df(col_info), width="stretch")

            st.subheader("✅ Validation Checks")
            _render_validation(prepared_df)

            if st.button(
                f"🚀 Process {uploaded_file.name}",
                key=f"process_{uploaded_file.name}",
                type="primary",
            ):
                valid, missing, issues, notices = _validate_for_pipeline(prepared_df)
                if not valid:
                    st.error(
                        "Cannot process this file yet. Missing required columns after mapping: "
                        + ", ".join(missing)
                    )
                elif issues:
                    st.warning("Data quality warnings: " + " | ".join(issues))
                elif notices:
                    st.info("Validation notes: " + " | ".join(notices))
                _run_pipeline(prepared_df, f"prepared_{_safe_filename(uploaded_file.name)}.csv")

    if len(prepared_frames) > 1:
        st.markdown("---")
        st.subheader("🧩 Consolidated Dataset (All Uploaded Files)")
        consolidated = _merge_prepared_frames([frame for _, frame in prepared_frames])
        valid, missing, issues, notices = _validate_for_pipeline(consolidated)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", f"{len(consolidated):,}")
        with col2:
            st.metric("Columns", len(consolidated.columns))
        with col3:
            st.metric(
                "Unique loan_id",
                int(consolidated["loan_id"].nunique()) if "loan_id" in consolidated.columns else 0,
            )

        st.dataframe(_to_arrow_safe_display_df(consolidated.head(15)), width="stretch")
        _render_validation(consolidated)

        if st.button("🚀 Process Consolidated Dataset", key="process_consolidated", type="primary"):
            if not valid:
                st.error(
                    "Cannot process consolidated dataset. Missing required columns after mapping: "
                    + ", ".join(missing)
                )
            else:
                if issues:
                    st.warning("Data quality warnings: " + " | ".join(issues))
                elif notices:
                    st.info("Validation notes: " + " | ".join(notices))
                _run_pipeline(consolidated, "consolidated_upload.csv")


def _read_uploaded_file(uploaded_file: Any) -> pd.DataFrame:
    uploaded_file.seek(0)
    if str(uploaded_file.name).lower().endswith(".csv"):
        return pd.read_csv(uploaded_file, low_memory=False)
    return pd.read_excel(uploaded_file)


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = (
        normalized.columns.astype(str)
        .str.normalize("NFKD")
        .str.encode("ascii", "ignore")
        .str.decode("ascii")
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    return normalized


def _to_arrow_safe_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert object columns to nullable strings for Streamlit/Arrow rendering.
    """
    safe = df.copy()
    for col in safe.columns:
        series = safe[col]
        if series.dtype == "object":
            safe[col] = series.map(_stringify_nullable).astype("string")
    return safe


def _stringify_nullable(value: Any) -> Any:
    if pd.isna(value):
        return pd.NA
    if isinstance(value, bytes):
        for encoding in ("utf-8", "latin-1"):
            try:
                return value.decode(encoding)
            except Exception:
                continue
        return repr(value)
    return str(value)


def _alias_matches(columns: list[str], alias: str) -> list[str]:
    """
    Return exact and suffix variations for one alias.

    Supports duplicate-column patterns after CSV parsing/normalization like:
    - codcliente_
    - codcliente_2
    - codcliente1
    """
    pattern = re.compile(rf"^{re.escape(alias)}(?:_?\d+|_+)?$")
    return [col for col in columns if col == alias or bool(pattern.match(col))]


def _apply_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build canonical columns by coalescing all matching alias columns.
    """
    normalized = df.copy()
    all_columns = list(normalized.columns)
    canonical_values: dict[str, pd.Series] = {}

    for canonical, aliases in ALIAS_MAP.items():
        candidates: list[str] = []
        seen: set[str] = set()
        for alias in [canonical, *aliases]:
            for match in _alias_matches(all_columns, alias):
                if match not in seen and match in normalized.columns:
                    seen.add(match)
                    candidates.append(match)
        if not candidates:
            continue
        if len(candidates) == 1:
            canonical_values[canonical] = normalized[candidates[0]]
            continue
        merged_series = _coalesce_series(
            [_nullify_missing_entries(normalized[col]) for col in candidates],
            index=normalized.index,
        )
        canonical_values[canonical] = merged_series

    if canonical_values:
        normalized = normalized.assign(**canonical_values)
    return normalized.copy()


def _nullify_missing_entries(series: pd.Series) -> pd.Series:
    """Normalize textual missing markers to <NA> without dtype downcast warnings."""
    text = series.astype(str).str.strip().str.lower()
    missing_mask = series.isna() | text.isin({"", "nan", "none", "null"})
    return series.where(~missing_mask, pd.NA)


def _coalesce_series(
    series_list: list[pd.Series], index: pd.Index, default: Any = pd.NA
) -> pd.Series:
    """Return first non-null value across candidate series without using bfill."""
    if not series_list:
        if isinstance(default, pd.Series):
            return default.reindex(index)
        return pd.Series(default, index=index)

    merged = series_list[0].copy()
    for candidate in series_list[1:]:
        fill_mask = merged.isna() & candidate.notna()
        if fill_mask.any():
            merged = merged.where(~fill_mask, candidate)

    if default is pd.NA:
        return merged
    return merged.where(merged.notna(), default)


def _to_datetime_mixed(series: pd.Series) -> pd.Series:
    """Parse mixed-format date columns while remaining compatible with older pandas."""
    try:
        return pd.to_datetime(series, errors="coerce", format="mixed")
    except TypeError:
        return pd.to_datetime(series, errors="coerce")


def _canonicalize_status(value: Any) -> str:
    raw = str(value).strip().lower()
    if not raw or raw == "nan":
        return "active"

    active_aliases = {"active", "current", "vigente", "open", "in_force"}
    closed_aliases = {
        "closed",
        "complete",
        "completed",
        "paid",
        "paid_off",
        "paid-off",
        "cancelled",
        "canceled",
        "liquidated",
    }
    delinquent_aliases = {"delinquent", "late", "past_due", "arrears", "mora"}
    defaulted_aliases = {"default", "defaulted", "charged_off", "charge_off", "written_off"}

    if raw in active_aliases:
        return "active"
    if raw in closed_aliases:
        return "closed"
    if raw in delinquent_aliases:
        return "delinquent"
    if raw in defaulted_aliases:
        return "defaulted"
    if "90+" in raw or "default" in raw or "charged" in raw:
        return "defaulted"
    if "60" in raw or "30" in raw or "mora" in raw or "past due" in raw:
        return "delinquent"
    return "unknown"


def _coerce_numeric(series: pd.Series) -> pd.Series:
    return _coerce_numeric_nullable(series).fillna(0.0)


def _coerce_numeric_nullable(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    text = text.mask(text.isin({"", "nan", "none", "null"}), pd.NA)
    cleaned = text.str.replace(r"[^0-9,.\-]", "", regex=True)

    comma_only_mask = cleaned.str.contains(",", na=False) & ~cleaned.str.contains(r"\.", na=False)
    thousands_mask = comma_only_mask & cleaned.str.contains(r",\d{3}$", regex=True, na=False)
    decimal_comma_mask = comma_only_mask & ~thousands_mask

    if thousands_mask.any():
        cleaned.loc[thousands_mask] = cleaned.loc[thousands_mask].str.replace(",", "", regex=False)
    if decimal_comma_mask.any():
        cleaned.loc[decimal_comma_mask] = cleaned.loc[decimal_comma_mask].str.replace(
            ",", ".", regex=False
        )
    other_mask = ~comma_only_mask
    if other_mask.any():
        cleaned.loc[other_mask] = cleaned.loc[other_mask].str.replace(",", "", regex=False)

    return pd.to_numeric(cleaned, errors="coerce")


def _derive_status(df: pd.DataFrame) -> pd.Series:
    dpd_col = (
        "days_past_due" if "days_past_due" in df.columns else "dpd" if "dpd" in df.columns else None
    )
    dpd = _coerce_numeric(df[dpd_col]) if dpd_col else None

    if "status" in df.columns:
        status = df["status"].apply(_canonicalize_status).astype(object)
        if dpd is not None:
            delinquent_mask = (dpd > 0) & (dpd < 90)
            defaulted_mask = dpd >= 90

            # DPD-based overrides when status is generic/unknown.
            status = status.mask(status.isin(["active", "unknown"]) & delinquent_mask, "delinquent")
            status = status.mask(status.isin(["active", "unknown"]) & defaulted_mask, "defaulted")
            status = status.mask(status == "unknown", "active")
        return status

    if dpd is not None:
        status = pd.Series(["active"] * len(df), index=df.index, dtype=object)
        status = status.mask((dpd > 0) & (dpd < 90), "delinquent")
        status = status.mask(dpd >= 90, "defaulted")
        return status

    return pd.Series(["active"] * len(df), index=df.index, dtype=object)


def _derive_amount(df: pd.DataFrame) -> pd.Series:
    amount_sources: list[pd.Series] = []
    if "amount" in df.columns:
        amount_sources.append(_coerce_numeric_nullable(df["amount"]).rename("amount"))

    for fallback_col in [
        "outstanding_balance",
        "current_balance",
        "principal_balance",
        "totalsaldovigente",
        "saldo_vigente",
        "saldo_pendiente",
        "capital_pendiente",
        "saldo",
        "saldo_capital",
        "principal_amount",
        "loan_amount",
        "monto_del_desembolso",
        "monto_financiado_real_por_desembolso",
        "monto_total_aprobado_por_desembolso",
        "monto_financiado_real",
        "monto_total_aprobado",
        "montodesembolsado",
    ]:
        if fallback_col in df.columns:
            amount_sources.append(_coerce_numeric_nullable(df[fallback_col]).rename(fallback_col))

    if not amount_sources:
        return pd.Series(0.0, index=df.index, dtype=float)
    return _coalesce_series(amount_sources, index=df.index, default=0.0)


def _prepare_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    prepared = _apply_aliases(_normalize_column_names(raw_df))
    prepared = prepared.loc[:, ~prepared.columns.duplicated()]

    if "loan_id" in prepared.columns:
        prepared["loan_id"] = prepared["loan_id"].astype(str).str.strip()
        prepared = prepared[prepared["loan_id"] != ""].copy()

    # Consolidate blocks before adding canonical columns to reduce fragmentation warnings.
    prepared = prepared.copy()
    prepared = prepared.assign(
        amount=_derive_amount(prepared),
        status=_derive_status(prepared),
    )

    # Derive canonical balance/amount fields expected by KPI formulas.
    balance_sources: list[pd.Series] = []
    for source_col in [
        "totalsaldovigente",
        "saldo_vigente",
        "saldo_pendiente",
        "capital_pendiente",
        "saldo",
        "saldo_capital",
        "outstanding_balance",
        "current_balance",
        "amount",
    ]:
        if source_col in prepared.columns:
            balance_sources.append(
                _coerce_numeric_nullable(prepared[source_col]).rename(source_col)
            )

    principal_sources: list[pd.Series] = []
    for source_col in [
        "principal_amount",
        "loan_amount",
        "monto_del_desembolso",
        "monto_financiado_real_por_desembolso",
        "monto_total_aprobado_por_desembolso",
        "monto_financiado_real",
        "monto_total_aprobado",
        "montodesembolsado",
        "amount",
    ]:
        if source_col in prepared.columns:
            principal_sources.append(
                _coerce_numeric_nullable(prepared[source_col]).rename(source_col)
            )

    balance_series = _coalesce_series(balance_sources, index=prepared.index, default=0.0)
    principal_series = _coalesce_series(
        principal_sources,
        index=prepared.index,
        default=prepared["amount"],
    )

    prepared = prepared.assign(
        outstanding_balance=_coerce_numeric(balance_series),
        current_balance=_coerce_numeric(balance_series),
        principal_amount=_coerce_numeric(principal_series),
        amount=_coerce_numeric(prepared["amount"]),
    )

    # Provide generic 'balance' alias used by some KPI formulas.
    if "balance" not in prepared.columns:
        prepared = prepared.assign(balance=prepared["outstanding_balance"])

    numeric_updates: dict[str, pd.Series] = {}
    for numeric_col in [
        "days_past_due",
        "interest_rate",
        "last_payment_amount",
        "total_scheduled",
        "recovery_value",
        "term_months",
        "tpv",
        "current_balance",
        "outstanding_balance",
        "principal_amount",
        "balance",
    ]:
        if numeric_col in prepared.columns:
            numeric_updates[numeric_col] = _coerce_numeric(prepared[numeric_col])
    if numeric_updates:
        prepared = prepared.assign(**numeric_updates)

    if "interest_rate" in prepared.columns:
        numeric_rate = _coerce_numeric(prepared["interest_rate"])
        if not numeric_rate.empty and numeric_rate.median() > 1:
            numeric_rate = numeric_rate / 100.0
        prepared = prepared.assign(interest_rate=numeric_rate)

    date_updates: dict[str, pd.Series] = {}
    application_dt: pd.Series | None = None
    if "application_date" in prepared.columns:
        application_dt = _to_datetime_mixed(prepared["application_date"])
        date_updates["application_date"] = application_dt

    if "origination_date" in prepared.columns:
        origination_dt = _to_datetime_mixed(prepared["origination_date"])
        if application_dt is not None:
            origination_dt = origination_dt.where(origination_dt.notna(), application_dt)
        date_updates["origination_date"] = origination_dt
    elif application_dt is not None:
        date_updates["origination_date"] = application_dt

    if "due_date" in prepared.columns:
        date_updates["due_date"] = _to_datetime_mixed(prepared["due_date"])

    if "last_payment_date" in prepared.columns:
        date_updates["last_payment_date"] = _to_datetime_mixed(prepared["last_payment_date"])

    if "maturity_date" in prepared.columns:
        date_updates["maturity_date"] = _to_datetime_mixed(prepared["maturity_date"])

    if date_updates:
        prepared = prepared.assign(**date_updates)

    # If borrower_name is missing, reuse mapped client_name to keep loan↔client association visible.
    if "borrower_name" not in prepared.columns and "client_name" in prepared.columns:
        prepared = prepared.assign(borrower_name=prepared["client_name"])
    elif "borrower_name" in prepared.columns and "client_name" in prepared.columns:
        borrower_series = _nullify_missing_entries(prepared["borrower_name"])
        client_series = _nullify_missing_entries(prepared["client_name"])
        fill_mask = borrower_series.isna() & client_series.notna()
        prepared = prepared.assign(borrower_name=borrower_series.where(~fill_mask, client_series))

    return prepared.copy()


def _collapse_to_loan_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse repeated rows per loan_id to avoid many-to-many merge explosions.

    Strategy:
    - Normalize and keep non-empty loan_id rows.
    - Build an event ordering using available date columns.
    - Keep the latest non-null value per column inside each loan_id group.
    """
    if "loan_id" not in df.columns:
        return df

    work = df.copy()
    work["loan_id"] = work["loan_id"].astype(str).str.strip()
    work = work[work["loan_id"] != ""].copy()
    if work.empty:
        return work

    date_candidates = [
        "as_of_date",
        "snapshot_date",
        "measurement_date",
        "reporting_date",
        "last_payment_date",
        "origination_date",
        "application_date",
        "maturity_date",
    ]
    present_dates = [col for col in date_candidates if col in work.columns]
    if present_dates:
        work = work.assign(**{col: _to_datetime_mixed(work[col]) for col in present_dates})

    event_date = (
        work[present_dates].max(axis=1) if present_dates else pd.Series(pd.NaT, index=work.index)
    )
    work = work.assign(_event_date=event_date, _row_order=range(len(work))).copy()
    work = work.sort_values(
        ["loan_id", "_event_date", "_row_order"],
        ascending=[True, True, True],
        na_position="last",
    )
    work = work.copy()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
        collapsed = work.groupby("loan_id", as_index=False).last()
    collapsed = collapsed.drop(columns=["_event_date", "_row_order"], errors="ignore")
    return collapsed


def _merge_prepared_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()

    normalized_frames = [_prepare_dataframe(frame) for frame in frames]
    stacked = pd.concat(normalized_frames, ignore_index=True, sort=False).copy()

    # Resolve cross-source overlap by most recent event_date per loan_id while
    # keeping the latest non-null value per column.
    if "loan_id" in stacked.columns:
        stacked = _collapse_to_loan_level(stacked)

    merged = _prepare_dataframe(stacked)
    if "loan_id" in merged.columns:
        merged = _collapse_to_loan_level(merged)
    return merged.copy()


def _classify_loan_id_duplicates(df: pd.DataFrame) -> list[tuple[str, str]]:
    """Classify duplicate loan_id rows into typed groups.

    Returns a list of (level, message) pairs where level is ``"warning"`` or
    ``"info"``, covering three distinct scenarios:

    * **Exact duplicates** – same ``loan_id`` + same borrower + same
      ``amount``.  These are data entry errors and should be deduplicated
      before pipeline execution.  Reported as ``"warning"``.
    * **Historical snapshots** – same ``loan_id`` + same borrower +
      *different* ``amount``.  These represent balance-rollup snapshots and
      are expected.  Reported as ``"info"``.
    * **Suspicious merges** – same ``loan_id`` shared by *different*
      borrower values.  Indicates a likely data-quality issue.
      Reported as ``"warning"``.

    The borrower identifier is resolved from the first available column among:
    ``borrower_id``, ``client_code``, ``client_name``, ``borrower_name``.
    This makes the function robust to pre- and post-homologation DataFrames.
    """
    if "loan_id" not in df.columns:
        return []

    # Work from the raw column to detect true nulls before any stringification.
    loan_id_raw = df["loan_id"]
    id_is_null = loan_id_raw.isna()
    id_series = loan_id_raw.astype(str).str.strip()
    # Exclude null/empty/sentinel values so NaN / NA loan_ids are not treated as a real ID.
    # Include the stringified representation of pd.NA ("<NA>") to robustly handle nullable dtypes.
    null_sentinels = frozenset({"nan", "None", "NaN", "none", "NA", "", "<NA>"})
    valid_id_mask = ~(id_is_null | id_series.isin(null_sentinels))
    dup_mask = id_series.duplicated(keep=False) & valid_id_mask
    if not dup_mask.any():
        return []

    dup_df = df[dup_mask].copy()
    dup_df["_loan_id_str"] = id_series[dup_mask]

    # Resolve borrower key: accept any common identifier column so the function
    # works correctly both before and after alias homologation.
    borrower_col = next((c for c in BORROWER_ID_COLS if c in dup_df.columns), None)
    has_borrower = borrower_col is not None
    has_amount = "amount" in dup_df.columns

    exact_dup_count: int = 0
    snapshot_count: int = 0
    suspicious_count: int = 0
    generic_count: int = 0

    for _, group in dup_df.groupby("_loan_id_str", sort=False):
        if len(group) < 2:
            continue

        # Determine whether we actually have any borrower information for this group.
        # If the borrower column exists but is entirely null within this loan_id group,
        # treat borrower as unavailable and fall back to generic classification instead
        # of treating it as "same borrower" based on amount alone.
        borrower_info_available = has_borrower and group[borrower_col].notna().any()

        if borrower_info_available:
            unique_borrowers = group[borrower_col].dropna().nunique()

            if unique_borrowers > 1:
                suspicious_count += 1
            elif has_amount:
                if group["amount"].nunique() == 1:
                    exact_dup_count += 1
                else:
                    snapshot_count += 1
            else:
                generic_count += 1
        else:
            # Borrower is unavailable for this group (no column or all-null),
            # so don't attempt exact/snapshot classification based on amount.
            generic_count += 1

    messages: list[tuple[str, str]] = []
    if exact_dup_count:
        messages.append(
            (
                "warning",
                f"{exact_dup_count} loan_id(s) have exact duplicate rows "
                "(same borrower, same amount) — consider deduplicating before processing",
            )
        )
    if snapshot_count:
        messages.append(
            (
                "info",
                f"{snapshot_count} loan_id(s) appear as historical snapshots "
                "(same borrower, different amounts) — treated as balance rollups",
            )
        )
    if suspicious_count:
        messages.append(
            (
                "warning",
                f"{suspicious_count} loan_id(s) are shared across different borrowers "
                "(suspicious merge) — verify source data integrity",
            )
        )
    if generic_count:
        messages.append(
            (
                "warning",
                f"{generic_count} loan_id(s) have duplicate rows "
                "(borrower/amount columns unavailable for detailed classification)",
            )
        )
    return messages


def _validate_for_pipeline(df: pd.DataFrame) -> tuple[bool, list[str], list[str], list[str]]:
    missing = [col for col in PIPELINE_REQUIRED_COLUMNS if col not in df.columns]
    issues: list[str] = []
    notices: list[str] = []

    if "loan_id" in df.columns:
        if df["loan_id"].astype(str).str.strip().eq("").all():
            issues.append("All loan_id values are empty")
        else:
            for level, message in _classify_loan_id_duplicates(df):
                if level == "info":
                    notices.append(message)
                else:
                    issues.append(message)

    if "amount" in df.columns and pd.to_numeric(df["amount"], errors="coerce").eq(0).all():
        issues.append("All amount values are zero after mapping")

    if "status" in df.columns and df["status"].astype(str).str.strip().eq("").all():
        issues.append("All status values are empty")

    return len(missing) == 0, missing, issues, notices


def _render_validation(df: pd.DataFrame) -> None:
    valid, missing, issues, notices = _validate_for_pipeline(df)
    if valid:
        st.success(
            "✅ Required pipeline columns present after alias mapping (loan_id, amount, status)"
        )
    else:
        st.error("❌ Missing required pipeline columns after alias mapping: " + ", ".join(missing))

    if issues:
        for issue in issues:
            st.warning(f"⚠️ {issue}")
    if notices:
        for notice in notices:
            st.info(f"ℹ️ {notice}")
    if not issues and not notices:
        st.success("✅ No critical data-quality warnings detected")


def _run_pipeline(df: pd.DataFrame, filename: str) -> None:
    """Execute the full data pipeline on a prepared dataset."""
    df = df.copy()
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path("logs/runs") / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        upload_meta = _build_upload_metadata(df, filename)
        (run_dir / "upload_metadata.json").write_text(
            json.dumps(upload_meta, indent=2, default=str)
        )

        input_path = run_dir / filename
        df.to_csv(input_path, index=False)

        pipeline_cfg = PipelineConfig.load()
        business_rules = load_business_rules()
        kpi_definitions = load_kpi_definitions()

        status_text.text("Phase 1/4: Ingesting data...")
        progress_bar.progress(25)
        ingestion = IngestionPhase(pipeline_cfg.ingestion)
        ingestion_result = ingestion.execute(input_path=input_path, run_dir=run_dir)
        if ingestion_result["status"] != "success":
            st.error(f"❌ Ingestion failed: {ingestion_result.get('error')}")
            return

        status_text.text("Phase 2/4: Transforming data...")
        progress_bar.progress(50)
        transformation = TransformationPhase(pipeline_cfg.transformation, business_rules)
        transform_result = transformation.execute(
            raw_data_path=run_dir / "raw_data.parquet", run_dir=run_dir
        )
        if transform_result["status"] != "success":
            st.error(f"❌ Transformation failed: {transform_result.get('error')}")
            return

        status_text.text("Phase 3/4: Calculating KPIs...")
        progress_bar.progress(75)
        calculation = CalculationPhase(pipeline_cfg.calculation, kpi_definitions)
        calc_result = calculation.execute(
            clean_data_path=run_dir / "clean_data.parquet", run_dir=run_dir
        )
        if calc_result["status"] != "success":
            st.error(f"❌ Calculation failed: {calc_result.get('error')}")
            return

        status_text.text("Phase 4/4: Generating outputs...")
        progress_bar.progress(90)
        output = OutputPhase(pipeline_cfg.output)
        output_result = output.execute(kpi_results=calc_result["kpis"], run_dir=run_dir)
        if output_result["status"] != "success":
            st.error(f"❌ Output failed: {output_result.get('error')}")
            return

        progress_bar.progress(100)
        status_text.text("✅ Pipeline completed successfully!")
        st.success(f"✅ Processing complete! Run ID: {run_id}")

        with st.expander("📊 Results Summary", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows Processed", f"{ingestion_result['row_count']:,}")
            with col2:
                st.metric("KPIs Calculated", calc_result["kpi_count"])
            with col3:
                st.metric("Data Quality", f"{transform_result.get('quality_score', 0.0):.1%}")

            st.subheader("Calculated KPIs")
            kpi_df = pd.DataFrame([calc_result["kpis"]]).T
            kpi_df.columns = ["Value"]
            st.dataframe(_to_arrow_safe_display_df(kpi_df), width="stretch")

        st.subheader("📥 Download Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            csv_path = run_dir / "kpis_output.csv"
            if csv_path.exists():
                with open(csv_path, "rb") as fh:
                    st.download_button(
                        "📄 Download CSV", fh, file_name=f"kpis_{run_id}.csv", mime="text/csv"
                    )

        with col2:
            json_path = run_dir / "kpis_output.json"
            if json_path.exists():
                with open(json_path, "rb") as fh:
                    st.download_button(
                        "📄 Download JSON",
                        fh,
                        file_name=f"kpis_{run_id}.json",
                        mime="application/json",
                    )

        with col3:
            parquet_path = run_dir / "kpis_output.parquet"
            if parquet_path.exists():
                with open(parquet_path, "rb") as fh:
                    st.download_button(
                        "📄 Download Parquet",
                        fh,
                        file_name=f"kpis_{run_id}.parquet",
                        mime="application/octet-stream",
                    )

    except Exception as exc:
        st.error(f"❌ Pipeline execution failed: {exc}")
        st.exception(exc)


def _build_upload_metadata(df: pd.DataFrame, filename: str) -> dict[str, Any]:
    as_of_date, as_of_source = _detect_as_of_date(df)
    tracked_fields = ["company", "credit_line", "kam_hunter", "kam_farmer"]
    field_non_empty: dict[str, int] = {}
    for field in tracked_fields:
        if field in df.columns:
            series = df[field]
            non_empty = ((~series.isna()) & (series.astype(str).str.strip() != "")).sum()
            field_non_empty[field] = int(non_empty)
        else:
            field_non_empty[field] = 0

    return {
        "source_file": filename,
        "uploaded_at": datetime.now().isoformat(),
        "detected_as_of_date": as_of_date,
        "detected_as_of_source": as_of_source,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "field_non_empty": field_non_empty,
    }


def _detect_as_of_date(df: pd.DataFrame) -> tuple[str | None, str | None]:
    primary_candidates = [
        "as_of_date",
        "snapshot_date",
        "measurement_date",
        "reporting_date",
        "fecha_corte",
        "fecha_de_corte",
        "cutoff_date",
        "data_ingest_ts",
    ]
    fallback_candidates = [
        "last_payment_date",
        "origination_date",
        "application_date",
    ]

    for col in [*primary_candidates, *fallback_candidates]:
        if col not in df.columns:
            continue
        try:
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True, format="mixed")
        except TypeError:
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
        max_dt = parsed.max()
        if pd.notna(max_dt):
            return str(max_dt.date()), col
    return None, None


def _safe_filename(name: str) -> str:
    normalized = "".join(ch if ch.isalnum() or ch in {".", "_", "-"} else "_" for ch in name)
    return normalized.strip("_") or "upload.csv"


def _format_file_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    st.set_page_config(page_title="CSV Upload - ABACO Analytics", page_icon="📤", layout="wide")
    render_csv_upload()
