"""
CSV File Upload Interface for ABACO Loans Analytics.

This uploader accepts partial source tables (loan data, customer, collateral, schedules,
INTERMEDIA exports), normalizes aliases into pipeline canonical columns, and can process
either a single prepared file or a consolidated multi-file dataset.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import pipeline components
try:
    from src.pipeline.calculation import CalculationPhase
    from src.pipeline.config import PipelineConfig, load_business_rules, load_kpi_definitions
    from src.pipeline.ingestion import IngestionPhase
    from src.pipeline.output import OutputPhase
    from src.pipeline.transformation import TransformationPhase
except ImportError as exc:
    st.error(f"❌ Pipeline modules not found: {exc}")
    st.info(f"Project root: {project_root}")
    st.info(f"sys.path: {sys.path[:3]}")
    st.stop()


PIPELINE_REQUIRED_COLUMNS = ["loan_id", "amount", "status"]

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
    "status": ["loan_status", "current_status", "estado", "estado_actual"],
    "days_past_due": ["dpd", "dias_mora", "dias_de_mora"],
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
        "tasa_interes",
        "tasa_de_interes",
        "tasa_anual",
    ],
    "total_scheduled": ["scheduled_amount", "total_due", "monto_programado"],
    "last_payment_amount": ["payment_amount", "monto_pagado", "ultimo_pago", "last_real_payment"],
    "recovery_value": ["recovery_value_", "recovery_value", "recovery_amount"],
    "client_code": ["codcliente", "codcliente_", "codcliente_2", "codcliente1"],
    "client_name": ["cliente", "cliente_", "cliente1"],
    "issuer_code": ["codemisor"],
    "issuer_name": ["emisor"],
    "credit_line": ["lineacredito"],
    "kam_hunter": ["cod_kam_hunter", "cod_kam_hunter_", "cod_kam_hunter1"],
    "kam_farmer": ["cod_kam_farmer", "cod_kam_farmer_", "cod_kam_farmer1"],
    "advisory_channel": ["asesoriadigital"],
    "application_date": ["fechasolicitado"],
    "utilization_pct": ["porcentaje_utilizado"],
}


def render_csv_upload() -> None:
    """Render CSV upload interface with validation and processing."""
    st.header("📤 CSV Data Upload")
    st.markdown(
        """
    Upload loan data files to process through the analytics pipeline.

    **Supported file types:** CSV, Excel (.xlsx, .xls)
    **Max file size:** 200 MB
    **Pipeline required columns after mapping:** loan_id, amount, status
    """
    )

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
            st.dataframe(raw_df.head(10), width="stretch")

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
                st.dataframe(col_info, width="stretch")

            st.subheader("✅ Validation Checks")
            _render_validation(prepared_df)

            if st.button(
                f"🚀 Process {uploaded_file.name}",
                key=f"process_{uploaded_file.name}",
                type="primary",
            ):
                valid, missing, issues = _validate_for_pipeline(prepared_df)
                if not valid:
                    st.error(
                        "Cannot process this file yet. Missing required columns after mapping: "
                        + ", ".join(missing)
                    )
                elif issues:
                    st.warning("Data quality warnings: " + " | ".join(issues))
                _run_pipeline(prepared_df, f"prepared_{_safe_filename(uploaded_file.name)}.csv")

    if len(prepared_frames) > 1:
        st.markdown("---")
        st.subheader("🧩 Consolidated Dataset (All Uploaded Files)")
        consolidated = _merge_prepared_frames([frame for _, frame in prepared_frames])
        valid, missing, issues = _validate_for_pipeline(consolidated)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", f"{len(consolidated):,}")
        with col2:
            st.metric("Columns", len(consolidated.columns))
        with col3:
            st.metric("Unique loan_id", int(consolidated["loan_id"].nunique()) if "loan_id" in consolidated.columns else 0)

        st.dataframe(consolidated.head(15), width="stretch")
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
            normalized[canonical] = normalized[candidates[0]]
            continue
        merged_series = normalized[candidates[0]]
        for col in candidates[1:]:
            merged_series = merged_series.combine_first(normalized[col])
        normalized[canonical] = merged_series

    return normalized


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
    text = series.astype(str).str.strip()
    text = text.replace({"": None, "nan": None, "None": None, "NaN": None})
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

    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)


def _derive_status(df: pd.DataFrame) -> pd.Series:
    if "status" in df.columns:
        return df["status"].apply(_canonicalize_status)
    if "days_past_due" in df.columns:
        dpd = _coerce_numeric(df["days_past_due"])
        status = pd.Series(["active"] * len(df), index=df.index, dtype=object)
        status = status.mask((dpd > 0) & (dpd < 90), "delinquent")
        status = status.mask(dpd >= 90, "defaulted")
        return status
    return pd.Series(["active"] * len(df), index=df.index, dtype=object)


def _derive_amount(df: pd.DataFrame) -> pd.Series:
    if "amount" in df.columns:
        amount = _coerce_numeric(df["amount"])
    else:
        amount = pd.Series([None] * len(df), index=df.index, dtype=float)
    for fallback_col in [
        "outstanding_balance",
        "current_balance",
        "principal_balance",
        "principal_amount",
        "loan_amount",
        "monto_del_desembolso",
        "monto_financiado_real_por_desembolso",
        "monto_total_aprobado_por_desembolso",
        "monto_financiado_real",
        "monto_total_aprobado",
    ]:
        if fallback_col in df.columns:
            fallback = _coerce_numeric(df[fallback_col])
            amount = amount.fillna(fallback)
    return amount.fillna(0.0)


def _prepare_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    prepared = _apply_aliases(_normalize_column_names(raw_df))
    prepared = prepared.loc[:, ~prepared.columns.duplicated()]

    if "loan_id" in prepared.columns:
        prepared["loan_id"] = prepared["loan_id"].astype(str).str.strip()
        prepared = prepared[prepared["loan_id"] != ""].copy()

    prepared["amount"] = _derive_amount(prepared)
    prepared["status"] = _derive_status(prepared)

    for numeric_col in [
        "days_past_due",
        "interest_rate",
        "last_payment_amount",
        "total_scheduled",
        "recovery_value",
        "current_balance",
        "outstanding_balance",
        "principal_amount",
    ]:
        if numeric_col in prepared.columns:
            prepared[numeric_col] = _coerce_numeric(prepared[numeric_col])

    if "interest_rate" in prepared.columns:
        numeric_rate = _coerce_numeric(prepared["interest_rate"])
        if not numeric_rate.empty and numeric_rate.median() > 1:
            numeric_rate = numeric_rate / 100.0
        prepared["interest_rate"] = numeric_rate

    if "origination_date" in prepared.columns:
        prepared["origination_date"] = pd.to_datetime(prepared["origination_date"], errors="coerce")
    elif "application_date" in prepared.columns:
        prepared["origination_date"] = pd.to_datetime(prepared["application_date"], errors="coerce")

    if "application_date" in prepared.columns:
        prepared["application_date"] = pd.to_datetime(prepared["application_date"], errors="coerce")
        if "origination_date" in prepared.columns:
            prepared["origination_date"] = prepared["origination_date"].fillna(
                prepared["application_date"]
            )

    return prepared


def _merge_prepared_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()

    merged = frames[0].copy()
    for frame in frames[1:]:
        if "loan_id" in merged.columns and "loan_id" in frame.columns:
            merged = merged.merge(frame, on="loan_id", how="outer", suffixes=("", "_dup"))
            dup_cols = [col for col in merged.columns if col.endswith("_dup")]
            for dup_col in dup_cols:
                base_col = dup_col[:-4]
                if base_col in merged.columns:
                    merged[base_col] = merged[base_col].combine_first(merged[dup_col])
                    merged = merged.drop(columns=[dup_col])
                else:
                    merged = merged.rename(columns={dup_col: base_col})
        else:
            merged = pd.concat([merged, frame], ignore_index=True, sort=False)
    return _prepare_dataframe(merged)


def _validate_for_pipeline(df: pd.DataFrame) -> tuple[bool, list[str], list[str]]:
    missing = [col for col in PIPELINE_REQUIRED_COLUMNS if col not in df.columns]
    issues: list[str] = []

    if "loan_id" in df.columns:
        if df["loan_id"].astype(str).str.strip().eq("").all():
            issues.append("All loan_id values are empty")
        duplicate_count = int(df["loan_id"].astype(str).duplicated().sum())
        if duplicate_count > 0:
            issues.append(f"{duplicate_count} duplicate loan_id values")

    if "amount" in df.columns and pd.to_numeric(df["amount"], errors="coerce").eq(0).all():
        issues.append("All amount values are zero after mapping")

    if "status" in df.columns and df["status"].astype(str).str.strip().eq("").all():
        issues.append("All status values are empty")

    return len(missing) == 0, missing, issues


def _render_validation(df: pd.DataFrame) -> None:
    valid, missing, issues = _validate_for_pipeline(df)
    if valid:
        st.success("✅ Required pipeline columns present after alias mapping (loan_id, amount, status)")
    else:
        st.error("❌ Missing required pipeline columns after alias mapping: " + ", ".join(missing))

    if issues:
        for issue in issues:
            st.warning(f"⚠️ {issue}")
    else:
        st.success("✅ No critical data-quality warnings detected")


def _run_pipeline(df: pd.DataFrame, filename: str) -> None:
    """Execute the full data pipeline on a prepared dataset."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path("logs/runs") / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

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
        transform_result = transformation.execute(raw_data_path=run_dir / "raw_data.parquet", run_dir=run_dir)
        if transform_result["status"] != "success":
            st.error(f"❌ Transformation failed: {transform_result.get('error')}")
            return

        status_text.text("Phase 3/4: Calculating KPIs...")
        progress_bar.progress(75)
        calculation = CalculationPhase(pipeline_cfg.calculation, kpi_definitions)
        calc_result = calculation.execute(clean_data_path=run_dir / "clean_data.parquet", run_dir=run_dir)
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
            st.dataframe(kpi_df, width="stretch")

        st.subheader("📥 Download Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            csv_path = run_dir / "kpis_output.csv"
            if csv_path.exists():
                with open(csv_path, "rb") as fh:
                    st.download_button("📄 Download CSV", fh, file_name=f"kpis_{run_id}.csv", mime="text/csv")

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
