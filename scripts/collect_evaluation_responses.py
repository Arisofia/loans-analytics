import pandas as pd
from apps.analytics.src.enterprise_analytics_engine import LoanAnalyticsEngine

# Load test queries
test_queries = pd.read_csv('data/queries.csv')

# Initialize engine and collect responses
engine = LoanAnalyticsEngine(test_queries)

results = {
    'ltv': engine.compute_loan_to_value().tolist(),
    'dti': engine.compute_debt_to_income().tolist(),
    'risk_alerts': engine.risk_alerts(ltv_threshold=80, dti_threshold=30).to_dict(orient='records'),
    'full_analysis': engine.run_full_analysis()
}

import json
with open('data/responses.json', 'w') as f:
    json.dump(results, f, indent=2)

print('Evaluation responses saved to data/responses.json')
