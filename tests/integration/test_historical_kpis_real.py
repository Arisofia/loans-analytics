import os
import socket
from datetime import date, timedelta
from urllib.parse import urlparse
from uuid import uuid4
import pytest
pytestmark = pytest.mark.skipif(not os.getenv('RUN_REAL_SUPABASE_TESTS'), reason='Requires RUN_REAL_SUPABASE_TESTS=1 and real Supabase credentials')

@pytest.fixture(scope='module')
def supabase_backend():
    from backend.loans_analytics.multi_agent.historical_backend_supabase import SupabaseHistoricalBackend
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_ANON_KEY'):
        pytest.fail('SUPABASE_URL and SUPABASE_ANON_KEY environment variables required for real Supabase integration tests')
    supabase_url = os.getenv('SUPABASE_URL', '')
    host = urlparse(supabase_url).hostname
    if not host:
        pytest.skip('SUPABASE_URL does not contain a valid hostname')
    try:
        socket.getaddrinfo(host, 443)
    except socket.gaierror as exc:
        pytest.skip(f'Supabase host DNS resolution failed for {host}: {exc}')
    try:
        import requests
        requests.get(f'{supabase_url}/rest/v1/', timeout=5)
    except Exception as exc:
        pytest.skip(f'Supabase endpoint is unreachable: {exc}')
    backend = SupabaseHistoricalBackend()
    return backend

@pytest.fixture(scope='module')
def historical_provider(supabase_backend):
    from backend.loans_analytics.multi_agent.historical_context import HistoricalContextProvider
    return HistoricalContextProvider(mode='REAL', backend=supabase_backend)

@pytest.fixture(scope='module')
def test_portfolio_id():
    return str(uuid4())

@pytest.fixture(scope='module')
def _service_headers(supabase_backend):
    """Headers using the service_role key (bypasses RLS for INSERT)."""
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    if not service_key:
        pytest.skip('SUPABASE_SERVICE_ROLE_KEY required for data seeding')
    return {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
    }

@pytest.fixture(scope='module')
def seed_test_data(supabase_backend, test_portfolio_id, _service_headers):
    from datetime import UTC, datetime
    import requests
    base_date = date.today() - timedelta(days=30)
    test_data = []
    test_kpi_id = f'default_rate_{test_portfolio_id[:8]}'
    for day_offset in range(30):
        current_date = base_date + timedelta(days=day_offset)
        test_data.append({'kpi_id': test_kpi_id, 'date': current_date.isoformat(), 'value_numeric': 0.025 + day_offset * 0.001, 'ts_utc': datetime.now(UTC).isoformat(), 'value_json': {'test': True, 'session': 'g4.2-integration', 'test_id': test_portfolio_id}})
    url = f'{supabase_backend.base_url}/rest/v1/{supabase_backend.table}'
    response = requests.post(url, headers=_service_headers, json=test_data, timeout=10)
    if response.status_code not in (201, 409):
        response.raise_for_status()
    yield {'data': test_data, 'kpi_id': test_kpi_id}
    try:
        delete_url = f'{url}?kpi_id=eq.{test_kpi_id}'
        delete_response = requests.delete(delete_url, headers=_service_headers, timeout=10)
        delete_response.raise_for_status()
    except Exception as e:
        print(f'Warning: Failed to cleanup test data: {e}')

@pytest.mark.integration
@pytest.mark.timeout(30)
def test_supabase_backend_connection(supabase_backend):
    assert supabase_backend.base_url is not None
    assert supabase_backend.api_key is not None
    assert supabase_backend.table == 'historical_kpis'

@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_provider_real_mode(historical_provider):
    assert historical_provider.mode == 'REAL'
    assert historical_provider._backend is not None

@pytest.mark.integration
@pytest.mark.timeout(30)
def test_fetch_historical_kpis_empty_range(historical_provider, test_portfolio_id, seed_test_data):
    result = historical_provider.get_kpi_history(kpi_id='nonexistent_kpi', start_date=date.today() - timedelta(days=60), end_date=date.today() - timedelta(days=31))
    assert isinstance(result, list)
    assert len(result) == 0

