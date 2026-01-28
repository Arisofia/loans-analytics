# Phase G4.2: Real Data Source Integration

## Overview

Phase G4.2 extends the Historical Context Provider with support for real data sources while maintaining full backward compatibility with Phase G4.1's mock data mode.

## Architecture

### Two-Mode Design

1. **MOCK Mode** (Default)
   - Uses deterministic synthetic data
   - No external dependencies
   - Perfect for unit tests and development
   - Fully backward compatible with G4.1

2. **REAL Mode** (New in G4.2)
   - Delegates to pluggable backend
   - Supports Supabase and future data sources
   - Requires environment configuration
   - Production-ready

### Mode Selection

Modes can be selected in three ways (priority order):

1. **Constructor parameter** (highest priority):

   ```python
   provider = HistoricalContextProvider(mode="REAL", backend=backend)
   ```

2. **Environment variable**:

   ```bash
   export HISTORICAL_CONTEXT_MODE=REAL
   ```

3. **Default**: `MOCK` (G4.1 backward compatibility)

## Usage Examples

### Mock Mode (Default - G4.1 Compatible)

```python
from python.multi_agent.historical_context import HistoricalContextProvider

# Works exactly as Phase G4.1 - no changes needed
provider = HistoricalContextProvider()
history = provider.get_kpi_history("default_rate", start_date, end_date)
```

### Real Mode with Supabase

```python
from python.multi_agent.historical_context import HistoricalContextProvider
from python.multi_agent.historical_backend_supabase import (
    SupabaseHistoricalBackend
)

# Configure Supabase backend
backend = SupabaseHistoricalBackend()

# Create provider in REAL mode
provider = HistoricalContextProvider(
    cache_ttl_seconds=3600,
    mode="REAL",
    backend=backend
)

# Use exactly as before - implementation is transparent
history = provider.get_kpi_history("default_rate", start_date, end_date)
trend = provider.get_trend("default_rate", periods=30)
```

## Environment Configuration

### Supabase Backend

Required environment variables:

```bash
# Mode selection
export HISTORICAL_CONTEXT_MODE=REAL

# Supabase configuration
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-or-service-key"
export SUPABASE_HISTORICAL_KPI_TABLE="historical_kpis"  # Optional, defaults to "historical_kpis"
```

### Supabase Table Schema

```sql
CREATE TABLE historical_kpis (
    id BIGSERIAL PRIMARY KEY,
    kpi_id TEXT NOT NULL,
    date DATE NOT NULL,
    value NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(kpi_id, date)
);

CREATE INDEX idx_historical_kpis_lookup
    ON historical_kpis(kpi_id, date);

-- Optional: Add RLS policies for security
ALTER TABLE historical_kpis ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read access to historical KPIs"
    ON historical_kpis FOR SELECT
    USING (true);
```

## Testing

### Unit Tests (MOCK Mode)

All Phase G4.1 tests run unchanged in MOCK mode:

```bash
pytest python/multi_agent/test_historical_context.py
```

**Result**: 20/20 tests passing

- 14 original G4.1 tests (historical data, trends, caching)
- 6 new G4.2 tests (mode selection, validation)

### Integration Tests (REAL Mode)

Mark integration tests with `@pytest.mark.integration`:

```python
import pytest

@pytest.mark.integration
def test_real_supabase_backend():
    """Integration test requiring live Supabase connection."""
    # Only runs when: pytest -m integration
    pass
```

Run integration tests:

```bash
# Skip integration tests (default)
pytest python/multi_agent/test_historical_context.py

# Run integration tests only
pytest python/multi_agent/test_historical_context.py -m integration

# Run all tests
pytest python/multi_agent/test_historical_context.py -m ""
```

## CI/CD Configuration

### Default: MOCK Mode

CI pipelines run in MOCK mode by default (no configuration needed):

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest python/multi_agent/test_historical_context.py
  # HISTORICAL_CONTEXT_MODE not set → defaults to MOCK
```

### Optional: Integration Tests

Add a separate job for integration tests:

```yaml
integration-tests:
  runs-on: ubuntu-latest
  if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
  steps:
    - uses: actions/checkout@v3
    - name: Run integration tests
      run: pytest -m integration
      env:
        HISTORICAL_CONTEXT_MODE: REAL
        SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
        SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
