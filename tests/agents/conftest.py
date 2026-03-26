import random
from datetime import date, timedelta
from unittest.mock import MagicMock, Mock

import pytest


def _realistic_loan(i: int, status: str, rng: random.Random) -> dict:
    today = date(2026, 3, 26)
    principal = round(rng.uniform(2_500, 45_000), 2)
    dpd_map = {
        "current": 0,
        "30-59 days past due": rng.randint(30, 59),
        "60-89 days past due": rng.randint(60, 89),
        "90+ days past due": rng.randint(90, 179),
        "default": rng.randint(180, 365),
    }
    dpd = dpd_map.get(status, 0)
    return {
        "loan_id": f"LN-A{i:03d}",
        "borrower_id": f"B-A{(i % 20) + 1:02d}",
        "loan_amount": principal,
        "principal_balance": round(principal * rng.uniform(0.30, 0.95), 2),
        "outstanding_loan_value": round(principal * rng.uniform(0.30, 0.95), 2),
        "appraised_value": round(principal * rng.uniform(1.1, 2.4), 2),
        "borrower_income": round(rng.uniform(18_000, 110_000), 2),
        "monthly_debt": round(rng.uniform(300, 2_800), 2),
        "interest_rate": round(rng.uniform(0.18, 0.44), 4),
        "interest_rate_apr": round(rng.uniform(0.18, 0.44), 4),
        "loan_status": status,
        "days_past_due": dpd,
        "term_months": rng.choice([6, 9, 12, 18, 24]),
        "origination_fee": round(principal * rng.uniform(0.01, 0.03), 2),
        "origination_fee_taxes": round(principal * 0.0026, 2),
        "total_scheduled": round(principal * rng.uniform(0.08, 0.15), 2),
        "last_payment_amount": round(principal * rng.uniform(0.05, 0.12), 2),
        "tpv": round(rng.uniform(60_000, 420_000), 2),
        "origination_date": (today - timedelta(days=rng.randint(90, 540))).isoformat(),
    }


@pytest.fixture
def mock_openai_client():
    client = MagicMock()
    client.chat.completions.create.return_value = Mock(choices=[Mock(message=Mock(content='Mocked LLM response'))])
    return client


@pytest.fixture
def mock_supabase_client():
    client = MagicMock()
    client.table.return_value.select.return_value.execute.return_value = Mock(data=[{'id': 1, 'name': 'test'}])
    return client


@pytest.fixture
def mock_llm_provider():
    provider = MagicMock()
    provider.complete.return_value = 'Mocked completion response'
    return provider


@pytest.fixture
def sample_agent_message():
    return [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Analyze this data.'},
    ]


@pytest.fixture
def sample_portfolio_data():
    """Single realistic loan record for agent unit tests."""
    return {
        'loan_id': 'LN-A001',
        'borrower_id': 'B-A01',
        'loan_amount': 18_500.00,
        'principal_balance': 14_320.50,
        'outstanding_loan_value': 14_320.50,
        'appraised_value': 28_000.00,
        'borrower_income': 54_000.00,
        'monthly_debt': 1_100.00,
        'interest_rate': 0.2850,
        'interest_rate_apr': 0.2850,
        'loan_status': 'current',
        'days_past_due': 0,
        'term_months': 18,
        'origination_fee': 370.00,
        'origination_fee_taxes': 48.10,
        'total_scheduled': 2_220.00,
        'last_payment_amount': 1_940.00,
        'tpv': 185_000.00,
        'origination_date': '2025-06-15',
    }


@pytest.fixture
def sample_portfolio_loans():
    """25-loan realistic portfolio for agent integration tests."""
    rng = random.Random(77)
    status_pool = (
        ['current'] * 17
        + ['30-59 days past due'] * 3
        + ['60-89 days past due'] * 2
        + ['90+ days past due'] * 2
        + ['default'] * 1
    )
    return [_realistic_loan(i + 1, status_pool[i], rng) for i in range(25)]


@pytest.fixture
def mock_n8n_webhook():
    webhook = MagicMock()
    webhook.post.return_value = Mock(status_code=200, json=lambda: {'success': True})
    return webhook


@pytest.fixture
def agent_execution_context():
    return {
        'user_id': 'test-user-123',
        'session_id': 'test-session-456',
        'timestamp': '2026-01-28T00:00:00Z',
        'environment': 'test',
    }


@pytest.fixture
def performance_metrics():
    return {'execution_times': [], 'token_counts': [], 'api_calls': []}


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key-123')
    monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
    monkeypatch.setenv('SUPABASE_KEY', 'test-supabase-key')
    monkeypatch.setenv('ENVIRONMENT', 'test')


@pytest.fixture
def mock_agent_response():
    return {
        'agent_name': 'test_agent',
        'status': 'success',
        'result': {'analysis': 'Test analysis complete'},
        'metadata': {'execution_time_ms': 150, 'tokens_used': 250, 'api_calls': 1},
    }


@pytest.fixture
def async_timeout():
    return 30
