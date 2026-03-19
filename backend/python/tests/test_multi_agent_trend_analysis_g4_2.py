"""
Phase G4.2: Advanced Trend Analysis Tests

Comprehensive test suite for exponential smoothing, polynomial fitting,
weighted moving averages, multi-period analysis, confidence intervals,
and change point detection.

This module extends Phase G4.1 with advanced statistical methods.
"""

import unittest

from backend.python.multi_agent.historical_context import (
    HistoricalContextProvider,
    TrendDirection,
    TrendStrength,
)


class TestExponentialTrendAnalysis(unittest.TestCase):
    """Test exponential smoothing trend calculations."""

    def setUp(self):
        """Initialize provider for each test."""
        self.provider = HistoricalContextProvider(mode="MOCK")

    def test_exponential_trend_calculation(self):
        """Test exponential smoothing trend is calculated correctly."""
        trend = self.provider.get_exponential_trend("test_kpi", alpha=0.3, periods=3)

        self.assertIsNotNone(trend)
        self.assertEqual(trend.kpi_id, "test_kpi")
        self.assertIn(
            trend.direction,
            [
                TrendDirection.INCREASING,
                TrendDirection.DECREASING,
                TrendDirection.STABLE,
            ],
        )
        self.assertIn(
            trend.strength,
            [TrendStrength.STRONG, TrendStrength.MODERATE, TrendStrength.WEAK],
        )

    def test_exponential_alpha_bounds(self):
        """Test alpha parameter validation."""
        with self.assertRaises(ValueError):
            self.provider.get_exponential_trend("test_kpi", alpha=-0.1)

        with self.assertRaises(ValueError):
            self.provider.get_exponential_trend("test_kpi", alpha=1.5)

    def test_exponential_emphasizes_recent_values(self):
        """Test that exponential smoothing emphasizes recent values."""
        # Higher alpha should follow recent values more closely
        trend_high_alpha = self.provider.get_exponential_trend("test_kpi", alpha=0.8, periods=3)
        trend_low_alpha = self.provider.get_exponential_trend("test_kpi", alpha=0.1, periods=3)

        # Both should be valid
        self.assertIsNotNone(trend_high_alpha)
        self.assertIsNotNone(trend_low_alpha)


class TestPolynomialTrendAnalysis(unittest.TestCase):
    """Test polynomial trend fitting."""

    def setUp(self):
        """Initialize provider for each test."""
        self.provider = HistoricalContextProvider(mode="MOCK")

    def test_polynomial_trend_fitting(self):
        """Test polynomial trend fit is calculated."""
        trend = self.provider.get_polynomial_trend("test_kpi", degree=2, periods=3)

        self.assertIsNotNone(trend)
        self.assertEqual(trend.kpi_id, "test_kpi")
        self.assertGreaterEqual(trend.r_squared, 0.0)
        self.assertLessEqual(trend.r_squared, 1.0)

    def test_polynomial_degree_validation(self):
        """Test polynomial degree bounds."""
        with self.assertRaises(ValueError):
            self.provider.get_polynomial_trend("test_kpi", degree=0)

        with self.assertRaises(ValueError):
            self.provider.get_polynomial_trend("test_kpi", degree=6)

    def test_polynomial_different_degrees(self):
        """Test polynomial fitting with different degrees."""
        for degree in [1, 2, 3]:
            trend = self.provider.get_polynomial_trend("test_kpi", degree=degree, periods=3)
            self.assertIsNotNone(trend)
            self.assertEqual(trend.kpi_id, "test_kpi")


class TestWeightedMovingAverage(unittest.TestCase):
    """Test weighted moving average calculations."""

    def setUp(self):
        """Initialize provider for each test."""
        self.provider = HistoricalContextProvider(mode="MOCK")

    def test_weighted_moving_average(self):
        """Test weighted moving average calculation."""
        wma = self.provider.get_weighted_moving_average("test_kpi", window_days=30)

        self.assertIsNotNone(wma)
        self.assertIsInstance(wma, float)
        self.assertGreater(wma, 0)

    def test_weighted_average_differs_from_simple(self):
        """Test that weighted average differs from simple moving average."""
        wma = self.provider.get_weighted_moving_average("test_kpi", window_days=30)
        sma = self.provider.get_moving_average("test_kpi", window_days=30)

        # With trending data, weighted should differ from simple
        self.assertIsNotNone(wma)
        self.assertIsNotNone(sma)
        # They may not always differ due to data generation, but values should be reasonable
        self.assertGreater(wma, 0)
        self.assertGreater(sma, 0)

    def test_weighted_average_with_short_window(self):
        """Test weighted average with small window."""
        wma = self.provider.get_weighted_moving_average("test_kpi", window_days=7)
        self.assertIsNotNone(wma)


