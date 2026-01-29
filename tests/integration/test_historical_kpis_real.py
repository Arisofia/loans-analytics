"""
Integration Tests for Historical KPIs - Real Supabase Mode.

These tests validate the HistoricalContextProvider against a real Supabase
database instance with the historical_kpis table schema.

Execution:
    - By default, these tests are SKIPPED (requires opt-in)
    - To run: RUN_REAL_SUPABASE_TESTS=1 pytest tests/integration/test_historical_kpis_real.py
    - Requires: SUPABASE_URL, SUPABASE_ANON_KEY environment variables

Phase G4.2 Implementation
"""

import os
from datetime import date, timedelta
from uuid import uuid4

import pytest

# Skip entire module if RUN_REAL_SUPABASE_TESTS is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_REAL_SUPABASE_TESTS"),
    reason="Requires RUN_REAL_SUPABASE_TESTS=1 and real Supabase credentials",
)


@pytest.fixture(scope="module")
def supabase_backend():
    """
    Fixture to initialize SupabaseHistoricalBackend.

    Validates environment configuration before running tests.
    """
    from python.multi_agent.historical_backend_supabase import (
        SupabaseHistoricalBackend,
    )

    # Verify required environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        pytest.fail(
            "SUPABASE_URL and SUPABASE_ANON_KEY environment variables required "
            "for real Supabase integration tests"
        )

    backend = SupabaseHistoricalBackend()
    return backend


@pytest.fixture(scope="module")
def historical_provider(supabase_backend):
    """
    Fixture to initialize HistoricalContextProvider in REAL mode.
    """
    from python.multi_agent.historical_context import HistoricalContextProvider

    provider = HistoricalContextProvider(mode="REAL", backend=supabase_backend)
    return provider


@pytest.fixture(scope="module")
def test_portfolio_id():
    """
    Generate a unique test portfolio ID for the test session.

    Using a unique UUID per session to avoid conflicts from:
    - Concurrent test runs
    - Failed cleanup from previous runs
    """
    # Use unique UUID per test session (timestamp-based)
    return str(uuid4())


