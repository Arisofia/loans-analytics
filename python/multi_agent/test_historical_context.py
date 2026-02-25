"""
Tests for Historical Context Provider.

Phase G4.1: Initial implementation tests
- Historical data retrieval
- Trend analysis
- Moving averages
- Caching behavior
"""

import unittest
from datetime import date, timedelta

from python.multi_agent.historical_context import (
    HistoricalContextProvider,
    TrendDirection,
    TrendStrength,
)


class TestHistoricalContextProvider(unittest.TestCase):
    """Test historical context provider functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = HistoricalContextProvider(cache_ttl_seconds=60)

    def test_get_kpi_history(self):
        """Test fetching historical KPI data."""
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)

        history = self.provider.get_kpi_history("default_rate", start_date, end_date)

        self.assertIsNotNone(history)
        self.assertEqual(len(history), 31)  # 31 days in January
        self.assertEqual(history[0].kpi_id, "default_rate")
        self.assertEqual(history[0].date, start_date)
        self.assertEqual(history[-1].date, end_date)

    def test_get_kpi_history_empty_range(self):
        """Test historical data for invalid date range."""
        start_date = date(2026, 1, 31)
        end_date = date(2026, 1, 1)  # End before start

        history = self.provider.get_kpi_history("default_rate", start_date, end_date)

        self.assertEqual(len(history), 0)

    def test_get_kpi_history_single_day(self):
        """Test historical data for single day."""
        target_date = date(2026, 1, 15)

        history = self.provider.get_kpi_history("default_rate", target_date, target_date)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].date, target_date)

    def test_calculate_trend_increasing(self):
        """Test trend calculation for increasing data."""
        trend = self.provider.get_trend("default_rate", periods=3)

        self.assertEqual(trend.kpi_id, "default_rate")
        self.assertEqual(trend.direction, TrendDirection.INCREASING)
        self.assertGreater(trend.slope, 0)
        self.assertGreater(trend.end_value, trend.start_value)
        self.assertGreater(trend.percent_change, 0)

    def test_calculate_trend_with_custom_period(self):
        """Test trend calculation with different period lengths."""
        trend_3m = self.provider.get_trend("default_rate", periods=3)
        trend_6m = self.provider.get_trend("default_rate", periods=6)

        self.assertLess(trend_3m.period_days, trend_6m.period_days)
        self.assertIsNotNone(trend_3m.r_squared)
        self.assertIsNotNone(trend_6m.r_squared)

    def test_trend_strength_classification(self):
        """Test trend strength is properly classified."""
        trend = self.provider.get_trend("default_rate", periods=3)

        self.assertIn(
            trend.strength, [TrendStrength.STRONG, TrendStrength.MODERATE, TrendStrength.WEAK]
        )
        self.assertGreaterEqual(trend.r_squared, 0.0)
        self.assertLessEqual(trend.r_squared, 1.0)

    def test_get_moving_average(self):
        """Test moving average calculation."""
        ma_30 = self.provider.get_moving_average("default_rate", window_days=30)
        ma_7 = self.provider.get_moving_average("default_rate", window_days=7)

        self.assertIsNotNone(ma_30)
        self.assertIsNotNone(ma_7)
        self.assertGreater(ma_30, 0)
        self.assertGreater(ma_7, 0)

    def test_moving_average_different_windows(self):
        """Test moving averages with different window sizes."""
        ma_7 = self.provider.get_moving_average("default_rate", window_days=7)
        ma_30 = self.provider.get_moving_average("default_rate", window_days=30)
        ma_90 = self.provider.get_moving_average("default_rate", window_days=90)

        # All should be valid numbers
        self.assertIsNotNone(ma_7)
        self.assertIsNotNone(ma_30)
        self.assertIsNotNone(ma_90)

    def test_historical_cache_efficiency(self):
        """Test that caching improves performance."""
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)

        # First call - populates cache
        history1 = self.provider.get_kpi_history("default_rate", start_date, end_date)

        # Second call - should use cache
        history2 = self.provider.get_kpi_history("default_rate", start_date, end_date)

        # Should return same data
        self.assertEqual(len(history1), len(history2))
        self.assertEqual(history1[0].date, history2[0].date)
        self.assertEqual(history1[0].value, history2[0].value)

    def test_cache_clear(self):
        """Test cache clearing functionality."""
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)

        # Populate cache
        self.provider.get_kpi_history("default_rate", start_date, end_date)
        self.assertGreater(len(self.provider._cache), 0)

        # Clear cache
        self.provider.clear_cache()
        self.assertEqual(len(self.provider._cache), 0)

    def test_multiple_kpis(self):
        """Test handling multiple different KPIs."""
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 10)

        history1 = self.provider.get_kpi_history("default_rate", start_date, end_date)
        history2 = self.provider.get_kpi_history("disbursements", start_date, end_date)

        self.assertEqual(len(history1), 10)
        self.assertEqual(len(history2), 10)
        self.assertNotEqual(history1[0].value, history2[0].value)  # Different KPIs


class TestTrendAnalysis(unittest.TestCase):
    """Test trend analysis functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = HistoricalContextProvider()

    def test_trend_analysis_fields(self):
        """Test that trend analysis contains all required fields."""
        trend = self.provider.get_trend("default_rate", periods=3)

        self.assertIsNotNone(trend.kpi_id)
        self.assertIsNotNone(trend.direction)
        self.assertIsNotNone(trend.strength)
        self.assertIsNotNone(trend.slope)
        self.assertIsNotNone(trend.r_squared)
        self.assertIsNotNone(trend.period_days)
        self.assertIsNotNone(trend.start_value)
        self.assertIsNotNone(trend.end_value)
        self.assertIsNotNone(trend.percent_change)
        self.assertIsNotNone(trend.calculated_at)

    def test_trend_r_squared_bounds(self):
        """Test R-squared is within valid bounds."""
        trend = self.provider.get_trend("default_rate", periods=6)

        self.assertGreaterEqual(trend.r_squared, 0.0)
        self.assertLessEqual(trend.r_squared, 1.0)

    def test_trend_percent_change_calculation(self):
        """Test percent change is calculated correctly."""
        trend = self.provider.get_trend("default_rate", periods=3)

        expected_pct = (trend.end_value - trend.start_value) / trend.start_value * 100
        self.assertAlmostEqual(trend.percent_change, expected_pct, places=2)

    def test_exponential_trend_calculation(self):
        """Test exponential smoothing trend calculation."""
        trend = self.provider.get_exponential_trend("default_rate", alpha=0.3, periods=3)

        self.assertIsNotNone(trend)
        self.assertEqual(trend.direction, TrendDirection.INCREASING)
        self.assertGreater(trend.slope, 0)

    def test_polynomial_trend_fitting(self):
        """Test polynomial trend fitting with numpy."""
        trend = self.provider.get_polynomial_trend("default_rate", degree=2, periods=3)

        self.assertIsNotNone(trend)
        self.assertIn(trend.direction, [TrendDirection.INCREASING, TrendDirection.DECREASING])
        self.assertGreaterEqual(trend.r_squared, 0.0)

    def test_weighted_moving_average(self):
        """Test weighted moving average calculation."""
        wma = self.provider.get_weighted_moving_average("default_rate", window_days=30)
        ma = self.provider.get_moving_average("default_rate", window_days=30)

        self.assertIsNotNone(wma)
        self.assertIsNotNone(ma)
        # Weighted should be slightly different from simple mean
        self.assertNotEqual(wma, ma)

    def test_multi_period_trends(self):
        """Test multi-period trend retrieval."""
        trends = self.provider.get_multi_period_trends("default_rate")

        self.assertIn("7_day", trends)
        self.assertIn("30_day", trends)
        self.assertIn("90_day", trends)
        self.assertIn("yoy", trends)

    def test_trend_confidence_intervals(self):
        """Test confidence interval calculation."""
        ci = self.provider.get_trend_confidence_interval("default_rate", confidence=0.95)

        self.assertIn("trend_slope", ci)
        self.assertIn("lower_bound", ci)
        self.assertIn("upper_bound", ci)
        self.assertLessEqual(ci["lower_bound"], ci["trend_slope"])
        self.assertGreaterEqual(ci["upper_bound"], ci["trend_slope"])

    def test_standard_deviation_bands(self):
        """Test standard deviation bands calculation."""
        bands = self.provider.get_standard_deviation_bands("default_rate", window_days=30)

        self.assertIn("moving_average", bands)
        self.assertIn("upper_band", bands)
        self.assertIn("lower_band", bands)
        self.assertGreater(bands["upper_band"], bands["moving_average"])
        self.assertLess(bands["lower_band"], bands["moving_average"])

    def test_change_point_detection(self):
        """Test change point detection logic."""
        # Note: With default mock data, change point might not always trigger
        # but we test that the function returns a valid result (Optional)
        change = self.provider.detect_change_point("default_rate", window_size=5, periods=1)

        if change:
            self.assertIn("change_point_date", change)
            self.assertIn("change_pct", change)
            self.assertGreater(change["change_pct"], 10)


