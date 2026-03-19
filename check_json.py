import json
try:
    with open('exports/complete_kpi_dashboard.json', 'r') as f:
        data = json.load(f)
    print(f"Portfolio Analytics present: {'portfolio_analytics' in data.get('extended_kpis', {})}")
    if 'portfolio_analytics' in data.get('extended_kpis', {}):
        print(f"Keys: {list(data['extended_kpis']['portfolio_analytics'].keys())}")
except Exception as e:
    print(f"Error: {e}")
