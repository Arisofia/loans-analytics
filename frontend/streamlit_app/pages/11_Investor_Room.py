"""11 — Investor Room.

Consolidated financial intelligence page for investors and board.
Wires the holding financial indicators module, covenant engine,
scenario projections, and vintage analysis from the decision state.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Investor Room", page_icon="🏦", layout="wide")

import logging
from typing import Any, Dict

from frontend.streamlit_app.decision_loader import (
    load_decision_state,
    load_scenario_results,
)

logger = logging.getLogger(__name__)


def _safe_import_holding():
    """Lazily import the holding indicators module."""
    try:
        from backend.loans_analytics.kpis.holding_financial_indicators import (
            calculate_liquidity_reserve,
            compare_scenarios,
            load_holding_config,
            reconcile_default_rates,
            verify_debt_covenants,
        )
        return {
            "config": load_holding_config,
            "liquidity": calculate_liquidity_reserve,
            "covenants": verify_debt_covenants,
            "reconcile": reconcile_default_rates,
            "scenarios": compare_scenarios,
        }
    except Exception as exc:
        logger.warning("Holding indicators unavailable: %s", exc)
        return None


def _render_covenant_section(state: Dict[str, Any]) -> None:
    """Render covenant status from decision state alerts."""
    all_alerts = state.get("critical_alerts", []) + state.get("ranked_alerts", [])
    covenant_alerts = [
        a for a in all_alerts
        if (a.get("alert_id") or "").startswith("covenant.")
    ]

    if covenant_alerts:
        st.error(f"⚠️ {len(covenant_alerts)} covenant breach(es)")
        for ca in covenant_alerts:
            sev = ca.get("severity", "warning")
            icon = {"critical": "🔴", "warning": "🟡"}.get(sev, "⚪")
            st.markdown(f"{icon} **{ca.get('title', 'Breach')}**")
            if ca.get("description"):
                st.caption(ca["description"])
            val = ca.get("current_value")
            thr = ca.get("threshold")
            if val is not None and thr is not None:
                st.caption(f"Current: `{val}` · Limit: `{thr}`")
    else:
        covenant_status = state.get("agent_statuses", {}).get("covenant", "not_run")
        if covenant_status == "ok":
            st.success("✅ All covenants within thresholds.")
        else:
            st.info("Covenant agent has not run yet.")


def _render_holding_indicators(holding: dict) -> None:
    """Render the holding financial indicators from config/module."""
    cfg_loader = holding["config"]
    try:
        cfg = cfg_loader()
    except Exception as exc:
        st.warning(f"Could not load holding config: {exc}")
        return

    # ── Debt Covenants ──────────────────────────────────────────────
    st.markdown("#### Debt Covenant Verification")
    cov_cfg = cfg.get("debt_covenants", {})
    try:
        cov_result = holding["covenants"](
            collection_rate=cov_cfg.get("min_collection_rate", 0.985),
            delinquency_growth=-0.01,
            repline_30d=cov_cfg.get("repline_distribution", {}).get("bucket_30_days_max_pct", 0.45),
            repline_60d=cov_cfg.get("repline_distribution", {}).get("bucket_60_days_max_pct", 0.35),
            repline_90d=cov_cfg.get("repline_distribution", {}).get("bucket_90_days_max_pct", 0.20),
        )
        status = cov_result.get("overall_status", "unknown")
        if status == "pass":
            st.success(f"Covenant status: **{status.upper()}**")
        else:
            st.error(f"Covenant status: **{status.upper()}**")

        checks = cov_result.get("checks", [])
        if checks:
            for check in checks:
                name = check.get("covenant", check.get("name", ""))
                passed = check.get("status", "fail") == "pass"
                icon = "✅" if passed else "❌"
                st.caption(f"{icon} {name}: {check.get('status', 'unknown')}")
    except Exception as exc:
        st.caption(f"Could not verify covenants: {exc}")

    # ── Default Rate Reconciliation ─────────────────────────────────
    st.markdown("#### Default Rate Reconciliation")
    try:
        recon = holding["reconcile"]()
        cols = st.columns(3)
        with cols[0]:
            st.metric("UNIT-EC Default Rate", f"{recon.get('unit_ec_default_rate_pct', 0):.2f}%")
        with cols[1]:
            st.metric("ER-CONS Monthly Rate", f"{recon.get('er_cons_monthly_rate_pct', 0):.4f}%")
        with cols[2]:
            reconciled = recon.get("reconciled", False)
            st.metric("Reconciled", "✅ Yes" if reconciled else "❌ No")
        if recon.get("explanation"):
            st.caption(recon["explanation"])
    except Exception as exc:
        st.caption(f"Could not reconcile: {exc}")

    # ── Liquidity Reserve ───────────────────────────────────────────
    st.markdown("#### Liquidity Reserve Model")
    try:
        liquidity = holding["liquidity"](
            total_portfolio=1_000_000,
            cash_available=80_000,
            min_reserve_pct=0.05,
        )
        cols = st.columns(3)
        with cols[0]:
            st.metric("Reserve Ratio", f"{liquidity.get('reserve_ratio_pct', 0):.2f}%")
        with cols[1]:
            st.metric("Required Reserve", f"${liquidity.get('required_reserve', 0):,.0f}")
        with cols[2]:
            adequate = liquidity.get("is_adequate", False)
            st.metric("Status", "✅ Adequate" if adequate else "❌ Shortfall")
    except Exception as exc:
        st.caption(f"Could not compute liquidity: {exc}")


def _render_scenarios(scenarios: list | None) -> None:
    """Render scenario engine results."""
    if not scenarios:
        st.info("No scenario projections available. Run the pipeline first.")
        return

    for sc in scenarios:
        scenario_name = sc.get("scenario", sc.get("name", "Unknown"))
        with st.expander(f"📊 {scenario_name}", expanded=False):
            triggers = sc.get("triggers", [])
            if triggers:
                st.caption(f"Triggers: {', '.join(str(t) for t in triggers)}")
            horizon = sc.get("horizon_months")
            if horizon:
                st.caption(f"Horizon: {horizon} months")
            impact = sc.get("impact", sc.get("projected_metrics", {}))
            if isinstance(impact, dict) and impact:
                cols = st.columns(min(len(impact), 4))
                for idx, (k, v) in enumerate(list(impact.items())[:8]):
                    with cols[idx % len(cols)]:
                        if isinstance(v, (int, float)):
                            st.metric(k, f"{v:,.2f}")
                        else:
                            st.metric(k, str(v))


def _render_vintage_summary(state: Dict[str, Any]) -> None:
    """Render vintage/cohort info from decision state alerts."""
    all_alerts = state.get("critical_alerts", []) + state.get("ranked_alerts", [])
    vintage_alerts = [
        a for a in all_alerts
        if (a.get("alert_id") or "").startswith("cohort_vintage.")
    ]

    if vintage_alerts:
        for va in vintage_alerts:
            sev = va.get("severity", "info")
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(sev, "⚪")
            st.markdown(f"{icon} **{va.get('title', '')}**")
            if va.get("description"):
                st.caption(va["description"])
    else:
        cohort_status = state.get("agent_statuses", {}).get("cohort_vintage", "not_run")
        if cohort_status == "ok":
            st.success("All vintages within thresholds.")
        else:
            st.info("Cohort/Vintage agent has not run yet.")


def main() -> None:
    st.title("🏦 Investor Room")
    st.caption("Consolidated financial intelligence for investors and board.")

    state = load_decision_state()
    scenarios = load_scenario_results()
    holding = _safe_import_holding()

    if state is None and holding is None:
        st.warning("No data available. Run the pipeline first.")
        return

    tab_covenants, tab_holding, tab_scenarios, tab_vintages = st.tabs(
        ["Covenant Monitor", "Holding Indicators", "Scenario Engine", "Vintage Analysis"],
    )

    with tab_covenants:
        st.subheader("Covenant Status")
        if state:
            _render_covenant_section(state)
        else:
            st.info("No decision state available.")

    with tab_holding:
        st.subheader("EEFF Holding — Financial Indicators")
        if holding:
            _render_holding_indicators(holding)
        else:
            st.warning("Holding indicators module not available.")

    with tab_scenarios:
        st.subheader("Scenario Projections")
        _render_scenarios(scenarios if isinstance(scenarios, list) else None)

    with tab_vintages:
        st.subheader("Vintage / Cohort Analysis")
        if state:
            _render_vintage_summary(state)
        else:
            st.info("No decision state available.")


if __name__ == "__main__":
    main()