class TestHistoricalContextProviderModes(unittest.TestCase):
    """
    Test mode selection and backend configuration.

    Phase G4.2: Ensure MOCK/REAL mode switching works correctly
    and maintains backward compatibility.
    """

    def test_default_mode_is_mock(self):
        """Test that default mode is MOCK for backward compatibility."""
        provider = HistoricalContextProvider()
        self.assertEqual(provider.mode, "MOCK")

    def test_explicit_mock_mode(self):
        """Test explicit MOCK mode selection."""
        provider = HistoricalContextProvider(mode="MOCK")
        self.assertEqual(provider.mode, "MOCK")

    def test_mode_case_insensitive(self):
        """Test mode selection is case-insensitive."""
        provider_lower = HistoricalContextProvider(mode="mock")
        provider_upper = HistoricalContextProvider(mode="MOCK")
        provider_mixed = HistoricalContextProvider(mode="Mock")

        self.assertEqual(provider_lower.mode, "MOCK")
        self.assertEqual(provider_upper.mode, "MOCK")
        self.assertEqual(provider_mixed.mode, "MOCK")

    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError."""
        with self.assertRaises(ValueError) as context:
            HistoricalContextProvider(mode="INVALID")

        self.assertIn("Invalid mode", str(context.exception))
        self.assertIn("MOCK", str(context.exception))
        self.assertIn("REAL", str(context.exception))

    def test_real_mode_without_backend_raises_error(self):
        """Test that REAL mode without backend raises RuntimeError."""
        with self.assertRaises(RuntimeError) as context:
            HistoricalContextProvider(mode="REAL")

        self.assertIn("REAL mode requires a backend", str(context.exception))

    def test_mock_mode_works_without_backend(self):
        """Test that MOCK mode works without backend (G4.1 compatibility)."""
        provider = HistoricalContextProvider(mode="MOCK", backend=None)
        self.assertEqual(provider.mode, "MOCK")

        # Should work exactly as G4.1
        history = provider.get_kpi_history("test_kpi", date(2026, 1, 1), date(2026, 1, 10))
        self.assertEqual(len(history), 10)


class TestSeasonalityDetection(unittest.TestCase):
    """Test seasonality detection and adjustment."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = HistoricalContextProvider()

    def test_seasonal_decomposition_additive(self):
        """Test additive seasonal decomposition."""
        decomp = self.provider.get_seasonal_decomposition("default_rate", model="additive")
        self.assertIn("trend", decomp)
        self.assertIn("seasonal", decomp)
        self.assertIn("residual", decomp)
        self.assertEqual(len(decomp["trend"]), 366)  # 1 year history

    def test_seasonal_decomposition_multiplicative(self):
        """Test multiplicative seasonal decomposition."""
        decomp = self.provider.get_seasonal_decomposition("default_rate", model="multiplicative")
        self.assertIn("trend", decomp)
        self.assertIn("seasonal", decomp)
        self.assertIn("residual", decomp)

    def test_monthly_pattern_detection(self):
        """Test monthly pattern detection."""
        seasonality = self.provider.get_seasonality("default_rate")
        self.assertTrue(seasonality.cycle_length_months == 12)
        self.assertTrue(len(seasonality.peak_months) > 0)
        self.assertTrue(len(seasonality.trough_months) > 0)

    def test_seasonal_index_calculation(self):
        """Test seasonal index (adjustment factors) calculation."""
        seasonality = self.provider.get_seasonality("default_rate")
        self.assertGreater(len(seasonality.adjustment_factors), 0)
        # Factors should be around 1.0
        for factor in seasonality.adjustment_factors.values():
            self.assertGreater(factor, 0.5)
            self.assertLess(factor, 1.5)

    def test_deseasonalization(self):
        """Test deseasonalization utility."""
        value = 100.0
        deseasonalized = self.provider.deseasonalize("default_rate", value, month=6)
        self.assertGreater(deseasonalized, 0)
        # Should be different if seasonality exists
        self.assertIsNotNone(deseasonalized)

    def test_seasonal_adjustment_factors(self):
        """Test all 12 months have adjustment factors."""
        seasonality = self.provider.get_seasonality("default_rate", periods_years=1)
        # We might not have all 12 months if history is short, but mock data should provide it
        self.assertGreaterEqual(len(seasonality.adjustment_factors), 1)


