#!/usr/bin/env python3
"""
ABACO LOANS ANALYTICS - Interactive Dashboard

Main Streamlit application for visualizing pipeline results and KPIs.
Serves as the frontend for the unified analytics platform.

Run with:
    streamlit run streamlit_app.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from api_client import AbacoAnalyticsApiClient
from python.logging_config import init_sentry

init_sentry(service_name="streamlit_app")

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

        kpis = calculation.get("kpis", {})

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
            kpi_df = pd.DataFrame([kpis])

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

            for idx, (kpi_name, kpi_value) in enumerate(kpis.items()):
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
            st.dataframe(kpi_df.T, use_container_width=True)

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
       python scripts/run_data_pipeline.py --input data/raw/loans.csv
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
