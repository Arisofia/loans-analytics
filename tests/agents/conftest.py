from unittest.mock import MagicMock, Mock
import pytest

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
    return [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'Analyze this data.'}]

@pytest.fixture
def sample_portfolio_data():
    return {'loan_id': 'LOAN-001', 'principal': 10000.0, 'interest_rate': 0.05, 'term_months': 12, 'status': 'active'}

@pytest.fixture
def mock_n8n_webhook():
    webhook = MagicMock()
    webhook.post.return_value = Mock(status_code=200, json=lambda: {'success': True})
    return webhook

@pytest.fixture
def agent_execution_context():
    return {'user_id': 'test-user-123', 'session_id': 'test-session-456', 'timestamp': '2026-01-28T00:00:00Z', 'environment': 'test'}

@pytest.fixture
def performance_metrics():
    metrics = {'execution_times': [], 'token_counts': [], 'api_calls': []}
    return metrics

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key-123')
    monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
    monkeypatch.setenv('SUPABASE_KEY', 'test-supabase-key')
    monkeypatch.setenv('ENVIRONMENT', 'test')

@pytest.fixture
def mock_agent_response():
    return {'agent_name': 'test_agent', 'status': 'success', 'result': {'analysis': 'Test analysis complete'}, 'metadata': {'execution_time_ms': 150, 'tokens_used': 250, 'api_calls': 1}}

@pytest.fixture
def async_timeout():
    return 30