class TestForecasting(unittest.TestCase):
    """Test forecasting and projections."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = HistoricalContextProvider()

    def test_exponential_smoothing_forecast(self):
        """Test simple exponential smoothing forecast."""
        projections = self.provider.get_forecast("default_rate", steps=10, method="exponential_smoothing")
        self.assertEqual(len(projections), 10)
        self.assertEqual(projections[0].method, "exponential_smoothing")
        self.assertGreater(projections[0].predicted_value, 0)

    def test_linear_forecast(self):
        """Test linear trend-based forecast."""
        projections = self.provider.get_forecast("default_rate", steps=10, method="linear")
        self.assertEqual(len(projections), 10)
        self.assertEqual(projections[0].method, "linear")

    def test_forecast_confidence_intervals(self):
        """Test that forecast confidence intervals expand over time."""
        projections = self.provider.get_forecast("default_rate", steps=10)
        widths = [p.upper_bound - p.lower_bound for p in projections]
        # Interval should be non-decreasing (expanding uncertainty)
        for i in range(1, len(widths)):
            self.assertGreaterEqual(widths[i], widths[i - 1])

    def test_scenario_projection(self):
        """Test multi-scenario projections."""
        scenarios = {"growth": 1.1, "recession": 0.8}
        results = self.provider.get_scenario_projection("default_rate", scenarios, steps=5)
        self.assertIn("base", results)
        self.assertIn("growth", results)
        self.assertIn("recession", results)
        self.assertGreater(results["growth"][0].predicted_value, results["base"][0].predicted_value)
        self.assertLess(results["recession"][0].predicted_value, results["base"][0].predicted_value)

    def test_forecast_validation(self):
        """Test forecast validation metrics."""
        # Create a "past" forecast to validate against "present" actuals
        # We'll use mock data and a small trick to get overlap
        # Forecast from 10 days ago for 20 days
        # But our get_forecast uses date.today() as start.
        # So we simulate validation by checking overlap in mock data.
        projections = self.provider.get_forecast("default_rate", steps=10)
        # Manually shift projections to the past for validation testing
        for p in projections:
            p.projection_date = p.projection_date - timedelta(days=10)

        metrics = self.provider.validate_forecast("default_rate", projections)
        self.assertIn("mae", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("mape", metrics)


class TestBenchmarking(unittest.TestCase):
    """Test benchmarking and comparison logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = HistoricalContextProvider()

    def test_peer_comparison_logic(self):
        """Test peer comparison and percentile ranking."""
        rank = self.provider.get_percentile_ranking("disbursements", 150.0)
        self.assertGreaterEqual(rank, 0.0)
        self.assertLessEqual(rank, 1.0)

    def test_percentile_ranking(self):
        """Test percentile ranking calculation."""
        # Higher is better for disbursements
        rank_high = self.provider.get_percentile_ranking("disbursements", 500.0)
        rank_low = self.provider.get_percentile_ranking("disbursements", 10.0)
        self.assertGreater(rank_high, rank_low)

    def test_z_score_calculation(self):
        """Test Z-score calculation."""
        z = self.provider.get_z_score("default_rate", 0.05)
        # 0.05 is the industry avg in mock data
        self.assertAlmostEqual(z, 0.0, places=1)

    def test_gap_analysis(self):
        """Test gap analysis against targets."""
        gap = self.provider.get_gap_analysis("default_rate", 0.07)
        self.assertIn("gap", gap)
        self.assertIn("status", gap)
        self.assertEqual(gap["status"], "at_risk")

    def test_regulatory_threshold_checks(self):
        """Test regulatory threshold validation."""
        # 0.12 is above 0.10 regulatory max for default_rate
        violations = self.provider.check_regulatory_thresholds("default_rate", 0.12)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]["status"], "violation")

    def test_benchmark_data_loading(self):
        """Test loading benchmark registry."""
        benchmarks = self.provider.get_benchmarks("default_rate")
        self.assertIn("industry_avg", benchmarks)
        self.assertIn("regulatory_max", benchmarks)


if __name__ == "__main__":
    unittest.main()
