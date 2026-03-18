"""Historical context dashboard for KPI trends, seasonality, and forecasting."""

from calendar import month_name
from datetime import date, timedelta
from typing import List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backend.python.multi_agent.config_historical import build_historical_context_provider
from backend.python.multi_agent.historical_context import (
    HistoricalContextProvider,
    KpiProjection,
    KpiHistoricalValue,
)

st.set_page_config(
    page_title="Historical Context",
    page_icon="History",
    layout="wide",
)

DEFAULT_KPI_IDS = [
    "default_rate",
    "delinquency_rate_30",
    "collection_efficiency",
    "approval_rate",
    "portfolio_growth",
]


@st.cache_resource(show_spinner=False)
def _provider(mode: str) -> HistoricalContextProvider:
    """Build and cache provider per mode."""
    return build_historical_context_provider(mode=mode)


def _history_df(history: List[KpiHistoricalValue]) -> pd.DataFrame:
    """Convert historical values to a plotting dataframe."""
    rows = [{"date": item.date, "value": item.value} for item in history]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date")


def _forecast_df(projections: List[KpiProjection]) -> pd.DataFrame:
    """Convert forecast projections to plotting dataframe."""
    rows = [
        {
            "date": item.projection_date,
            "predicted_value": item.predicted_value,
            "lower_bound": item.lower_bound,
            "upper_bound": item.upper_bound,
            "method": item.method,
        }
        for item in projections
    ]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date")


def _seasonality_df(adjustments: dict[int, float]) -> pd.DataFrame:
    """Prepare monthly adjustment factors for display."""
    if not adjustments:
        return pd.DataFrame()

    rows = []
    for month_idx in sorted(adjustments):
        month_int = int(month_idx)
        rows.append(
            {
                "month": month_name[month_int],
                "month_number": month_int,
                "adjustment_factor": adjustments[month_idx],
            }
        )
    return pd.DataFrame(rows)


st.title("Historical Context")
st.caption("Trend analysis, seasonality decomposition, and forward forecast for selected KPIs.")

sidebar_col_1, sidebar_col_2 = st.columns(2)
with sidebar_col_1:
    selected_mode = st.selectbox("Data Mode", options=["MOCK", "REAL"], index=0)
with sidebar_col_2:
    selected_kpi = st.selectbox("KPI", options=DEFAULT_KPI_IDS, index=0)

custom_kpi_id = st.text_input("Custom KPI ID (optional)", value="")
kpi_id = custom_kpi_id.strip() or selected_kpi

period_days = st.slider("History Window (days)", min_value=30, max_value=730, value=365, step=30)
forecast_steps = st.slider("Forecast Horizon (days)", min_value=7, max_value=180, value=30, step=1)
forecast_method = st.selectbox("Forecast Method", options=["exponential", "linear"], index=0)

try:
    provider = _provider(selected_mode)
except Exception as exc:  # pragma: no cover - defensive UI fallback
    st.warning(
        "REAL mode is not available in the current environment. "
        f"Reason: {exc}. Falling back to MOCK mode."
    )
    selected_mode = "MOCK"
    provider = _provider("MOCK")

end_date = date.today()
start_date = end_date - timedelta(days=period_days)
analysis_periods = max(1, period_days // 30)
seasonality_years = max(1, period_days // 365)

with st.spinner("Computing historical context..."):
    history = provider.get_kpi_history(kpi_id, start_date, end_date)
    trend = provider.get_trend(kpi_id, periods=analysis_periods)
    seasonality = provider.get_seasonality(kpi_id, periods_years=seasonality_years)
    forecast = provider.get_forecast(kpi_id, steps=forecast_steps, method=forecast_method)
    summary = provider.agent_summary(kpi_id, periods=analysis_periods)

history_frame = _history_df(history)
forecast_frame = _forecast_df(forecast)
seasonality_frame = _seasonality_df(seasonality.adjustment_factors)

metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)
metric_1.metric("Mode", selected_mode)
metric_2.metric("Trend Direction", trend.direction.value.title())
metric_3.metric("Trend Strength", trend.strength.value.title())
metric_4.metric("Change (%)", f"{trend.percent_change:.2f}%")
metric_5.metric("R²", f"{trend.r_squared:.3f}")

chart = go.Figure()
if not history_frame.empty:
    chart.add_trace(
        go.Scatter(
            x=history_frame["date"],
            y=history_frame["value"],
            mode="lines",
            name="Historical",
            line={"width": 2},
        )
    )
if not forecast_frame.empty:
    chart.add_trace(
        go.Scatter(
            x=forecast_frame["date"],
            y=forecast_frame["predicted_value"],
            mode="lines",
            name=f"Forecast ({forecast_method})",
            line={"dash": "dash", "width": 2},
        )
    )
    chart.add_trace(
        go.Scatter(
            x=forecast_frame["date"],
            y=forecast_frame["upper_bound"],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    chart.add_trace(
        go.Scatter(
            x=forecast_frame["date"],
            y=forecast_frame["lower_bound"],
            mode="lines",
            line={"width": 0},
            fill="tonexty",
            fillcolor="rgba(31, 119, 180, 0.15)",
            name="Confidence Band",
        )
    )

chart.update_layout(
    title=f"KPI Trajectory: {kpi_id}",
    xaxis_title="Date",
    yaxis_title="Value",
    template="plotly_white",
    height=460,
)
st.plotly_chart(chart, width="stretch")

left_col, right_col = st.columns(2)
with left_col:
    st.subheader("Seasonality")
    st.write(f"Detected: {'Yes' if seasonality.has_seasonality else 'No'}")
    st.write(f"Seasonal strength: {seasonality.seasonal_strength:.3f}")
    st.write(f"Cycle length (months): {seasonality.cycle_length_months or 'N/A'}")
    if not seasonality_frame.empty:
        st.dataframe(
            seasonality_frame[["month", "adjustment_factor"]],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No monthly adjustment factors available for this KPI.")

with right_col:
    st.subheader("Forecast Table")
    if not forecast_frame.empty:
        display_frame = forecast_frame.copy()
        display_frame["date"] = display_frame["date"].dt.date
        st.dataframe(display_frame, width="stretch", hide_index=True)
    else:
        st.info("Forecast output is empty for the selected inputs.")

st.subheader("Agent Summary Payload")
st.json(summary)
