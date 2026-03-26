"""Risk Intelligence — Expected Loss, Roll Rates, Vintage Analysis, Concentration HHI.

Institutional-grade risk analytics page that reads pipeline output artifacts
and presents deep credit-risk intelligence with interactive visualizations.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOGS_DIR = ROOT_DIR / "logs" / "runs"

st.set_page_config(page_title="Risk Intelligence", page_icon="🛡️", layout="wide")


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


# ──────────────────────────────────────────────────────────────────────
# Rendering Functions
# ──────────────────────────────────────────────────────────────────────

def _render_expected_loss(el_data: Dict[str, Any]) -> None:
    """Render Expected Loss analysis section."""
    st.subheader("Expected Loss (EL = PD × LGD × EAD)")
    st.caption("Basel-aligned expected credit loss calculation across the portfolio")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total Expected Loss",
            f"${el_data.get('total_expected_loss_usd', 0):,.2f}",
        )
    with col2:
        st.metric(
            "EL Rate",
            f"{el_data.get('expected_loss_rate_pct', 0):.4f}%",
        )
    with col3:
        st.metric(
            "Weighted Avg PD",
            f"{el_data.get('weighted_avg_pd_pct', 0):.4f}%",
        )
    with col4:
        st.metric(
            "LGD Assumed",
            f"{el_data.get('lgd_assumed_pct', 10):.1f}%",
        )

    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"**Total EAD:** ${el_data.get('total_ead_usd', 0):,.2f}")
    with col_b:
        st.info(f"**Loans Analyzed:** {el_data.get('loan_count', 0):,}")

    el_rate = el_data.get("expected_loss_rate_pct", 0)
    if el_rate > 5:
        st.error("⚠️ EL Rate exceeds 5% — critical portfolio stress level")
    elif el_rate > 3:
        st.warning("⚡ EL Rate above 3% — elevated risk, review underwriting")
    else:
        st.success("✅ EL Rate within acceptable range")


def _render_roll_rates(rr_data: Dict[str, Any]) -> None:
    """Render Roll Rate / DPD bucket migration analysis."""
    st.subheader("Roll Rate Analysis (DPD Bucket Transitions)")
    st.caption("Balance-weighted migration across delinquency buckets")

    bucket_dist = rr_data.get("bucket_distribution", {})
    if bucket_dist:
        cols = st.columns(len(bucket_dist))
        for i, (bucket, info) in enumerate(bucket_dist.items()):
            with cols[i]:
                st.metric(
                    bucket.upper(),
                    f"${info.get('balance_usd', 0):,.0f}",
                    f"{info.get('pct_of_portfolio', 0):.2f}%",
                )

    roll_matrix = rr_data.get("roll_rate_matrix", {})
    if roll_matrix:
        st.markdown("#### Migration Matrix")
        rows = []
        for transition, info in roll_matrix.items():
            rows.append({
                "Transition": transition.replace("_to_", " → "),
                "From Balance": f"${info.get('from_balance', 0):,.2f}",
                "To Balance": f"${info.get('to_balance', 0):,.2f}",
                "Roll Rate": f"{info.get('roll_rate_pct', 0):.2f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Chart
        chart_data = pd.DataFrame([
            {"Transition": k.replace("_to_", " → "), "Roll Rate %": v.get("roll_rate_pct", 0)}
            for k, v in roll_matrix.items()
        ])
        st.bar_chart(chart_data.set_index("Transition"), y="Roll Rate %")


def _render_vintage_analysis(vintage_data: Dict[str, Any]) -> None:
    """Render Vintage / Cohort Analysis."""
    st.subheader("Vintage Analysis (Origination Cohort)")
    st.caption("Portfolio quality tracking by origination month — identifies underwriting trends")

    vintages = vintage_data.get("vintages", {})
    if not vintages:
        st.info("No vintage data available")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Vintages", vintage_data.get("total_vintages", 0))
    with col2:
        worst = vintage_data.get("worst_vintage", "N/A")
        st.metric("Worst Vintage", worst, help="Highest default rate cohort")
    with col3:
        best = vintage_data.get("best_vintage", "N/A")
        st.metric("Best Vintage", best, help="Lowest default rate cohort")

    rows = []
    for vintage, info in sorted(vintages.items()):
        rows.append({
            "Cohort": vintage,
            "Loans": info.get("loan_count", 0),
            "Balance ($)": f"{info.get('total_balance_usd', 0):,.2f}",
            "Avg DPD": f"{info.get('avg_dpd', 0):.1f}",
            "PAR 30 %": f"{info.get('par_30_rate', 0):.2f}",
            "PAR 90 %": f"{info.get('par_90_rate', 0):.2f}",
            "Default %": f"{info.get('default_rate', 0):.2f}",
            "Defaults": info.get("default_count", 0),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Vintage curve chart
    chart_df = pd.DataFrame([
        {
            "Cohort": v,
            "PAR 30": info.get("par_30_rate", 0),
            "Default Rate": info.get("default_rate", 0),
        }
        for v, info in sorted(vintages.items())
    ]).set_index("Cohort")
    st.line_chart(chart_df)


def _render_concentration_hhi(hhi_data: Dict[str, Any]) -> None:
    """Render Concentration / HHI analysis."""
    st.subheader("Concentration Analysis (Herfindahl-Hirschman Index)")
    st.caption("Portfolio concentration risk — obligor-level exposure analysis")

    col1, col2, col3 = st.columns(3)
    with col1:
        hhi = hhi_data.get("hhi_index", 0)
        level = hhi_data.get("concentration_level", "unknown")
        st.metric("HHI Index", f"{hhi:,.0f}", help=f"Level: {level}")
    with col2:
        st.metric("Total Obligors", f"{hhi_data.get('total_obligors', 0):,}")
    with col3:
        st.metric(
            "Portfolio Total",
            f"${hhi_data.get('total_portfolio_usd', 0):,.2f}",
        )

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("Top-1 Obligor", f"{hhi_data.get('top_1_obligor_pct', 0):.2f}%")
    with col_b:
        st.metric("Top-5 Obligors", f"{hhi_data.get('top_5_obligor_pct', 0):.2f}%")
    with col_c:
        st.metric("Top-10 Obligors", f"{hhi_data.get('top_10_obligor_pct', 0):.2f}%")
    with col_d:
        st.metric("Top-20 Obligors", f"{hhi_data.get('top_20_obligor_pct', 0):.2f}%")

    # Concentration level indicator
    level = hhi_data.get("concentration_level", "unknown")
    if level == "very_high":
        st.error("🔴 VERY HIGH concentration — immediate diversification required")
    elif level == "high":
        st.warning("🟠 HIGH concentration — review obligor limits")
    elif level == "moderate":
        st.info("🟡 MODERATE concentration — monitor top exposures")
    else:
        st.success("🟢 LOW concentration — well diversified portfolio")

    # HHI scale reference
    st.markdown("""
    **HHI Scale Reference:** <1,000 = Low | 1,000–1,800 = Moderate | 1,800–2,500 = High | >2,500 = Very High
    """)


# ──────────────────────────────────────────────────────────────────────
# Main Page
# ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.title("🛡️ Risk Intelligence")
    st.markdown(
        "Institutional-grade credit risk analytics: Expected Loss, "
        "Roll Rates, Vintage Curves, and Concentration Analysis."
    )

    run_dir = _find_latest_run_dir()
    if run_dir is None:
        st.warning("No pipeline runs found. Run the pipeline first to generate risk analytics.")
        return

    st.sidebar.success(f"**Latest Run:** `{run_dir.name}`")

    # Load all risk artifacts
    el_data = _load_json_artifact(run_dir, "expected_loss.json")
    rr_data = _load_json_artifact(run_dir, "roll_rates.json")
    vintage_data = _load_json_artifact(run_dir, "vintage_analysis.json")
    hhi_data = _load_json_artifact(run_dir, "concentration_hhi.json")

    available = sum(1 for d in [el_data, rr_data, vintage_data, hhi_data] if d)
    if available == 0:
        st.warning(
            "No risk intelligence artifacts found in latest run. "
            "Re-run the pipeline to generate EL, roll rates, vintage, and HHI data."
        )
        return

    st.sidebar.info(f"**Risk Modules Loaded:** {available}/4")

    # Tabs for each risk module
    tabs = st.tabs([
        "📊 Expected Loss",
        "🔄 Roll Rates",
        "📈 Vintage Curves",
        "🎯 Concentration HHI",
    ])

    with tabs[0]:
        if el_data:
            _render_expected_loss(el_data)
        else:
            st.info("Expected Loss data not available — run pipeline to generate")

    with tabs[1]:
        if rr_data:
            _render_roll_rates(rr_data)
        else:
            st.info("Roll Rate data not available — run pipeline to generate")

    with tabs[2]:
        if vintage_data:
            _render_vintage_analysis(vintage_data)
        else:
            st.info("Vintage analysis not available — run pipeline to generate")

    with tabs[3]:
        if hhi_data:
            _render_concentration_hhi(hhi_data)
        else:
            st.info("Concentration HHI not available — run pipeline to generate")

    # Raw data expander
    with st.expander("📋 Raw Risk Data (JSON)"):
        for label, data in [
            ("Expected Loss", el_data),
            ("Roll Rates", rr_data),
            ("Vintage Analysis", vintage_data),
            ("Concentration HHI", hhi_data),
        ]:
            if data:
                st.markdown(f"**{label}:**")
                st.json(data)


if __name__ == "__main__":
    main()
else:
    main()
