# Historical Context Integration

## Purpose
This document describes how historical context is integrated in the multi-agent analytics stack, how forecasts are generated, and how caching is managed for predictable performance.

## Architecture
- Core provider: `python/multi_agent/historical_context.py`
- Integration point: `python/multi_agent/orchestrator.py`
- Validation suites:
  - `python/multi_agent/test_historical_context.py`
  - `python/multi_agent/test_trend_analysis_g4_2.py`

The provider exposes deterministic methods for:
- Trend analysis (`get_trend`, `get_exponential_trend`, `get_polynomial_trend`)
- Seasonality (`get_seasonality`, `get_seasonal_decomposition`, `deseasonalize`)
- Forecasting (`get_forecast`, `validate_forecast`, `get_scenario_projection`)
- Benchmarking (`get_benchmarks`, `get_percentile_ranking`, `get_z_score`, `get_gap_analysis`)

## Data Usage Guide
Historical context is consumed as a read-only analytical layer. The orchestrator requests KPI history and derived trend/forecast artifacts, then injects the results into agent context for scenario workflows.

Typical flow:
1. Resolve KPI history for a date window.
2. Compute trend and seasonality factors.
3. Build base forecast and scenario-adjusted projections.
4. Compare against benchmark/regulatory thresholds.
5. Return a compact context payload to the agent step.

## Caching Strategy
- TTL-based cache is implemented in `HistoricalContextProvider`.
- Default design target: 1-hour cache horizon for repeated KPI window queries.
- Cache management:
  - Warm on first query.
  - Reuse by `(kpi_id, date_range)` key.
  - Explicit invalidation via `clear_cache()`.

Operational notes:
- Keeps repeated analyses fast in multi-agent runs.
- Maintains deterministic outputs within a run window.
- Reduces unnecessary recomputation in stress/scenario exploration.

## Trend and Forecast Examples

### Example 1: Exponential trend
```python
provider = HistoricalContextProvider()
trend = provider.get_exponential_trend("default_rate", alpha=0.3, periods=3)
```

### Example 2: Seasonality decomposition
```python
decomp = provider.get_seasonal_decomposition("default_rate", model="additive")
```

### Example 3: Scenario projection
```python
scenarios = {"best_case": 1.1, "worst_case": 0.9, "most_likely": 1.0}
proj = provider.get_scenario_projection("default_rate", scenarios, steps=30)
```

### Example 4: Forecast validation
```python
forecast = provider.get_forecast("default_rate", steps=14, method="exponential_smoothing")
metrics = provider.validate_forecast("default_rate", forecast)
```

## Quality and Verification
- Multi-agent and historical context suites pass in CI/local runs.
- E2E workflow validates API + dashboard behavior with real pipeline artifacts.
- Forecast outputs include confidence bounds and uncertainty expansion over time.

## Scope Notes
- "ARIMA" support is API-compatible through the forecast method selector path.
- The current implementation prioritizes deterministic and dependency-light behavior suitable for pipeline reproducibility.
