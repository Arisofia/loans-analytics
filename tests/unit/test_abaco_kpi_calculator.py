import pytest
import pandas as pd
from src.analytics.kpi_calculator_complete import ABACOKPICalculator

@pytest.fixture
def sample_data():
    loans = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "outstanding_balance": [1000.0, 2000.0, 0.0],
        "term": [12, 24, 6],
        "disbursement_date": ["2023-01-01", "2023-01-01", "2023-01-01"]
    })
    payments = pd.DataFrame({
        "loan_id": [1, 2],
        "amount": [100.0, 200.0],
        "payment_date": ["2023-02-01", "2023-02-01"]
    })
    customers = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "customer_type": ["retail", "business", "retail"]
    })
    return loans, payments, customers

def test_calculator_init(sample_data):
    loans, payments, customers = sample_data
    calc = ABACOKPICalculator(loans, payments, customers)
    assert calc.get_active_clients() == 3
    assert calc.get_total_aum() == 3000.0

def test_aum_by_customer_type(sample_data):
    loans, payments, customers = sample_data
    calc = ABACOKPICalculator(loans, payments, customers)
    df = calc.get_aum_by_customer_type()
    assert len(df) > 0
    assert "customer_type" in df.columns