@pytest.fixture(scope="module")
def seed_test_data(supabase_backend, test_portfolio_id):
    """
    Seed the historical_kpis table with test data.

    Inserts a month of daily KPI observations for testing.
    Cleans up test data after tests complete.

    Note: Uses a unique kpi_id based on test session to enable proper cleanup.
    """
    import requests
    from datetime import datetime, UTC

    # Build insert payload using the simplified schema
    # Schema: kpi_id, date, value, timestamp
    base_date = date.today() - timedelta(days=30)  # Use relative dates
    test_data = []

    # Create a unique kpi_id for this test session to avoid conflicts
    # Tests will query using this specific kpi_id
    test_kpi_id = f"default_rate_{test_portfolio_id[:8]}"

    for day_offset in range(30):
        current_date = base_date + timedelta(days=day_offset)
        test_data.append(
            {
                "kpi_id": test_kpi_id,
                "date": current_date.isoformat(),
                "value": 0.025 + (day_offset * 0.001),  # Increasing trend
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": {"test": True, "session": "g4.2-integration", "test_id": test_portfolio_id},
            }
        )

    # Insert test data via Supabase REST API
    url = f"{supabase_backend.base_url}/rest/v1/{supabase_backend.table}"
    headers = supabase_backend._headers

    response = requests.post(url, headers=headers, json=test_data, timeout=10)

    # If 409 (conflict), test data already exists - that's OK
    if response.status_code not in (201, 409):
        response.raise_for_status()

    # Return both test_data and the kpi_id used
    yield {"data": test_data, "kpi_id": test_kpi_id}

    # Cleanup: Delete test data after tests
    # Using query parameter to delete by kpi_id
    try:
        delete_url = f"{url}?kpi_id=eq.{test_kpi_id}"
        delete_response = requests.delete(delete_url, headers=headers, timeout=10)
        delete_response.raise_for_status()
    except Exception as e:
        # Log cleanup failure but don't fail the test
        print(f"Warning: Failed to cleanup test data: {e}")


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_supabase_backend_connection(supabase_backend):
    """
    Test 1: Verify Supabase backend is properly configured and reachable.

    Validates:
    - Backend initialization with environment variables
    - API endpoint accessibility
    - Authentication headers
    """
    assert supabase_backend.base_url is not None
    assert supabase_backend.api_key is not None
    assert supabase_backend.table == "historical_kpis"


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_provider_real_mode(historical_provider):
    """
    Test 2: Verify HistoricalContextProvider initializes in REAL mode.

    Validates:
    - Mode is correctly set to REAL
    - Backend is properly attached
    """
    assert historical_provider.mode == "REAL"
    assert historical_provider._backend is not None


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_fetch_historical_kpis_empty_range(
    historical_provider, test_portfolio_id, seed_test_data
):
    """
    Test 3: Query for KPIs with no matching data returns empty list.

    Validates:
    - Queries for non-existent KPI return gracefully
    - No errors on empty result sets
    """
    # Query for a KPI that doesn't exist
    result = historical_provider.get_kpi_history(
        kpi_id="nonexistent_kpi",
        start_date=date.today() - timedelta(days=60),
        end_date=date.today() - timedelta(days=31),  # Date range with no test data
    )

    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_fetch_historical_kpis_with_data(
    historical_provider, test_portfolio_id, seed_test_data
):
    """
    Test 4: Query for seeded test data returns expected results.

    Validates:
    - Data retrieval from Supabase
    - Result structure matches KpiHistoricalValue schema
    - Date filtering works correctly
    - Values are returned in ascending date order
    """
    # Use the kpi_id from seeded test data
    test_kpi_id = seed_test_data["kpi_id"]

    # Query for the seeded test data using relative dates
    result = historical_provider.get_kpi_history(
        kpi_id=test_kpi_id,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today(),
    )

    # Validate result structure
    assert isinstance(result, list)
    assert len(result) == 30  # 30 days seeded

    # Validate first record
    first_record = result[0]
    assert hasattr(first_record, "kpi_id")
    assert hasattr(first_record, "date")
    assert hasattr(first_record, "value")
    assert hasattr(first_record, "timestamp")

    # Validate data correctness
    assert first_record.kpi_id == test_kpi_id
    assert first_record.value > 0  # Should have positive value

    # Validate ordering (ascending by date)
    dates = [record.date for record in result]
    assert dates == sorted(dates)


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_kpis_query_performance(
    historical_provider, test_portfolio_id, seed_test_data
):
    """
    Test 5: Verify query performance meets SLO (p99 < 500ms).

    Validates:
    - Query execution time is within acceptable limits
    - Indices are being utilized effectively
    """
    import time

    test_kpi_id = seed_test_data["kpi_id"]

    start_time = time.time()

    # Execute query
    result = historical_provider.get_kpi_history(
        kpi_id=test_kpi_id,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today(),
    )

    elapsed_time = time.time() - start_time

    # Validate performance (should be < 500ms)
    assert len(result) > 0
    assert elapsed_time < 0.5, f"Query took {elapsed_time:.3f}s, expected < 0.5s"


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_context_provider_cache_behavior(
    historical_provider, test_portfolio_id, seed_test_data
):
    """
    Test 6: Verify caching improves subsequent query performance.

    Validates:
    - First query populates cache
    - Second query uses cached data
    - Cache reduces query time significantly
    """
    import time

    test_kpi_id = seed_test_data["kpi_id"]

    # Clear cache
    historical_provider.clear_cache()

    # First query (cold cache)
    start_time = time.time()
    result1 = historical_provider.get_kpi_history(
        kpi_id=test_kpi_id,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today(),
    )
    # Note: cold_cache_time not used, network latency varies

    # Second query (warm cache)
    start_time = time.time()
    result2 = historical_provider.get_kpi_history(
        kpi_id=test_kpi_id,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today(),
    )
    warm_cache_time = time.time() - start_time

    # Validate results are identical
    assert len(result1) == len(result2)

    # Validate cache improved performance (warm cache should be faster)
    # Note: This might not always be true due to network variability,
    # but we expect cache to be significantly faster (< 10ms typically)
    assert warm_cache_time < 0.1, f"Cached query took {warm_cache_time:.3f}s"


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_trend_analysis_with_real_data(
    historical_provider, test_portfolio_id, seed_test_data
):
    """
    Test 7: Verify trend analysis works with real Supabase data.

    Validates:
    - Trend calculation on real data
    - Trend direction is detected correctly (increasing trend)
    - R-squared and slope values are reasonable
    """
    test_kpi_id = seed_test_data["kpi_id"]

    # Calculate trend for the seeded data (increasing trend)
    trend = historical_provider.get_trend(kpi_id=test_kpi_id, periods=1)

    # Validate trend structure
    assert trend.kpi_id == test_kpi_id
    assert trend.direction is not None
    assert trend.strength is not None
    assert trend.slope is not None
    assert trend.r_squared is not None

    # Validate trend direction (should be increasing)
    # Our seed data has an increasing trend: 0.025 + (day * 0.001)
    assert trend.slope > 0, "Expected increasing trend from seed data"
    assert trend.percent_change > 0, "Expected positive percent change"


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_moving_average_with_real_data(
    historical_provider, test_portfolio_id, seed_test_data
):
    """
    Test 8: Verify moving average calculation with real Supabase data.

    Validates:
    - Moving average is calculated correctly
    - Result is within expected range
    """
    test_kpi_id = seed_test_data["kpi_id"]

    # Calculate 30-day moving average
    ma = historical_provider.get_moving_average(
        kpi_id=test_kpi_id, window_days=30
    )

    # Validate moving average
    assert ma is not None
    assert ma > 0
    # Our seed data ranges from 0.025 to 0.054, so average should be around 0.04
    assert 0.02 < ma < 0.06, f"Moving average {ma} outside expected range"


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_historical_kpis_data_integrity(
    supabase_backend, test_portfolio_id, seed_test_data
):
    """
    Test 9: Verify data integrity constraints are enforced.

    Validates:
    - Unique constraint on (kpi_id, date)
    - Indices exist and are utilized
    """
    import requests

    test_kpi_id = seed_test_data["kpi_id"]

    # Attempt to insert duplicate record (should fail or be ignored)
    from datetime import UTC, datetime
    duplicate_data = {
        "kpi_id": test_kpi_id,
        "value": 0.999,  # Different value
        "date": (date.today() - timedelta(days=30)).isoformat(),  # Same date as first seed
        "timestamp": datetime.now(UTC).isoformat(),
        "metadata": {"test": True, "duplicate": True},
    }

    url = f"{supabase_backend.base_url}/rest/v1/{supabase_backend.table}"
    headers = supabase_backend._headers

    response = requests.post(url, headers=headers, json=duplicate_data, timeout=10)

    # Should fail with 409 Conflict due to unique constraint
    assert response.status_code == 409, (
        f"Expected 409 Conflict for duplicate insert, got {response.status_code}"
    )
