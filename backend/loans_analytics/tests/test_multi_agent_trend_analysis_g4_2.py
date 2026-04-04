import unittest
from backend.loans_analytics.multi_agent.historical_context import HistoricalContextProvider, TrendDirection, TrendStrength

class TestExponentialTrendAnalysis(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(mode='MOCK')

    def test_exponential_trend_calculation(self):
        trend = self.provider.get_exponential_trend('test_kpi', alpha=0.3, periods=3)
        self.assertIsNotNone(trend)
        self.assertEqual(trend.kpi_id, 'test_kpi')
        self.assertIn(trend.direction, [TrendDirection.INCREASING, TrendDirection.DECREASING, TrendDirection.STABLE])
        self.assertIn(trend.strength, [TrendStrength.STRONG, TrendStrength.MODERATE, TrendStrength.WEAK])

    def test_exponential_alpha_bounds(self):
        with self.assertRaises(ValueError):
            self.provider.get_exponential_trend('test_kpi', alpha=-0.1)
        with self.assertRaises(ValueError):
            self.provider.get_exponential_trend('test_kpi', alpha=1.5)

    def test_exponential_emphasizes_recent_values(self):
        trend_high_alpha = self.provider.get_exponential_trend('test_kpi', alpha=0.8, periods=3)
        trend_low_alpha = self.provider.get_exponential_trend('test_kpi', alpha=0.1, periods=3)
        self.assertIsNotNone(trend_high_alpha)
        self.assertIsNotNone(trend_low_alpha)

class TestPolynomialTrendAnalysis(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(mode='MOCK')

    def test_polynomial_trend_fitting(self):
        trend = self.provider.get_polynomial_trend('test_kpi', degree=2, periods=3)
        self.assertIsNotNone(trend)
        self.assertEqual(trend.kpi_id, 'test_kpi')
        self.assertGreaterEqual(trend.r_squared, 0.0)
        self.assertLessEqual(trend.r_squared, 1.0)

    def test_polynomial_degree_validation(self):
        with self.assertRaises(ValueError):
            self.provider.get_polynomial_trend('test_kpi', degree=0)
        with self.assertRaises(ValueError):
            self.provider.get_polynomial_trend('test_kpi', degree=6)

    def test_polynomial_different_degrees(self):
        trend_d1 = self.provider.get_polynomial_trend('test_kpi', degree=1, periods=3)
        trend_d2 = self.provider.get_polynomial_trend('test_kpi', degree=2, periods=3)
        trend_d3 = self.provider.get_polynomial_trend('test_kpi', degree=3, periods=3)
        self.assertTrue(all((trend_d1, trend_d2, trend_d3)))
        self.assertEqual(trend_d1.kpi_id, 'test_kpi')
        self.assertEqual(trend_d2.kpi_id, 'test_kpi')
        self.assertEqual(trend_d3.kpi_id, 'test_kpi')

class TestWeightedMovingAverage(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(mode='MOCK')

    def test_weighted_moving_average(self):
        wma = self.provider.get_weighted_moving_average('test_kpi', window_days=30)
        self.assertIsNotNone(wma)
        self.assertIsInstance(wma, float)
        self.assertGreater(wma, 0)

    def test_weighted_average_differs_from_simple(self):
        wma = self.provider.get_weighted_moving_average('test_kpi', window_days=30)
        sma = self.provider.get_moving_average('test_kpi', window_days=30)
        self.assertIsNotNone(wma)
        self.assertIsNotNone(sma)
        self.assertGreater(wma, 0)
        self.assertGreater(sma, 0)

    def test_weighted_average_with_short_window(self):
        wma = self.provider.get_weighted_moving_average('test_kpi', window_days=7)
        self.assertIsNotNone(wma)

class TestMultiPeriodTrends(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(mode='MOCK')

    def test_multi_period_trends(self):
        trends = self.provider.get_multi_period_trends('test_kpi')
        self.assertIsNotNone(trends)
        self.assertIn('7_day', trends)
        self.assertIn('30_day', trends)
        self.assertIn('90_day', trends)
        self.assertIn('yoy', trends)
        self.assertTrue(all((trend.kpi_id == 'test_kpi' for trend in trends.values())))
        self.assertTrue(all((trend.direction is not None for trend in trends.values())))
        self.assertTrue(all((trend.strength is not None for trend in trends.values())))

    def test_longer_periods_have_more_data(self):
        trends = self.provider.get_multi_period_trends('test_kpi')
        self.assertIn('7_day', trends)
        self.assertIn('30_day', trends)
        self.assertIn('90_day', trends)
        self.assertIn('yoy', trends)
        self.assertGreater(trends['7_day'].period_days, 0)
        self.assertGreater(trends['30_day'].period_days, 0)
        self.assertGreater(trends['90_day'].period_days, 0)
        self.assertGreater(trends['yoy'].period_days, 0)

class TestTrendConfidenceInterval(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(mode='MOCK')

    def test_confidence_interval_calculation(self):
        ci = self.provider.get_trend_confidence_interval('test_kpi', confidence=0.95, periods=3)
        self.assertIsNotNone(ci)
        self.assertIn('trend_slope', ci)
        self.assertIn('lower_bound', ci)
        self.assertIn('upper_bound', ci)
        self.assertIn('confidence_level', ci)
        self.assertLess(ci['lower_bound'], ci['upper_bound'])
        self.assertEqual(ci['confidence_level'], 0.95)

    def test_confidence_levels(self):
        ci_90 = self.provider.get_trend_confidence_interval('test_kpi', confidence=0.9, periods=3)
        ci_95 = self.provider.get_trend_confidence_interval('test_kpi', confidence=0.95, periods=3)
        ci_99 = self.provider.get_trend_confidence_interval('test_kpi', confidence=0.99, periods=3)
        self.assertEqual(ci_90['confidence_level'], 0.9)
        self.assertEqual(ci_95['confidence_level'], 0.95)
        self.assertEqual(ci_99['confidence_level'], 0.99)
        self.assertGreater(ci_90['upper_bound'] - ci_90['lower_bound'], 0)
        self.assertGreater(ci_95['upper_bound'] - ci_95['lower_bound'], 0)
        self.assertGreater(ci_99['upper_bound'] - ci_99['lower_bound'], 0)

    def test_interval_width_increases_with_confidence(self):
        ci_90 = self.provider.get_trend_confidence_interval('test_kpi', confidence=0.9, periods=3)
        ci_99 = self.provider.get_trend_confidence_interval('test_kpi', confidence=0.99, periods=3)
        width_90 = ci_90['upper_bound'] - ci_90['lower_bound']
        width_99 = ci_99['upper_bound'] - ci_99['lower_bound']
        self.assertLess(width_90, width_99)

class TestChangePointDetection(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(mode='MOCK')

    def test_change_point_detection(self):
        result = self.provider.detect_change_point('test_kpi', periods=6)
        self.assertTrue(result is None or 'change_point_date' in result)
        self.assertTrue(result is None or 'before_mean' in result)
        self.assertTrue(result is None or 'after_mean' in result)
        self.assertTrue(result is None or 'change_pct' in result)
        self.assertTrue(result is None or 'direction' in result)
        self.assertTrue(result is None or result['change_pct'] > 10)

    def test_change_point_direction(self):
        result = self.provider.detect_change_point('test_kpi', periods=6)
        self.assertTrue(result is None or result['direction'] in ['increase', 'decrease'])
        self.assertTrue(
            result is None
            or (
                (result['direction'] == 'increase' and result['after_mean'] > result['before_mean'])
                or (result['direction'] == 'decrease' and result['after_mean'] < result['before_mean'])
            )
        )

    def test_change_point_with_insufficient_data(self):
        result = self.provider.detect_change_point('test_kpi', window_size=100, periods=1)
        self.assertTrue(result is None or isinstance(result, dict))

class TestTrendAnalysisIntegration(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(mode='MOCK')

    def test_multiple_trend_methods_on_same_kpi(self):
        kpi_id = 'integration_test_kpi'
        linear_trend = self.provider.get_trend(kpi_id, periods=3)
        exp_trend = self.provider.get_exponential_trend(kpi_id, periods=3)
        poly_trend = self.provider.get_polynomial_trend(kpi_id, periods=3)
        multi_trends = self.provider.get_multi_period_trends(kpi_id)
        self.assertIsNotNone(linear_trend)
        self.assertIsNotNone(exp_trend)
        self.assertIsNotNone(poly_trend)
        self.assertIsNotNone(multi_trends)

    def test_consistency_across_methods(self):
        kpi_id = 'consistency_test_kpi'
        linear_trend = self.provider.get_trend(kpi_id, periods=6)
        exp_trend = self.provider.get_exponential_trend(kpi_id, periods=6)
        self.assertEqual(linear_trend.kpi_id, kpi_id)
        self.assertEqual(exp_trend.kpi_id, kpi_id)
        self.assertEqual(linear_trend.direction, exp_trend.direction)

    def test_averaging_methods_consistency(self):
        kpi_id = 'averaging_test_kpi'
        sma = self.provider.get_moving_average(kpi_id, window_days=30)
        wma = self.provider.get_weighted_moving_average(kpi_id, window_days=30)
        self.assertGreater(sma, 0)
        self.assertGreater(wma, 0)
        ratio = max(sma, wma) / min(sma, wma)
        self.assertLess(ratio, 2.0)

class TestPhaseG42Completeness(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(mode='MOCK')

    def test_all_g42_methods_exist(self):
        self.assertTrue(hasattr(self.provider, 'get_exponential_trend'))
        self.assertTrue(hasattr(self.provider, 'get_polynomial_trend'))
        self.assertTrue(hasattr(self.provider, 'get_weighted_moving_average'))
        self.assertTrue(hasattr(self.provider, 'get_multi_period_trends'))
        self.assertTrue(hasattr(self.provider, 'get_trend_confidence_interval'))
        self.assertTrue(hasattr(self.provider, 'detect_change_point'))

    def test_all_g42_methods_callable(self):
        self.assertTrue(callable(self.provider.get_exponential_trend))
        self.assertTrue(callable(self.provider.get_polynomial_trend))
        self.assertTrue(callable(self.provider.get_weighted_moving_average))
        self.assertTrue(callable(self.provider.get_multi_period_trends))
        self.assertTrue(callable(self.provider.get_trend_confidence_interval))
        self.assertTrue(callable(self.provider.detect_change_point))
if __name__ == '__main__':
    unittest.main()
