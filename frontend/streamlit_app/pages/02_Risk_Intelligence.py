import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
import pandas as pd
import streamlit as st
from backend.python.logging_config import get_logger
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
AGENT_OUTPUTS_DIR = ROOT_DIR / 'data' / 'agent_outputs'
logger = get_logger(__name__)
st.set_page_config(page_title='Risk Intelligence', page_icon='🛡️', layout='wide')
AGENT_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

def get_agent_output_files() -> list[Path]:
    if not AGENT_OUTPUTS_DIR.exists():
        return []
    files = list(AGENT_OUTPUTS_DIR.glob('*_response.json'))
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)

def parse_agent_output(file_path: Path) -> dict[str, Any]:
    try:
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)
        filename = file_path.stem
        parts = filename.split('_')
        timestamp_str = parts[0] if len(parts) > 0 else 'unknown'
        agent_name = parts[1] if len(parts) > 1 else 'unknown'
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, OSError):
            formatted_time = timestamp_str
        return {'timestamp': formatted_time, 'agent': agent_name.replace('-', ' ').title(), 'query': data.get('query', 'N/A'), 'response': data.get('response', 'N/A'), 'status': data.get('status', 'unknown'), 'tokens': data.get('tokens_used', 0), 'cost': data.get('cost_usd', 0.0), 'raw_data': data}
    except Exception as exc:
        logger.exception('Error parsing agent output file %s: %s', file_path, exc)
        return {'timestamp': 'Error', 'agent': 'Error', 'query': 'Failed to parse file', 'response': str(exc), 'status': 'error', 'tokens': 0, 'cost': 0.0, 'raw_data': {}}
st.title('🤖 Agent Insights')
st.markdown('View AI agent feedback, conversation history, and recommendations from the multi-agent system.')
st.sidebar.header('Filters')
output_files = get_agent_output_files()
if not output_files:
    st.warning('No agent outputs found. Run agents using:\n\n```bash\npython -m src.agents.multi_agent.cli \\\n  --agent risk \\\n  --query "Your question here"\n```')
    with st.expander('📖 How to Use Multi-Agent System'):
        st.markdown('\n        ### Available Agents\n\n        1. **Risk Analyst** - Portfolio risk assessment\n        2. **Growth Strategist** - Expansion opportunities\n        3. **Operations Optimizer** - Process efficiency\n        4. **Compliance Officer** - Regulatory adherence\n        5. **Collections Specialist** - Recovery strategies\n        6. **Fraud Detection** - Anomaly identification\n        7. **Pricing Strategist** - Rate optimization\n        8. **Retention Specialist** - Customer lifecycle\n        9. **Database Designer** - Schema optimization\n\n        ### CLI Usage\n\n        ```bash\n        # Activate environment\n        source .venv/bin/activate\n\n        # Run single agent\n        python -m src.agents.multi_agent.cli \\\n          --agent risk \\\n          --query "Analyze portfolio with DPD > 30"\n\n        # Run pre-built scenario\n        python -m src.agents.multi_agent.cli \\\n          --scenario "monthly_portfolio_health"\n\n        # List scenarios\n        python -m src.agents.multi_agent.cli --list-scenarios\n        ```\n\n        ### Output Location\n\n        Agent responses are saved to:\n        ```\n        data/agent_outputs/<timestamp>_<agent_name>_response.json\n        ```\n\n        This page automatically loads and displays all saved agent interactions.\n        ')
    st.stop()
parsed_outputs = [parse_agent_output(f) for f in output_files]
agents = sorted({output['agent'] for output in parsed_outputs})
selected_agents = st.sidebar.multiselect('Select Agents', options=agents, default=agents)
min_date = datetime.now().date()
if parsed_outputs:
    try:
        dates = [datetime.fromisoformat(output['timestamp']).date() for output in parsed_outputs if output['timestamp'] != 'Error']
        if dates:
            min_date = min(dates)
    except (ValueError, OSError):
        logger.warning('Failed to parse one or more agent interaction timestamps; using default date filter of %s', min_date)