@pytest.mark.integration
@pytest.mark.timeout(30)
def test_fetch_historical_kpis_with_data(historical_provider, test_portfolio_id, seed_test_data):
    test_kpi_id = seed_test_data['kpi_id']
    result = historical_provider.get_kpi_history(kpi_id=test_kpi_id, start_date=date.today() - timedelta(days=30), end_date=date.today())
    assert isinstance(result, list)
    assert len(result) == 30
    first_record = result[0]
    assert hasattr(first_record, 'kpi_id')
    assert hasattr(first_record, 'date')
    assert hasattr(first_record, 'value')
    assert hasattr(first_record, 'timestamp')
    assert first_record.kpi_id == test_kpi_id
    assert first_record.value > 0
    dates = [record.date for record in result]
    assert dates == sorted(dates)

@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_kpis_query_performance(historical_provider, test_portfolio_id, seed_test_data):
    import time
    test_kpi_id = seed_test_data['kpi_id']
    start_time = time.time()
    result = historical_provider.get_kpi_history(kpi_id=test_kpi_id, start_date=date.today() - timedelta(days=30), end_date=date.today())
    elapsed_time = time.time() - start_time
    assert len(result) > 0
    assert elapsed_time < 0.5, f'Query took {elapsed_time:.3f}s, expected < 0.5s'

@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_context_provider_cache_behavior(historical_provider, test_portfolio_id, seed_test_data):
    import time
    test_kpi_id = seed_test_data['kpi_id']
    historical_provider.clear_cache()
    result1 = historical_provider.get_kpi_history(kpi_id=test_kpi_id, start_date=date.today() - timedelta(days=30), end_date=date.today())
    start_time = time.time()
    result2 = historical_provider.get_kpi_history(kpi_id=test_kpi_id, start_date=date.today() - timedelta(days=30), end_date=date.today())
    warm_cache_time = time.time() - start_time
    assert len(result1) == len(result2)
    assert warm_cache_time < 0.1, f'Cached query took {warm_cache_time:.3f}s'

@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_trend_analysis_with_real_data(historical_provider, test_portfolio_id, seed_test_data):
    test_kpi_id = seed_test_data['kpi_id']
    trend = historical_provider.get_trend(kpi_id=test_kpi_id, periods=1)
    assert trend.kpi_id == test_kpi_id
    assert trend.direction is not None
    assert trend.strength is not None
    assert trend.slope is not None
    assert trend.r_squared is not None
    assert trend.slope > 0, 'Expected increasing trend from seed data'
    assert trend.percent_change > 0, 'Expected positive percent change'

@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_moving_average_with_real_data(historical_provider, test_portfolio_id, seed_test_data):
    test_kpi_id = seed_test_data['kpi_id']
    ma = historical_provider.get_moving_average(kpi_id=test_kpi_id, window_days=30)
    assert ma is not None
    assert ma > 0
    assert 0.02 < ma < 0.06, f'Moving average {ma} outside expected range'

@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_kpis_data_integrity(supabase_backend, test_portfolio_id, seed_test_data, _service_headers):
    import requests
    test_kpi_id = seed_test_data['kpi_id']
    duplicate_data = {'kpi_id': test_kpi_id, 'value_numeric': 0.999, 'date': (date.today() - timedelta(days=30)).isoformat(), 'ts_utc': '2026-01-28T00:00:00Z', 'value_json': {'test': True, 'duplicate': True}}
    url = f'{supabase_backend.base_url}/rest/v1/{supabase_backend.table}'
    response = requests.post(url, headers=_service_headers, json=duplicate_data, timeout=10)
    assert response.status_code in {201, 409}, f'Expected 201 or 409 for duplicate insert, got {response.status_code}: {response.text}'
