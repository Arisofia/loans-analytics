#!/usr/bin/env python3
"""
ABACO LOANS ANALYTICS - Interactive Dashboard

Main Streamlit application for visualizing pipeline results and KPIs.
Serves as the frontend for the unified analytics platform.

Run with:
    streamlit run streamlit_app.py
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from api_client import AbacoAnalyticsApiClient
from python.logging_config import init_sentry

init_sentry(service_name="streamlit_app")

STANDARD_TREND_KPIS = [
    "par_30",
    "par_60",
    "par_90",
    "delinq_1_30_rate",
    "delinq_31_60_rate",
    "npl_ratio",
    "npl_90_ratio",
    "default_rate",
    "loss_rate",
    "cost_of_risk",
    "portfolio_yield",
    "portfolio_growth_rate",
    "disbursement_volume_mtd",
    "total_outstanding_balance",
    "total_loans_count",
    "active_borrowers",
]

REQUIRED_RUN_FIELDS = [
    "dpd",
    "current_balance",
    "amount",
    "company",
    "credit_line",
    "kam_hunter",
    "kam_farmer",
]

REQUIRED_FIELD_ALIASES: dict[str, list[str]] = {
    "dpd": ["dpd", "days_past_due", "dias_mora", "dias_de_mora"],
    "current_balance": ["current_balance", "outstanding_balance", "principal_balance"],
    "amount": [
        "amount",
        "principal_amount",
        "loan_amount",
        "monto_del_desembolso",
        "monto_financiado_real_por_desembolso",
        "monto_total_aprobado_por_desembolso",
        "monto_financiado_real",
        "monto_total_aprobado",
    ],
    "company": ["company", "Company"],
    "credit_line": ["credit_line", "lineacredito", "LineaCredito", "linea_credito"],
    "kam_hunter": ["kam_hunter", "cod_kam_hunter", "Cod_Kam_hunter", "cod_kam_hunter1"],
    "kam_farmer": ["kam_farmer", "cod_kam_farmer", "Cod_Kam_farmer", "cod_kam_farmer1"],
}

REQUIRED_RUN_KPIS = [
    "par_30",
    "par_60",
    "par_90",
    "delinq_1_30_rate",
    "delinq_31_60_rate",
    "npl_ratio",
    "npl_90_ratio",
    "default_rate",
    "loss_rate",
    "portfolio_yield",
    "cost_of_risk",
    "total_outstanding_balance",
    "total_loans_count",
]


def _run_type(run_id: str) -> str:
    run_id_l = run_id.lower()
    if run_id_l.endswith("_dry_run"):
        return "dry_run"
    if run_id_l.endswith("_validate"):
        return "validate"
    if "_pre_" in run_id_l:
        return "full_variant"
    return "full"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _load_run_dataframe(run_dir: Path) -> pd.DataFrame | None:
    dataset_paths = [run_dir / "clean_data.parquet", run_dir / "transformed.parquet"]
    for dataset_path in dataset_paths:
        if dataset_path.exists():
            try:
                return pd.read_parquet(dataset_path)
            except Exception:
                return None
    return None


def _load_upload_metadata(run_dir: Path) -> dict[str, Any]:
    return _load_json(run_dir / "upload_metadata.json")


def _resolve_series_by_aliases(df: pd.DataFrame, aliases: list[str]) -> pd.Series | None:
    lower_map = {col.lower(): col for col in df.columns}
    for alias in aliases:
        matched = lower_map.get(alias.lower())
        if matched is not None:
            return df[matched]
    return None


def _extract_run_timestamp(run_dir: Path, pipeline_results: dict[str, Any]) -> "pd.Timestamp":
    manifest = _load_json(run_dir / "calculation_manifest.json")
    manifest_ts = manifest.get("run_timestamp")
    if manifest_ts:
        ts = pd.to_datetime(manifest_ts, errors="coerce")
        if pd.notna(ts):
            return ts

    phases = pipeline_results.get("phases", {}) if isinstance(pipeline_results, dict) else {}
    output_phase = phases.get("output", {}) if isinstance(phases, dict) else {}
    phase_ts = output_phase.get("timestamp") if isinstance(output_phase, dict) else None
    if phase_ts:
        ts = pd.to_datetime(phase_ts, errors="coerce")
        if pd.notna(ts):
            return ts

    try:
        return pd.to_datetime(run_dir.name[:8], format="%Y%m%d", errors="coerce")
    except Exception:
        return pd.NaT


def _derive_as_of_date(
    run_dir: Path, pipeline_results: dict[str, Any], run_df: pd.DataFrame | None
) -> "pd.Timestamp":
    upload_meta = _load_upload_metadata(run_dir)
    detected_as_of = upload_meta.get("detected_as_of_date")
    if isinstance(detected_as_of, str) and detected_as_of.strip():
        parsed = pd.to_datetime(detected_as_of, errors="coerce")
        if pd.notna(parsed):
            return parsed

    primary_date_candidates = [
        "as_of_date",
        "snapshot_date",
        "measurement_date",
        "reporting_date",
        "data_ingest_ts",
    ]
    fallback_date_candidates = ["origination_date", "application_date"]

    if run_df is not None:
        for col in primary_date_candidates:
            if col in run_df.columns:
                parsed = pd.to_datetime(run_df[col], errors="coerce")
                max_dt = parsed.max()
                if pd.notna(max_dt):
                    return max_dt

    run_ts = _extract_run_timestamp(run_dir, pipeline_results)
    if pd.notna(run_ts):
        return run_ts

    if run_df is not None:
        for col in fallback_date_candidates:
            if col in run_df.columns:
                parsed = pd.to_datetime(run_df[col], errors="coerce")
                max_dt = parsed.max()
                if pd.notna(max_dt):
                    return max_dt

    return pd.NaT


def _load_run_kpis(run_dir: Path, pipeline_results: dict[str, Any]) -> dict[str, float]:
    kpi_file = run_dir / "kpis_output.json"
    payload = _load_json(kpi_file)
    if not payload:
        phases = pipeline_results.get("phases", {}) if isinstance(pipeline_results, dict) else {}
        calc = phases.get("calculation", {}) if isinstance(phases, dict) else {}
        payload = calc.get("kpis", {}) if isinstance(calc, dict) else {}
        payload = payload if isinstance(payload, dict) else {}

    normalized: dict[str, float] = {}
    for key, value in payload.items():
        if key is None:
            continue
        num = pd.to_numeric(value, errors="coerce")
        if pd.notna(num):
            normalized[str(key)] = float(num)
    return normalized


def _classify_run(
    run_dir: Path,
    pipeline_results: dict[str, Any],
    run_df: pd.DataFrame | None,
    kpis: dict[str, float],
) -> tuple[str, list[str]]:
    notes: list[str] = []
    inconsistent = False

    declared_run_id = pipeline_results.get("run_id")
    if isinstance(declared_run_id, str) and declared_run_id != run_dir.name:
        notes.append(f"pipeline_results.run_id={declared_run_id}")
        inconsistent = True

    phases = pipeline_results.get("phases", {}) if isinstance(pipeline_results, dict) else {}
    mismatched_phase_paths: list[str] = []
    if isinstance(phases, dict):
        for phase_name, phase_payload in phases.items():
            if isinstance(phase_payload, dict):
                for key, value in phase_payload.items():
                    if (
                        isinstance(value, str)
                        and "logs/runs/" in value
                        and run_dir.name not in value
                    ):
                        mismatched_phase_paths.append(f"{phase_name}.{key}")
    if mismatched_phase_paths:
        notes.append("mismatched phase paths: " + ", ".join(sorted(mismatched_phase_paths)))
        inconsistent = True

    if run_df is None:
        notes.append("missing/invalid clean_data.parquet or transformed.parquet")
        inconsistent = True

    if not (run_dir / "kpis_output.json").exists():
        notes.append("missing kpis_output.json")
        inconsistent = True

    if inconsistent:
        return "inconsistent", notes

    missing_fields: list[str] = []
    empty_fields: list[str] = []
    all_zero_fields: list[str] = []

    assert run_df is not None
    for field in REQUIRED_RUN_FIELDS:
        aliases = REQUIRED_FIELD_ALIASES.get(field, [field])
        series = _resolve_series_by_aliases(run_df, aliases)
        if series is None:
            missing_fields.append(field)
            continue

        text_non_empty = (
            (~series.isna()) & (series.astype(str).str.strip() != "") & (series.astype(str) != "nan")
        ).sum()
        if text_non_empty == 0:
            empty_fields.append(field)
            continue

        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() > 0 and (numeric.fillna(0) == 0).all():
            all_zero_fields.append(field)

    if missing_fields:
        notes.append("missing fields: " + ", ".join(missing_fields))
    if empty_fields:
        notes.append("empty fields: " + ", ".join(empty_fields))
    if all_zero_fields:
        notes.append("all-zero fields: " + ", ".join(all_zero_fields))

    missing_kpis = [k for k in REQUIRED_RUN_KPIS if k not in kpis]
    if missing_kpis:
        notes.append("missing KPIs: " + ", ".join(missing_kpis))

    present_required_values = [kpis.get(k) for k in REQUIRED_RUN_KPIS if k in kpis]
    if present_required_values and all(abs(float(v)) < 1e-12 for v in present_required_values):
        notes.append("all required KPIs are zero")

    if notes:
        return "partially_populated", notes
    return "fully_populated", []


def _field_non_empty_count(run_df: pd.DataFrame | None, canonical_field: str) -> int | None:
    if run_df is None:
        return None
    aliases = REQUIRED_FIELD_ALIASES.get(canonical_field, [canonical_field])
    series = _resolve_series_by_aliases(run_df, aliases)
    if series is None:
        return None
    return int(((~series.isna()) & (series.astype(str).str.strip() != "")).sum())


@st.cache_data(show_spinner=False)
def build_trends_frame(logs_dir: str) -> pd.DataFrame:
    base = Path(logs_dir)
    if not base.exists():
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for run_dir in sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name):
        pipeline_results = _load_json(run_dir / "pipeline_results.json")
        upload_meta = _load_upload_metadata(run_dir)
        run_df = _load_run_dataframe(run_dir)
        kpis = _load_run_kpis(run_dir, pipeline_results)
        integration_status, integration_notes = _classify_run(
            run_dir=run_dir,
            pipeline_results=pipeline_results,
            run_df=run_df,
            kpis=kpis,
        )
        run_timestamp = _extract_run_timestamp(run_dir, pipeline_results)
        as_of_date = _derive_as_of_date(run_dir, pipeline_results, run_df)
        row: dict[str, Any] = {
            "run_id": run_dir.name,
            "run_type": _run_type(run_dir.name),
            "run_timestamp": run_timestamp,
            "as_of_date": as_of_date,
            "source_file": upload_meta.get("source_file", ""),
            "integration_status": integration_status,
            "integration_notes": " | ".join(integration_notes),
        }
        row.update(kpis)
        rows.append(row)

    if not rows:
        return pd.DataFrame()

    trends = pd.DataFrame(rows)
    trends["run_timestamp"] = pd.to_datetime(trends["run_timestamp"], errors="coerce")
    trends["as_of_date"] = pd.to_datetime(trends["as_of_date"], errors="coerce")
    trends = trends.sort_values(["run_timestamp", "run_id"], na_position="last").reset_index(drop=True)
    trends["trend_point"] = trends.apply(
        lambda r: f"{r['as_of_date'].date() if pd.notna(r['as_of_date']) else 'n/a'} | {r['run_id']}",
        axis=1,
    )
    return trends


def render_trends_section(logs_dir: Path) -> None:
    st.markdown("---")
    st.header("📉 Historical Trends Across Runs")

    trends = build_trends_frame(str(logs_dir))
    if trends.empty:
        st.info("No run outputs found to build historical trends.")
        return

    status_counts = trends["integration_status"].value_counts(dropna=False).to_dict()
    summary_parts = [
        f"{k}: {v}" for k, v in [
            ("fully_populated", status_counts.get("fully_populated", 0)),
            ("partially_populated", status_counts.get("partially_populated", 0)),
            ("inconsistent", status_counts.get("inconsistent", 0)),
        ]
    ]
    st.caption("Run quality summary: " + " | ".join(summary_parts))

    control_col1, control_col2, control_col3 = st.columns([1, 1, 2])
    with control_col1:
        include_non_full = st.checkbox(
            "Include dry-run/validate runs",
            value=False,
            help="By default, only full runs are included in trend charts.",
        )
    with control_col2:
        include_partially = st.checkbox(
            "Include partially_populated runs",
            value=True,
            help="Disable to chart only fully_populated runs.",
        )
    with control_col3:
        include_inconsistent = st.checkbox(
            "Include inconsistent runs",
            value=False,
            help="Default excludes structurally inconsistent runs from trend charts.",
        )

    run_rows = trends[["run_id", "integration_status"]].drop_duplicates()
    run_label_map = {
        f"{row.run_id} [{row.integration_status}]": row.run_id
        for row in run_rows.itertuples(index=False)
    }
    selected_labels = st.multiselect(
            "Runs included in trends",
            options=list(run_label_map.keys()),
            default=list(run_label_map.keys()),
        )
    selected_runs = [run_label_map[label] for label in selected_labels]

    filtered = trends[trends["run_id"].isin(selected_runs)].copy()
    if not include_non_full:
        filtered = filtered[filtered["run_type"].isin(["full", "full_variant"])].copy()
    if not include_inconsistent:
        filtered = filtered[filtered["integration_status"] != "inconsistent"].copy()
    if not include_partially:
        filtered = filtered[filtered["integration_status"] == "fully_populated"].copy()

    if filtered.empty:
        st.warning("No runs left after filters. Adjust run selection/options.")
        return

    meta_cols = {
        "run_id",
        "run_type",
        "run_timestamp",
        "as_of_date",
        "source_file",
        "trend_point",
        "integration_status",
        "integration_notes",
    }
    preferred_kpis = [k for k in STANDARD_TREND_KPIS if k in filtered.columns]
    extra_kpis = sorted(
        [
            c
            for c in filtered.columns
            if c not in meta_cols
            and c not in preferred_kpis
            and pd.api.types.is_numeric_dtype(filtered[c])
        ]
    )
    available_kpis = [*preferred_kpis, *extra_kpis]
    default_kpis = [k for k in ["par_30", "par_60", "par_90", "npl_ratio"] if k in available_kpis]
    selected_kpis = st.multiselect(
        "Trend KPIs",
        options=available_kpis,
        default=default_kpis if default_kpis else available_kpis[:4],
    )

    if selected_kpis:
        chart_df = filtered[["trend_point", *selected_kpis]].set_index("trend_point")
        st.line_chart(chart_df)
    else:
        st.info("Select at least one KPI to render trend charts.")

    table_cols = [
        "as_of_date",
        "run_timestamp",
        "run_id",
        "source_file",
        "run_type",
        "integration_status",
        "integration_notes",
        *selected_kpis,
    ]
    table_cols = [c for c in table_cols if c in filtered.columns]
    st.subheader("🧾 Trend Dataset")
    st.dataframe(filtered[table_cols], width="stretch")

# Set page config
st.set_page_config(
    page_title="Abaco Loans Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Title
st.markdown(
    '<p class="main-header">📊 Abaco Loans Analytics Dashboard</p>',
    unsafe_allow_html=True,
)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("🎯 Navigation")

    page = st.radio(
        "Select Page",
        options=["📊 Dashboard", "📤 Upload Data", "📈 KPI Analysis", "⚙️ Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.header("📁 Data Source")

    # Pipeline run selection
    logs_dir = Path("logs/runs")
    if logs_dir.exists():
        run_dirs = sorted([d for d in logs_dir.iterdir() if d.is_dir()], reverse=True)

        if run_dirs:
            run_options = [d.name for d in run_dirs]
            selected_run = st.selectbox("Select Pipeline Run", options=run_options, index=0)
        else:
            st.warning("No pipeline runs found")
            selected_run = None
    else:
        st.warning("Logs directory not found. Please run the pipeline first.")
        selected_run = None

    st.markdown("---")

    st.header("⚙️ Options")
    auto_refresh = st.checkbox("Auto-refresh", value=False)
    show_technical = st.checkbox("Show technical details", value=False)

    st.markdown("---")

    st.header("📚 Documentation")
    st.markdown("""
    - [Quick Start](QUICK_START.md)
    - [Workflow Guide](UNIFIED_WORKFLOW.md)
    - [Documentation Index](DOCUMENTATION_INDEX.md)
    """)

# Main content
if page == "📤 Upload Data":
    # Import CSV upload component
    try:
        from streamlit_app.components.csv_upload import render_csv_upload

        render_csv_upload()
    except ImportError as e:
        st.error(f"Upload component not available: {e}")
        st.info("Please ensure the project is run from the root directory")

elif page == "📊 Dashboard" and selected_run:
    run_dir = Path("logs/runs") / selected_run

    # Load pipeline results
    results_file = run_dir / "pipeline_results.json"

    if results_file.exists():
        with open(results_file, "r") as f:
            results = json.load(f)

        # Status banner
        status = results.get("status", "unknown")
        if status == "success":
            st.success(f"✅ Pipeline Run: {selected_run} - Status: SUCCESS")
        elif status == "failed":
            st.error(f"❌ Pipeline Run: {selected_run} - Status: FAILED")
        else:
            st.warning(f"⚠️ Pipeline Run: {selected_run} - Status: {status.upper()}")

        # Key metrics
        st.header("📈 Key Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            duration = results.get("duration_seconds", 0)
            st.metric("Execution Time", f"{duration:.2f}s")

        with col2:
            phases = results.get("phases", {})
            successful_phases = sum(1 for p in phases.values() if p.get("status") == "success")
            st.metric("Successful Phases", f"{successful_phases}/{len(phases)}")

        with col3:
            ingestion = phases.get("ingestion", {})
            row_count = ingestion.get("row_count", 0)
            st.metric("Rows Processed", f"{row_count:,}")

        with col4:
            calculation = phases.get("calculation", {})
            kpi_count = calculation.get("kpi_count", 0)
            st.metric("KPIs Calculated", kpi_count)

        run_df = _load_run_dataframe(run_dir)
        upload_meta = _load_upload_metadata(run_dir)
        st.subheader("🧾 Source Data Integration")
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        with meta_col1:
            st.metric("Source File", upload_meta.get("source_file", "pipeline/default"))
        with meta_col2:
            st.metric(
                "Detected As-of",
                upload_meta.get("detected_as_of_date", "from run metadata"),
            )
        with meta_col3:
            company_non_empty = _field_non_empty_count(run_df, "company")
            if company_non_empty is None:
                st.metric("Company Rows", "missing")
            else:
                st.metric("Company Rows", f"{company_non_empty:,}")

        control_fields = ["company", "credit_line", "kam_hunter", "kam_farmer"]
        readiness = {
            field: _field_non_empty_count(run_df, field) for field in control_fields
        }
        readiness_parts = [
            f"{field}={count if count is not None else 'missing'}"
            for field, count in readiness.items()
        ]
        st.caption("Control de Mora mapped fields: " + " | ".join(readiness_parts))

        st.markdown("---")

        # Phase Results
        st.header("🔄 Pipeline Phases")

        phase_names = {
            "ingestion": "1️⃣ Ingestion",
            "transformation": "2️⃣ Transformation",
            "calculation": "3️⃣ Calculation",
            "output": "4️⃣ Output",
        }

        cols = st.columns(4)

        for idx, (phase_key, phase_title) in enumerate(phase_names.items()):
            with cols[idx]:
                phase_data = phases.get(phase_key, {})
                phase_status = phase_data.get("status", "unknown")

                if phase_status == "success":
                    st.success(f"✅ {phase_title}")
                elif phase_status == "failed":
                    st.error(f"❌ {phase_title}")
                else:
                    st.info(f"⚠️ {phase_title}")

                if show_technical and phase_data:
                    with st.expander("Details"):
                        st.json(phase_data)

        st.markdown("---")

        # KPI Results
        st.header("💰 KPI Results")

        kpis = _load_run_kpis(run_dir, results)

        st.subheader("🛰 Backend Portfolio Analysis (API)")

        portfolio_request = results.get("portfolio")

        if portfolio_request:
            api_client = AbacoAnalyticsApiClient()
            col_api1, col_api2 = st.columns(2)
            with col_api1:
                if st.button("Run Full Analysis via API"):
                    with st.spinner("Calling Abaco Analytics API..."):
                        try:
                            full_analysis = api_client.run_full_analysis(portfolio_request)
                            st.success("Full analysis completed via API.")
                            st.json(full_analysis)
                        except Exception as exc:
                            st.error(f"API call failed: {exc}")
            with col_api2:
                if st.button("Check Drilldown Status via API"):
                    with st.spinner("Fetching drilldown statuses..."):
                        try:
                            statuses = api_client.get_drilldown_statuses()
                            st.json(statuses)
                        except Exception as exc:
                            st.error(f"Status fetch failed: {exc}")
        else:
            st.info("No portfolio payload found in results to send to the API.")

        if kpis:
            kpi_df = pd.DataFrame([kpis]).reindex(sorted(kpis.keys()), axis=1)

            with st.expander("🤖 AI Portfolio Insights", expanded=False):
                st.markdown("Get strategic, AI-generated insights on this run's KPIs.")

                ai_context = st.text_area(
                    "Optional context (e.g., target market, constraints, current strategy)",
                    value=(
                        "Retail loans portfolio, focus on risk-adjusted growth and "
                        "NPL reduction."
                    ),
                )

                if st.button("Generate AI Insights for this run"):
                    with st.spinner("Generating AI insights..."):
                        try:
                            from ai_insights import generate_kpi_insights

                            insights = generate_kpi_insights(kpis=kpis, context=ai_context)
                            st.markdown("### Strategic Insights")
                            st.markdown(insights)
                        except Exception as exc:
                            st.error(f"AI insights generation failed: {exc}")
                            st.info("Check OPENAI_API_KEY and network connectivity.")

            # Display as metrics
            kpi_cols = st.columns(min(3, len(kpis)))

            for idx, (kpi_name, kpi_value) in enumerate(sorted(kpis.items())):
                with kpi_cols[idx % 3]:
                    # Format value based on type
                    if isinstance(kpi_value, (int, float)):
                        if "amount" in kpi_name.lower() or "balance" in kpi_name.lower():
                            formatted_value = f"${kpi_value:,.2f}"
                        elif "count" in kpi_name.lower():
                            formatted_value = f"{int(kpi_value):,}"
                        else:
                            formatted_value = f"{kpi_value:,.2f}"
                    else:
                        formatted_value = str(kpi_value)

                    st.metric(kpi_name.replace("_", " ").title(), formatted_value)

            # Display as table
            st.subheader("📋 Full KPI Table")
            st.dataframe(kpi_df.T, width="stretch")

            # Download button
            csv = kpi_df.to_csv(index=False)
            st.download_button(
                label="Download KPI Results (CSV)",
                data=csv,
                file_name=f"kpi_results_{selected_run}.csv",
                mime="text/csv",
            )
        else:
            st.info("No KPI results available for this run")

        render_trends_section(logs_dir)

        st.markdown("---")

        # Technical Details
        if show_technical:
            st.header("🔧 Technical Details")

            tab1, tab2, tab3 = st.tabs(["Full Results", "Configuration", "Logs"])

            with tab1:
                st.json(results)

            with tab2:
                config_file = Path("config/pipeline.yml")
                if config_file.exists():
                    with open(config_file, "r") as f:
                        st.code(f.read(), language="yaml")
                else:
                    st.warning("Configuration file not found")

            with tab3:
                log_files = list(run_dir.glob("*.log"))
                if log_files:
                    selected_log = st.selectbox("Select log file", [f.name for f in log_files])
                    log_file = run_dir / selected_log
                    with open(log_file, "r") as f:
                        st.code(f.read(), language="log")
                else:
                    st.info("No log files found")

    else:
        st.warning(f"Results file not found for run: {selected_run}")
        st.info("The pipeline may still be running or the run directory is incomplete")

else:
    # Welcome screen
    st.info("👋 Welcome to Abaco Loans Analytics!")
    st.markdown("""
    ### Getting Started

    1. **Run the pipeline** to generate data:
       ```bash
       python scripts/data/run_data_pipeline.py --input data/raw/loans.csv
       ```

    2. **Select a pipeline run** from the sidebar to view results

    3. **Explore KPIs** and visualizations

    ### Quick Links

    - 📖 [Quick Start Guide](QUICK_START.md)
    - 🔄 [Unified Workflow](UNIFIED_WORKFLOW.md)
    - 📊 [Workflow Diagrams](WORKFLOW_DIAGRAMS.md)
    - 📋 [Documentation Index](DOCUMENTATION_INDEX.md)

    ### Pipeline Architecture

    The unified pipeline consists of 4 phases:

    1. **Ingestion** - Data collection and validation
    2. **Transformation** - Data cleaning and normalization
    3. **Calculation** - KPI computation
    4. **Output** - Results distribution

    Results are stored in `logs/runs/<timestamp>/` for easy access.
    """)

# Footer
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>Abaco Loans Analytics Platform v2.0 | Unified Pipeline Architecture</p>
    <p>For support, see <a href='DOCUMENTATION_INDEX.md'>Documentation Index</a></p>
</div>
""",
    unsafe_allow_html=True,
)
