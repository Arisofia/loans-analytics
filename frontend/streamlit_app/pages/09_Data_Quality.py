"""Data Quality — Rule Results, Anomaly Detection, Blocking Policy.

Data quality dashboard showing validation results, detected anomalies,
and blocking rule enforcement from the DQ engine.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOGS_DIR = ROOT_DIR / "logs" / "runs"
CONFIG_DIR = ROOT_DIR / "config"

st.set_page_config(page_title="Data Quality", page_icon="✅", layout="wide")


# ──────────────────────────────────────────────────────────────────────
# Data Loading
# ──────────────────────────────────────────────────────────────────────

def _find_latest_run_dir() -> Optional[Path]:
    """Find the most recent pipeline run directory."""
    if not LOGS_DIR.exists():
        return None
    runs = sorted(
        [d for d in LOGS_DIR.iterdir() if d.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return runs[0] if runs else None


def _load_json_artifact(run_dir: Path, filename: str) -> Optional[Dict[str, Any]]:
    """Load a JSON artifact from a pipeline run directory."""
    path = run_dir / filename
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_business_parameters() -> Dict[str, Any]:
    """Load business parameters from config."""
    import yaml

    params_path = CONFIG_DIR / "business_parameters.yml"
    if not params_path.exists():
        return {}
    with open(params_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ──────────────────────────────────────────────────────────────────────
# Rendering Functions
# ──────────────────────────────────────────────────────────────────────

def _render_unit_economics(kpi_data: Dict[str, Any], el_data: Optional[Dict[str, Any]]) -> None:
    """Render unit economics tab."""
    st.subheader("Unit Economics")
    st.caption("Core financial metrics derived from portfolio data")

    col1, col2, col3, col4 = st.columns(4)

    npl = kpi_data.get("npl_ratio", kpi_data.get("NPL_RATIO", 0))
    if isinstance(npl, dict):
        npl = npl.get("value", 0)
    with col1:
        st.metric("NPL Ratio", f"{float(npl or 0):.2f}%")

    cost_of_risk = 0.0
    if el_data:
        cost_of_risk = el_data.get("expected_loss_rate_pct", 0)
    with col2:
        st.metric("Cost of Risk", f"{cost_of_risk:.4f}%")

    collection_rate = kpi_data.get("collection_rate", kpi_data.get("COLLECTION_RATE", 0))
    if isinstance(collection_rate, dict):
        collection_rate = collection_rate.get("value", 0)
    with col3:
        st.metric("Collection Rate", f"{float(collection_rate or 0):.2f}%")

    default_rate = kpi_data.get("default_rate", 0)
    with col4:
        st.metric("Default Rate", f"{float(default_rate or 0):.2f}%")

    st.divider()

    # Derived risk metrics
    st.markdown("#### Derived Risk Metrics")
    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        npl_90 = kpi_data.get("npl_90_ratio", 0)
        st.metric("NPL 90+ Ratio", f"{float(npl_90 or 0):.4f}%")
    with col_b:
        def_out = kpi_data.get("defaulted_outstanding_ratio", 0)
        st.metric("Defaulted Outstanding %", f"{float(def_out or 0):.4f}%")
    with col_c:
        top10 = kpi_data.get("top_10_borrower_concentration", 0)
        st.metric("Top-10 Concentration", f"{float(top10 or 0):.2f}%")
    with col_d:
        ltv_mean = kpi_data.get("ltv_sintetico_mean", 0)
        st.metric("LTV Sintético (Avg)", f"{float(ltv_mean or 0):.4f}")


def _render_financial_indicators(params: Dict[str, Any]) -> None:
    """Render holding financial indicators and guardrails."""
    st.subheader("Financial Guardrails & Targets")
    st.caption("From business_parameters.yml — institutional governance thresholds")

    financial = params.get("financial_guardrails", {})
    risk = params.get("risk", {})
    sla = params.get("sla", {})
    liquidity = params.get("liquidity", {})

    if financial:
        st.markdown("#### Financial Guardrails")
        cols = st.columns(4)
        guardrail_items = list(financial.items())
        for i, (key, value) in enumerate(guardrail_items):
            with cols[i % 4]:
                label = key.replace("_", " ").title()
                if isinstance(value, (int, float)):
                    if "pct" in key or "rate" in key or "max" in key or "min" in key:
                        st.metric(label, f"{value}%")
                    else:
                        st.metric(label, f"{value}")
                elif isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        st.metric(f"{label} ({sub_key})", f"{sub_val}")
                else:
                    st.metric(label, str(value))

    if risk:
        st.markdown("#### Risk Parameters")
        cols = st.columns(4)
        for i, (key, value) in enumerate(risk.items()):
            with cols[i % 4]:
                label = key.replace("_", " ").title()
                st.metric(label, f"{value}")

    if liquidity:
        st.markdown("#### Liquidity Requirements")
        cols = st.columns(3)
        for i, (key, value) in enumerate(liquidity.items()):
            with cols[i % 3]:
                label = key.replace("_", " ").title()
                if isinstance(value, (int, float)):
                    st.metric(label, f"{value}")
                else:
                    st.metric(label, str(value))

    if sla:
        st.markdown("#### SLA Targets")
        cols = st.columns(4)
        for i, (key, value) in enumerate(sla.items()):
            with cols[i % 4]:
                label = key.replace("_", " ").title()
                st.metric(label, str(value))


def _render_portfolio_targets(params: Dict[str, Any]) -> None:
    """Render 2026 portfolio targets with progress tracking."""
    st.subheader("2026 Portfolio Targets")
    st.caption("Monthly AUM targets from business_parameters.yml")

    targets_2026 = params.get("targets_2026", {})
    portfolio_targets = targets_2026.get("portfolio_aum_monthly", {})

    if not portfolio_targets:
        st.info("No 2026 targets configured")
        return

    rows = []
    for month, target in sorted(portfolio_targets.items()):
        if isinstance(target, (int, float)):
            rows.append({"Month": str(month), "Target AUM ($)": target})

    if rows:
        df = pd.DataFrame(rows)
        st.bar_chart(df.set_index("Month"), y="Target AUM ($)")
        st.dataframe(df, use_container_width=True, hide_index=True)


def _render_kpi_deep_dive(kpi_data: Dict[str, Any]) -> None:
    """Full KPI catalog with all computed metrics."""
    st.subheader("Full KPI Catalog")
    st.caption("All metrics computed in the latest pipeline run")

    if not kpi_data:
        st.info("No KPI data available")
        return

    # Categorize KPIs
    categories: Dict[str, List] = {
        "Asset Quality": [],
        "Portfolio": [],
        "Collections": [],
        "Growth": [],
        "Risk": [],
        "Other": [],
    }

    risk_kpis = {
        "par_30", "par_60", "par_90", "npl_ratio", "npl_90_ratio",
        "default_rate", "loss_rate", "defaulted_outstanding_ratio",
        "top_10_borrower_concentration", "ltv_sintetico_mean",
        "ltv_sintetico_high_risk_pct", "velocity_of_default",
    }
    portfolio_kpis = {
        "total_outstanding", "disbursement_volume",
        "average_loan_size", "total_loans_count", "active_borrowers",
    }
    collections_kpis = {
        "collection_rate", "capital_collection_rate",
        "collections_eligible_rate",
    }
    growth_kpis = {
        "repeat_borrower_rate", "disbursement_growth_rate_mom",
    }

    for kpi_name, value in sorted(kpi_data.items()):
        if isinstance(value, dict):
            display_val = value.get("value", value)
        else:
            display_val = value

        entry = {"KPI": kpi_name, "Value": display_val}

        if kpi_name.lower() in risk_kpis or "par" in kpi_name.lower():
            categories["Asset Quality"].append(entry)
        elif kpi_name.lower() in portfolio_kpis:
            categories["Portfolio"].append(entry)
        elif kpi_name.lower() in collections_kpis:
            categories["Collections"].append(entry)
        elif kpi_name.lower() in growth_kpis:
            categories["Growth"].append(entry)
        else:
            categories["Other"].append(entry)

    for category, entries in categories.items():
        if entries:
            st.markdown(f"#### {category}")
            df = pd.DataFrame(entries)
            st.dataframe(df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────
# Main Page
# ──────────────────────────────────────────────────────────────────────

def _render_data_freshness(run_dir: Optional[Path]) -> None:
    """Render data freshness and pipeline provenance information."""
    st.subheader("Data Freshness")
    st.caption("When was the data last extracted and from which source?")

    if run_dir is None:
        st.info("No pipeline runs found. Run the pipeline to see data freshness information.")
        return

    pipeline_results = _load_json_artifact(run_dir, "pipeline_results.json")

    if not pipeline_results:
        st.warning("No pipeline_results.json found for the latest run.")
        return

    ingestion_phase = pipeline_results.get("phases", {}).get("ingestion", {})
    start_time = pipeline_results.get("start_time")
    end_time = pipeline_results.get("end_time")
    ingestion_source = ingestion_phase.get("ingestion_source", "unknown")
    ingestion_ts = ingestion_phase.get("timestamp") or start_time
    data_as_of = ingestion_phase.get("data_as_of_date")
    data_as_of_col = ingestion_phase.get("data_as_of_column")
    row_count = ingestion_phase.get("row_count")
    col_count = ingestion_phase.get("column_count")

    source_label = (
        "Google Sheets" if ingestion_source == "google_sheets"
        else "CSV / File" if ingestion_source == "file"
        else ingestion_source.replace("_", " ").title()
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Data Source", source_label)
    with col2:
        if ingestion_ts:
            try:
                ts_fmt = datetime.fromisoformat(ingestion_ts).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                ts_fmt = ingestion_ts
            st.metric("Last Extracted At", ts_fmt)
        else:
            st.metric("Last Extracted At", "N/A")
    with col3:
        st.metric("Data As-Of Date", data_as_of or "N/A")
    with col4:
        if data_as_of:
            try:
                as_of_dt = datetime.fromisoformat(data_as_of)
                now = datetime.now()
                days_stale = (now - as_of_dt).days
                staleness_label = (
                    "🟢 Current" if days_stale <= 1
                    else f"🟡 {days_stale}d old" if days_stale <= 7
                    else f"🔴 {days_stale}d old"
                )
                st.metric("Staleness", staleness_label)
            except ValueError:
                st.metric("Staleness", "N/A")
        else:
            st.metric("Staleness", "N/A")

    st.divider()
    st.markdown("#### Pipeline Run Details")
    detail_cols = st.columns(2)
    with detail_cols[0]:
        if start_time:
            try:
                st.write(f"**Run Started:** {datetime.fromisoformat(start_time).strftime('%Y-%m-%d %H:%M:%S')}")
            except ValueError:
                st.write(f"**Run Started:** {start_time}")
        if end_time:
            try:
                st.write(f"**Run Ended:** {datetime.fromisoformat(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
            except ValueError:
                st.write(f"**Run Ended:** {end_time}")
        duration = pipeline_results.get("duration_seconds")
        if duration is not None:
            st.write(f"**Duration:** {duration:.1f}s")
    with detail_cols[1]:
        if row_count is not None:
            st.write(f"**Rows Ingested:** {row_count:,}")
        if col_count is not None:
            st.write(f"**Columns:** {col_count}")
        if data_as_of_col:
            st.write(f"**As-Of Column:** `{data_as_of_col}`")
        run_id = pipeline_results.get("run_id")
        if run_id:
            st.write(f"**Run ID:** `{run_id}`")

    status = pipeline_results.get("status", "unknown")
    if status == "success":
        st.success(f"✅ Pipeline status: **{status}**")
    elif status in ("partial",):
        st.warning(f"⚠️ Pipeline status: **{status}**")
    else:
        st.error(f"❌ Pipeline status: **{status}**")



    st.title("💰 Capital & Economics")
    st.markdown(
        "Unit economics, financial indicators, profitability analysis, "
        "and portfolio targets — institutional-grade financial intelligence."
    )

    run_dir = _find_latest_run_dir()
    params = _load_business_parameters()

    kpi_data: Dict[str, Any] = {}
    el_data: Optional[Dict[str, Any]] = None

    if run_dir:
        st.sidebar.success(f"**Latest Run:** `{run_dir.name}`")
        kpi_data = _load_json_artifact(run_dir, "kpis.json") or {}
        el_data = _load_json_artifact(run_dir, "expected_loss.json")
    else:
        st.sidebar.warning("No pipeline runs found")

    tabs = st.tabs([
        "🗓️ Data Freshness",
        "📊 Unit Economics",
        "🏛️ Financial Guardrails",
        "🎯 2026 Targets",
        "📋 Full KPI Catalog",
    ])

    with tabs[0]:
        _render_data_freshness(run_dir)

    with tabs[1]:
        if kpi_data:
            _render_unit_economics(kpi_data, el_data)
        else:
            st.info("Run the pipeline to generate unit economics data")

    with tabs[2]:
        if params:
            _render_financial_indicators(params)
        else:
            st.info("No business parameters found at config/business_parameters.yml")

    with tabs[3]:
        if params:
            _render_portfolio_targets(params)
        else:
            st.info("No 2026 targets configured")

    with tabs[4]:
        _render_kpi_deep_dive(kpi_data)


if __name__ == "__main__":
    main()
else:
    main()