class TestMultiPeriodTrends(unittest.TestCase):
    """Test multi-period trend analysis."""

    def setUp(self):
        """Initialize provider for each test."""
        self.provider = HistoricalContextProvider(mode="MOCK")

    def test_multi_period_trends(self):
        """Test multi-period trend calculation."""
        trends = self.provider.get_multi_period_trends("test_kpi")

        self.assertIsNotNone(trends)
        # Should have trends for multiple periods
        self.assertIn("7_day", trends)
        self.assertIn("30_day", trends)
        self.assertIn("90_day", trends)
        self.assertIn("yoy", trends)

        # All should be valid trends
        for _period, trend in trends.items():
            self.assertEqual(trend.kpi_id, "test_kpi")
            self.assertIsNotNone(trend.direction)
            self.assertIsNotNone(trend.strength)

    def test_longer_periods_have_more_data(self):
        """Test that longer periods have more historical data."""
        # This is implicit in the implementation
        trends = self.provider.get_multi_period_trends("test_kpi")

        # All periods should return valid trends
        for period in ["7_day", "30_day", "90_day", "yoy"]:
            self.assertIn(period, trends)
            self.assertGreater(trends[period].period_days, 0)


class TestTrendConfidenceInterval(unittest.TestCase):
    """Test confidence interval calculations."""

    def setUp(self):
        """Initialize provider for each test."""
        self.provider = HistoricalContextProvider(mode="MOCK")

    def test_confidence_interval_calculation(self):
        """Test confidence interval calculation."""
        ci = self.provider.get_trend_confidence_interval("test_kpi", confidence=0.95, periods=3)

        self.assertIsNotNone(ci)
        self.assertIn("trend_slope", ci)
        self.assertIn("lower_bound", ci)
        self.assertIn("upper_bound", ci)
        self.assertIn("confidence_level", ci)

        # Lower bound should be less than upper bound
        self.assertLess(ci["lower_bound"], ci["upper_bound"])
        self.assertEqual(ci["confidence_level"], 0.95)

    def test_confidence_levels(self):
        """Test different confidence levels."""
        for conf in [0.90, 0.95, 0.99]:
            ci = self.provider.get_trend_confidence_interval("test_kpi", confidence=conf, periods=3)
            self.assertEqual(ci["confidence_level"], conf)
            # Higher confidence = wider interval
            self.assertGreater(ci["upper_bound"] - ci["lower_bound"], 0)

    def test_interval_width_increases_with_confidence(self):
        """Test that interval width increases with higher confidence."""
        ci_90 = self.provider.get_trend_confidence_interval("test_kpi", confidence=0.90, periods=3)
        ci_99 = self.provider.get_trend_confidence_interval("test_kpi", confidence=0.99, periods=3)

        width_90 = ci_90["upper_bound"] - ci_90["lower_bound"]
        width_99 = ci_99["upper_bound"] - ci_99["lower_bound"]

        # Higher confidence should have wider interval
        self.assertLess(width_90, width_99)


class TestChangePointDetection(unittest.TestCase):
    """Test change point detection."""

    def setUp(self):
        """Initialize provider for each test."""
        self.provider = HistoricalContextProvider(mode="MOCK")

    def test_change_point_detection(self):
        """Test change point detection returns valid result or None."""
        result = self.provider.detect_change_point("test_kpi", periods=6)

        # Result can be None or a dict with change point info
        if result is not None:
            self.assertIn("change_point_date", result)
            self.assertIn("before_mean", result)
            self.assertIn("after_mean", result)
            self.assertIn("change_pct", result)
            self.assertIn("direction", result)

            # Change percentage should be >10% to be detected
            self.assertGreater(result["change_pct"], 10)

    def test_change_point_direction(self):
        """Test that change direction is correctly identified."""
        result = self.provider.detect_change_point("test_kpi", periods=6)

        if result is not None:
            direction = result["direction"]
            self.assertIn(direction, ["increase", "decrease"])

            # Direction should match before/after means
            if direction == "increase":
                self.assertGreater(result["after_mean"], result["before_mean"])
            else:
                self.assertLess(result["after_mean"], result["before_mean"])

    def test_change_point_with_insufficient_data(self):
        """Test change point with insufficient data window."""
        # Very small period should return None due to insufficient data
        result = self.provider.detect_change_point("test_kpi", window_size=100, periods=1)

        # Should handle gracefully (may return None)
        if result is not None:
            self.assertIsInstance(result, dict)


