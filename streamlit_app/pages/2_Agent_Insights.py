"""Agent Insights - View AI agent feedback and conversation history."""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from python.logging_config import get_logger

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger = get_logger(__name__)

# Configure page
st.set_page_config(
    page_title="Agent Insights - Abaco Analytics",
    page_icon="🤖",
    layout="wide",
)

# Paths for agent data
AGENT_OUTPUTS_DIR = ROOT_DIR / "data" / "agent_outputs"
AGENT_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def get_agent_output_files() -> list[Path]:
    """Get all agent output files sorted by timestamp (newest first)."""
    if not AGENT_OUTPUTS_DIR.exists():
        return []

    files = list(AGENT_OUTPUTS_DIR.glob("*_response.json"))
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def parse_agent_output(file_path: Path) -> dict[str, str]:
    """Parse agent output JSON file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Extract metadata from filename: <timestamp>_<agent_name>_response.json
        filename = file_path.stem  # Remove .json
        parts = filename.split("_")

        timestamp_str = parts[0] if len(parts) > 0 else "unknown"
        agent_name = parts[1] if len(parts) > 1 else "unknown"

        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            formatted_time = timestamp_str

        return {
            "timestamp": formatted_time,
            "agent": agent_name.replace("-", " ").title(),
            "query": data.get("query", "N/A"),
            "response": data.get("response", "N/A"),
            "status": data.get("status", "unknown"),
            "tokens": data.get("tokens_used", 0),
            "cost": data.get("cost_usd", 0.0),
            "raw_data": data,
        }
    except Exception as exc:
        logger.exception("Error parsing agent output file %s: %s", file_path, exc)
        return {
            "timestamp": "Error",
            "agent": "Error",
            "query": "Failed to parse file",
            "response": str(exc),
            "status": "error",
            "tokens": 0,
            "cost": 0.0,
            "raw_data": {},
        }


# Header
st.title("🤖 Agent Insights")
st.markdown(
    "View AI agent feedback, conversation history, and recommendations from the multi-agent system."
)

# Sidebar - Agent selection
st.sidebar.header("Filters")

# Get available agents
output_files = get_agent_output_files()

if not output_files:
    st.warning(
        "No agent outputs found. Run agents using:\n\n"
        "```bash\n"
        "python -m python.multi_agent.cli \\\n"
        "  --agent risk \\\n"
        '  --query "Your question here"\n'
        "```"
    )

    # Show instructions
    with st.expander("📖 How to Use Multi-Agent System"):
        st.markdown("""
        ### Available Agents

        1. **Risk Analyst** - Portfolio risk assessment
        2. **Growth Strategist** - Expansion opportunities
        3. **Operations Optimizer** - Process efficiency
        4. **Compliance Officer** - Regulatory adherence
        5. **Collections Specialist** - Recovery strategies
        6. **Fraud Detection** - Anomaly identification
        7. **Pricing Strategist** - Rate optimization
        8. **Retention Specialist** - Customer lifecycle
        9. **Database Designer** - Schema optimization

        ### CLI Usage

        ```bash
        # Activate environment
        source .venv/bin/activate

        # Run single agent
        python -m python.multi_agent.cli \\
          --agent risk \\
          --query "Analyze portfolio with DPD > 30"

        # Run pre-built scenario
        python -m python.multi_agent.cli \\
          --scenario "monthly_portfolio_health"

        # List scenarios
        python -m python.multi_agent.cli --list-scenarios
        ```

        ### Output Location

        Agent responses are saved to:
        ```
        data/agent_outputs/<timestamp>_<agent_name>_response.json
        ```

        This page automatically loads and displays all saved agent interactions.
        """)

    st.stop()

# Parse all outputs
parsed_outputs = [parse_agent_output(f) for f in output_files]

# Extract unique agents for filter
agents = sorted({output["agent"] for output in parsed_outputs})
selected_agents = st.sidebar.multiselect(
    "Select Agents",
    options=agents,
    default=agents,
)

# Date range filter
min_date = datetime.now().date()
if parsed_outputs:
    try:
        dates = [
            datetime.fromisoformat(output["timestamp"]).date()
            for output in parsed_outputs
            if output["timestamp"] != "Error"
        ]
        if dates:
            min_date = min(dates)
    except (ValueError, OSError):
        logger.warning(
            "Failed to parse one or more agent interaction timestamps; "
            "using default date filter of %s",
            min_date,
        )

date_filter = st.sidebar.date_input(
    "Show interactions since",
    value=min_date,
    max_value=datetime.now().date(),
)

# Filter outputs
filtered_outputs = [output for output in parsed_outputs if output["agent"] in selected_agents]

# Apply date filter
if date_filter:
    filtered_outputs = [
        output
        for output in filtered_outputs
        if output["timestamp"] != "Error"
        and datetime.fromisoformat(output["timestamp"]).date() >= date_filter
    ]

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Interactions", len(filtered_outputs))
with col2:
    total_tokens = sum(output["tokens"] for output in filtered_outputs)
    st.metric("Total Tokens Used", f"{total_tokens:,}")
with col3:
    total_cost = sum(output["cost"] for output in filtered_outputs)
    st.metric("Total Cost", f"${total_cost:.4f}")
with col4:
    success_count = sum(1 for o in filtered_outputs if o["status"] == "success")
    success_rate = (success_count / len(filtered_outputs) * 100) if filtered_outputs else 0
    st.metric("Success Rate", f"{success_rate:.1f}%")

st.markdown("---")

# Display mode selection
display_mode = st.radio(
    "Display Mode",
    options=["💬 Conversations", "📊 Summary Table", "📈 Analytics"],
    horizontal=True,
)

if display_mode == "💬 Conversations":
    # Conversation view - show each interaction
    st.subheader("Agent Conversations")

    for i, output in enumerate(filtered_outputs):
        with st.expander(
            f"🤖 {output['agent']} - {output['timestamp']} "
            f"({'✅' if output['status'] == 'success' else '❌'})",
            expanded=(i == 0),  # Expand first one by default
        ):
            # Metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"**Agent:** {output['agent']}")
            with col2:
                st.caption(f"**Tokens:** {output['tokens']}")
            with col3:
                st.caption(f"**Cost:** ${output['cost']:.4f}")

            # Query
            st.markdown("**Query:**")
            st.info(output["query"])

            # Response
            st.markdown("**Response:**")
            if output["status"] == "success":
                st.success(output["response"])
            else:
                st.error(output["response"])

            # Raw data toggle
            with st.expander("🔍 View Raw JSON"):
                st.json(output["raw_data"])

elif display_mode == "📊 Summary Table":
    # Table view
    st.subheader("Summary Table")

    # Create DataFrame
    df = pd.DataFrame(
        [
            {
                "Timestamp": output["timestamp"],
                "Agent": output["agent"],
                "Status": output["status"],
                "Query": (
                    output["query"][:100] + "..." if len(output["query"]) > 100 else output["query"]
                ),
                "Tokens": output["tokens"],
                "Cost ($)": output["cost"],
            }
            for output in filtered_outputs
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    # Export button
    if st.button("📥 Export to CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"agent_insights_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

else:  # Analytics view
    st.subheader("Agent Analytics")

    if not filtered_outputs:
        st.info("No data to display")
    else:
        # Agent usage distribution
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Interactions by Agent")
            agent_counts = {}
            for output in filtered_outputs:
                agent_counts[output["agent"]] = agent_counts.get(output["agent"], 0) + 1

            agent_df = pd.DataFrame(
                [{"Agent": agent, "Count": count} for agent, count in agent_counts.items()]
            ).sort_values("Count", ascending=False)

            st.bar_chart(agent_df.set_index("Agent"))

        with col2:
            st.markdown("#### Cost by Agent")
            agent_costs = {}
            for output in filtered_outputs:
                agent_costs[output["agent"]] = agent_costs.get(output["agent"], 0) + output["cost"]

            cost_df = pd.DataFrame(
                [{"Agent": agent, "Cost ($)": cost} for agent, cost in agent_costs.items()]
            ).sort_values("Cost ($)", ascending=False)

            st.bar_chart(cost_df.set_index("Agent"))

        # Timeline
        st.markdown("#### Interaction Timeline")

        # Group by date
        timeline_data = {}
        for output in filtered_outputs:
            if output["timestamp"] != "Error":
                try:
                    date = datetime.fromisoformat(output["timestamp"]).date()
                    timeline_data[date] = timeline_data.get(date, 0) + 1
                except (ValueError, OSError):
                    continue

        if timeline_data:
            timeline_df = pd.DataFrame(
                [
                    {"Date": date, "Interactions": count}
                    for date, count in sorted(timeline_data.items())
                ]
            )
            st.line_chart(timeline_df.set_index("Date"))

# Footer
st.markdown("---")
st.caption("💡 Tip: Agent outputs are saved automatically to `data/agent_outputs/`")