```

## Migration Path from G4.1 to G4.2

### Phase 1: Code Deployment (Zero Downtime)

1. Deploy Phase G4.2 code (this PR)
2. **No configuration changes needed**
3. System continues running in MOCK mode
4. All G4.1 tests remain green

### Phase 2: Data Source Setup

1. Create Supabase table with schema above
2. Populate with historical data
3. Set environment variables in staging

### Phase 3: Gradual Rollout

1. Enable REAL mode in staging:
   ```bash
   export HISTORICAL_CONTEXT_MODE=REAL
   ```
2. Monitor behavior and performance
3. Roll back to MOCK if needed (just unset variable)
4. Enable in production when validated

## Backward Compatibility Guarantees

✅ **All Phase G4.1 code works unchanged**

- `HistoricalContextProvider()` constructor (no args)
- `get_kpi_history()` method signature
- `get_trend()` method signature
- `get_moving_average()` method signature
- Mock data generation behavior

✅ **All Phase G4.1 tests pass**

- 14/14 original tests green
- No test modifications required

✅ **MOCK mode is the default**

- No breaking changes
- Explicit opt-in to REAL mode

## Custom Backend Implementation

Implement the `HistoricalDataBackend` protocol:

```python
from python.multi_agent.historical_context import (
    HistoricalDataBackend,
    KpiHistoricalValue
)
from datetime import date
from typing import List

class CustomBackend(HistoricalDataBackend):
    """Custom data source implementation."""

    def get_kpi_history(
        self,
        kpi_id: str,
        start_date: date,
        end_date: date,
    ) -> List[KpiHistoricalValue]:
        # Your implementation here
        # - Query your database
        # - Call external API
        # - Read from files
        # - etc.
        pass
```

Use with provider:

```python
backend = CustomBackend()
provider = HistoricalContextProvider(mode="REAL", backend=backend)
```

## Performance Considerations

### Caching

Both MOCK and REAL modes use the same caching layer:

```python
provider = HistoricalContextProvider(
    cache_ttl_seconds=3600,  # 1 hour cache
    mode="REAL",
    backend=backend
)
```

### Supabase Query Optimization

The Supabase backend uses indexed queries:

```sql
-- Automatically uses idx_historical_kpis_lookup
SELECT * FROM historical_kpis
WHERE kpi_id = 'default_rate'
  AND date >= '2026-01-01'
  AND date <= '2026-01-31'
ORDER BY date ASC;
```

### Request Timeouts

All HTTP requests have 10-second timeouts:

```python
response = requests.get(url, headers=headers, params=params, timeout=10)
```

## Error Handling

### Configuration Errors

```python
# Missing backend in REAL mode
RuntimeError: HistoricalContextProvider in REAL mode requires a backend

# Invalid mode
ValueError: Invalid mode 'INVALID'. Must be 'MOCK' or 'REAL'.

# Missing Supabase credentials
RuntimeError: SupabaseHistoricalBackend requires SUPABASE_URL and SUPABASE_ANON_KEY
```

### Runtime Errors

```python
# Supabase API errors
requests.HTTPError: 404 Not Found (table doesn't exist)
requests.HTTPError: 401 Unauthorized (invalid API key)

# Network errors
requests.Timeout: Request timed out after 10 seconds
```

## Next Steps (Future Phases)

### Phase G4.3: Trend Analysis Enhancements

- Exponential smoothing
- Polynomial regression
- Seasonal decomposition

### Phase G4.4: Forecasting

- ARIMA models
- Prophet integration
- Confidence intervals

### Phase G4.5: Benchmarking

- Industry comparisons
- Peer analysis
- Historical baselines

## Files Changed

### Core Implementation

- `python/multi_agent/historical_context.py` - Added mode selection and Protocol
- `python/multi_agent/historical_backend_supabase.py` - New Supabase backend

### Tests

- `python/multi_agent/test_historical_context.py` - Added 6 mode selection tests

### Documentation

- `docs/phase-g4.2-real-data-integration.md` - This file

## Test Results

```
20 passed, 7 warnings in 0.20s

Phase G4.1 Tests (14): ✅ All passing
Phase G4.2 Tests (6):  ✅ All passing

Coverage: Historical context provider - 100%
```

## Summary

Phase G4.2 delivers:

- ✅ Clean abstraction for data sources
- ✅ Pluggable backend architecture
- ✅ Supabase integration ready
- ✅ 100% backward compatible
- ✅ Zero breaking changes
- ✅ CI-ready (MOCK default)
- ✅ Production-ready (REAL opt-in)
- ✅ 20/20 tests passing