date_filter = st.sidebar.date_input('Show interactions since', value=min_date, max_value=datetime.now().date())
filtered_outputs = [output for output in parsed_outputs if output['agent'] in selected_agents]
if date_filter:
    filtered_outputs = [output for output in filtered_outputs if output['timestamp'] != 'Error' and datetime.fromisoformat(output['timestamp']).date() >= date_filter]
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric('Total Interactions', len(filtered_outputs))
with col2:
    total_tokens = sum((output['tokens'] for output in filtered_outputs))
    st.metric('Total Tokens Used', f'{total_tokens:,}')
with col3:
    total_cost = sum((output['cost'] for output in filtered_outputs))
    st.metric('Total Cost', f'${total_cost:.4f}')
with col4:
    success_count = sum((o['status'] == 'success' for o in filtered_outputs))
    success_rate = success_count / len(filtered_outputs) * 100 if filtered_outputs else 0
    st.metric('Success Rate', f'{success_rate:.1f}%')
st.markdown('---')
display_mode = st.radio('Display Mode', options=['💬 Conversations', '📊 Summary Table', '📈 Analytics'], horizontal=True)
if display_mode == '💬 Conversations':
    st.subheader('Agent Conversations')
    for i, output in enumerate(filtered_outputs):
        with st.expander(f"🤖 {output['agent']} - {output['timestamp']} ({('✅' if output['status'] == 'success' else '❌')})", expanded=i == 0):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"**Agent:** {output['agent']}")
            with col2:
                st.caption(f"**Tokens:** {output['tokens']}")
            with col3:
                st.caption(f"**Cost:** ${output['cost']:.4f}")
            st.markdown('**Query:**')
            st.info(output['query'])
            st.markdown('**Response:**')
            if output['status'] == 'success':
                st.success(output['response'])
            else:
                st.error(output['response'])
            with st.expander('🔍 View Raw JSON'):
                st.json(output['raw_data'])
elif display_mode == '📊 Summary Table':
    st.subheader('Summary Table')
    df = pd.DataFrame([{'Timestamp': output['timestamp'], 'Agent': output['agent'], 'Status': output['status'], 'Query': output['query'][:100] + '...' if len(output['query']) > 100 else output['query'], 'Tokens': output['tokens'], 'Cost ($)': output['cost']} for output in filtered_outputs])
    st.dataframe(df, width='stretch', hide_index=True)
    if st.button('📥 Export to CSV'):
        csv = df.to_csv(index=False)
        st.download_button(label='Download CSV', data=csv, file_name=f"agent_insights_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv')
else:
    st.subheader('Agent Analytics')
    if not filtered_outputs:
        st.info('No data to display')
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('#### Interactions by Agent')
            agent_counts: dict[str, int] = {}
            for output in filtered_outputs:
                agent_counts[output['agent']] = agent_counts.get(output['agent'], 0) + 1
            agent_df = pd.DataFrame([{'Agent': agent, 'Count': count} for agent, count in agent_counts.items()]).sort_values('Count', ascending=False)
            st.bar_chart(agent_df.set_index('Agent'))
        with col2:
            st.markdown('#### Cost by Agent')
            agent_costs: dict[str, float] = {}
            for output in filtered_outputs:
                agent_costs[output['agent']] = agent_costs.get(output['agent'], 0) + output['cost']
            cost_df = pd.DataFrame([{'Agent': agent, 'Cost ($)': cost} for agent, cost in agent_costs.items()]).sort_values('Cost ($)', ascending=False)
            st.bar_chart(cost_df.set_index('Agent'))
        st.markdown('#### Interaction Timeline')
        timeline_data: dict[date, int] = {}
        for output in filtered_outputs:
            if output['timestamp'] != 'Error':
                try:
                    date_key = datetime.fromisoformat(output['timestamp']).date()
                    timeline_data[date_key] = timeline_data.get(date_key, 0) + 1
                except (ValueError, OSError):
                    continue
        if timeline_data:
            timeline_df = pd.DataFrame([{'Date': date, 'Interactions': count} for date, count in sorted(timeline_data.items())])
            st.line_chart(timeline_df.set_index('Date'))
st.markdown('---')
st.caption('💡 Tip: Agent outputs are saved automatically to `data/agent_outputs/`')