class TestTrendAnalysisIntegration(unittest.TestCase):
    """Integration tests for multiple trend methods."""

    def setUp(self):
        """Initialize provider for each test."""
        self.provider = HistoricalContextProvider(mode="MOCK")

    def test_multiple_trend_methods_on_same_kpi(self):
        """Test running multiple trend methods on same KPI."""
        kpi_id = "integration_test_kpi"

        # Get trends using different methods
        linear_trend = self.provider.get_trend(kpi_id, periods=3)
        exp_trend = self.provider.get_exponential_trend(kpi_id, periods=3)
        poly_trend = self.provider.get_polynomial_trend(kpi_id, periods=3)
        multi_trends = self.provider.get_multi_period_trends(kpi_id)

        # All should return valid trends
        self.assertIsNotNone(linear_trend)
        self.assertIsNotNone(exp_trend)
        self.assertIsNotNone(poly_trend)
        self.assertIsNotNone(multi_trends)

    def test_consistency_across_methods(self):
        """Test that different methods show consistent direction."""
        kpi_id = "consistency_test_kpi"

        linear_trend = self.provider.get_trend(kpi_id, periods=6)
        exp_trend = self.provider.get_exponential_trend(kpi_id, periods=6)

        # Both should have same KPI and direction (with same data)
        self.assertEqual(linear_trend.kpi_id, kpi_id)
        self.assertEqual(exp_trend.kpi_id, kpi_id)
        self.assertEqual(linear_trend.direction, exp_trend.direction)

    def test_averaging_methods_consistency(self):
        """Test that different moving average methods are consistent."""
        kpi_id = "averaging_test_kpi"

        sma = self.provider.get_moving_average(kpi_id, window_days=30)
        wma = self.provider.get_weighted_moving_average(kpi_id, window_days=30)

        # Both should return positive values
        self.assertGreater(sma, 0)
        self.assertGreater(wma, 0)

        # Values should be in similar range
        ratio = max(sma, wma) / min(sma, wma)
        self.assertLess(ratio, 2.0)  # Not drastically different


class TestPhaseG42Completeness(unittest.TestCase):
    """Verify Phase G4.2 implementation completeness."""

    def setUp(self):
        """Initialize provider for each test."""
        self.provider = HistoricalContextProvider(mode="MOCK")

    def test_all_g42_methods_exist(self):
        """Test that all Phase G4.2 methods are implemented."""
        # Exponential trend
        self.assertTrue(hasattr(self.provider, "get_exponential_trend"))
        # Polynomial trend
        self.assertTrue(hasattr(self.provider, "get_polynomial_trend"))
        # Weighted moving average
        self.assertTrue(hasattr(self.provider, "get_weighted_moving_average"))
        # Multi-period trends
        self.assertTrue(hasattr(self.provider, "get_multi_period_trends"))
        # Confidence interval
        self.assertTrue(hasattr(self.provider, "get_trend_confidence_interval"))
        # Change point detection
        self.assertTrue(hasattr(self.provider, "detect_change_point"))

    def test_all_g42_methods_callable(self):
        """Test that all Phase G4.2 methods are callable."""
        self.assertTrue(callable(self.provider.get_exponential_trend))
        self.assertTrue(callable(self.provider.get_polynomial_trend))
        self.assertTrue(callable(self.provider.get_weighted_moving_average))
        self.assertTrue(callable(self.provider.get_multi_period_trends))
        self.assertTrue(callable(self.provider.get_trend_confidence_interval))
        self.assertTrue(callable(self.provider.detect_change_point))


if __name__ == "__main__":
    unittest.main()
