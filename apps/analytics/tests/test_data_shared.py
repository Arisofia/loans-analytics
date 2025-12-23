"""
Shared test data for analytics engine and metrics utils tests.
"""

SAMPLE_LOAN_DATA = {
    "loan_amount": [250000],
    "appraised_value": [300000],
    "borrower_income": [80000],
    "monthly_debt": [1500],
    "loan_status": ["current"],
    "interest_rate": [0.035],
    "principal_balance": [240000],
}

SAMPLE_LOAN_DATA_MULTI = {
    "loan_amount": [250000, 450000, 150000],
    "appraised_value": [300000, 500000, 160000],
    "borrower_income": [80000, 120000, 60000],
    "monthly_debt": [1500, 2500, 1000],
    "loan_status": ["current", "current", "current"],
    "interest_rate": [0.035, 0.042, 0.038],
    "principal_balance": [240000, 440000, 145000],
}
