import unittest
from datetime import date, timedelta
from backend.python.multi_agent.historical_context import HistoricalContextProvider, KpiProjection, TrendDirection, TrendStrength

class EmptyHistoricalBackend:

    def get_kpi_history(self, kpi_id: str, start_date: date, end_date: date):
        return []

class TestHistoricalContextProvider(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(cache_ttl_seconds=60)

    def test_get_kpi_history(self):
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)
        history = self.provider.get_kpi_history('default_rate', start_date, end_date)
        self.assertIsNotNone(history)
        self.assertEqual(len(history), 31)
        self.assertEqual(history[0].kpi_id, 'default_rate')
        self.assertEqual(history[0].date, start_date)
        self.assertEqual(history[-1].date, end_date)

    def test_get_kpi_history_empty_range(self):
        start_date = date(2026, 1, 31)
        end_date = date(2026, 1, 1)
        history = self.provider.get_kpi_history('default_rate', start_date, end_date)
        self.assertEqual(len(history), 0)

    def test_get_kpi_history_single_day(self):
        target_date = date(2026, 1, 15)
        history = self.provider.get_kpi_history('default_rate', target_date, target_date)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].date, target_date)

    def test_calculate_trend_increasing(self):
        trend = self.provider.get_trend('default_rate', periods=3)
        self.assertEqual(trend.kpi_id, 'default_rate')
        self.assertEqual(trend.direction, TrendDirection.INCREASING)
        self.assertGreater(trend.slope, 0)
        self.assertGreater(trend.end_value, trend.start_value)
        self.assertGreater(trend.percent_change, 0)

    def test_calculate_trend_with_custom_period(self):
        trend_3m = self.provider.get_trend('default_rate', periods=3)
        trend_6m = self.provider.get_trend('default_rate', periods=6)
        self.assertLess(trend_3m.period_days, trend_6m.period_days)
        self.assertIsNotNone(trend_3m.r_squared)
        self.assertIsNotNone(trend_6m.r_squared)

    def test_trend_strength_classification(self):
        trend = self.provider.get_trend('default_rate', periods=3)
        self.assertIn(trend.strength, [TrendStrength.STRONG, TrendStrength.MODERATE, TrendStrength.WEAK])
        self.assertGreaterEqual(trend.r_squared, 0.0)
        self.assertLessEqual(trend.r_squared, 1.0)

    def test_get_moving_average(self):
        ma_30 = self.provider.get_moving_average('default_rate', window_days=30)
        ma_7 = self.provider.get_moving_average('default_rate', window_days=7)
        self.assertIsNotNone(ma_30)
        self.assertIsNotNone(ma_7)
        self.assertGreater(ma_30, 0)
        self.assertGreater(ma_7, 0)

    def test_moving_average_different_windows(self):
        ma_7 = self.provider.get_moving_average('default_rate', window_days=7)
        ma_30 = self.provider.get_moving_average('default_rate', window_days=30)
        ma_90 = self.provider.get_moving_average('default_rate', window_days=90)
        self.assertIsNotNone(ma_7)
        self.assertIsNotNone(ma_30)
        self.assertIsNotNone(ma_90)

    def test_historical_cache_efficiency(self):
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)
        history1 = self.provider.get_kpi_history('default_rate', start_date, end_date)
        history2 = self.provider.get_kpi_history('default_rate', start_date, end_date)
        self.assertEqual(len(history1), len(history2))
        self.assertEqual(history1[0].date, history2[0].date)
        self.assertEqual(history1[0].value, history2[0].value)

    def test_cache_clear(self):
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)
        self.provider.get_kpi_history('default_rate', start_date, end_date)
        self.assertGreater(len(self.provider._cache), 0)
        self.provider.clear_cache()
        self.assertEqual(len(self.provider._cache), 0)

    def test_multiple_kpis(self):
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 10)
        history1 = self.provider.get_kpi_history('default_rate', start_date, end_date)
        history2 = self.provider.get_kpi_history('disbursements', start_date, end_date)
        self.assertEqual(len(history1), 10)
        self.assertEqual(len(history2), 10)
        self.assertNotEqual(history1[0].value, history2[0].value)

class TestTrendAnalysis(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider()

    def test_trend_analysis_fields(self):
        trend = self.provider.get_trend('default_rate', periods=3)
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
        trend = self.provider.get_trend('default_rate', periods=6)
        self.assertGreaterEqual(trend.r_squared, 0.0)
        self.assertLessEqual(trend.r_squared, 1.0)

    def test_trend_percent_change_calculation(self):
        trend = self.provider.get_trend('default_rate', periods=3)
        expected_pct = (trend.end_value - trend.start_value) / trend.start_value * 100
        self.assertAlmostEqual(trend.percent_change, expected_pct, places=2)

    def test_exponential_trend_calculation(self):
        trend = self.provider.get_exponential_trend('default_rate', alpha=0.3, periods=3)
        self.assertIsNotNone(trend)
        self.assertEqual(trend.direction, TrendDirection.INCREASING)
        self.assertGreater(trend.slope, 0)

    def test_polynomial_trend_fitting(self):
        trend = self.provider.get_polynomial_trend('default_rate', degree=2, periods=3)
        self.assertIsNotNone(trend)
        self.assertIn(trend.direction, [TrendDirection.INCREASING, TrendDirection.DECREASING])
        self.assertGreaterEqual(trend.r_squared, 0.0)

    def test_weighted_moving_average(self):
        wma = self.provider.get_weighted_moving_average('default_rate', window_days=30)
        ma = self.provider.get_moving_average('default_rate', window_days=30)
        self.assertIsNotNone(wma)
        self.assertIsNotNone(ma)
        self.assertNotEqual(wma, ma)

    def test_multi_period_trends(self):
        trends = self.provider.get_multi_period_trends('default_rate')
        self.assertIn('7_day', trends)
        self.assertIn('30_day', trends)
        self.assertIn('90_day', trends)
        self.assertIn('yoy', trends)

    def test_trend_confidence_intervals(self):
        ci = self.provider.get_trend_confidence_interval('default_rate', confidence=0.95)
        self.assertIn('trend_slope', ci)
        self.assertIn('lower_bound', ci)
        self.assertIn('upper_bound', ci)
        self.assertLessEqual(ci['lower_bound'], ci['trend_slope'])
        self.assertGreaterEqual(ci['upper_bound'], ci['trend_slope'])

    def test_standard_deviation_bands(self):
        bands = self.provider.get_standard_deviation_bands('default_rate', window_days=30)
        self.assertIn('moving_average', bands)
        self.assertIn('upper_band', bands)
        self.assertIn('lower_band', bands)
        self.assertGreater(bands['upper_band'], bands['moving_average'])
        self.assertLess(bands['lower_band'], bands['moving_average'])

    def test_change_point_detection(self):
        change = self.provider.detect_change_point('default_rate', window_size=5, periods=1)
        if change:
            self.assertIn('change_point_date', change)
            self.assertIn('change_pct', change)
            self.assertGreater(change['change_pct'], 10)

class TestHistoricalContextProviderModes(unittest.TestCase):

    def test_default_mode_is_mock(self):
        provider = HistoricalContextProvider()
        self.assertEqual(provider.mode, 'MOCK')

    def test_explicit_mock_mode(self):
        provider = HistoricalContextProvider(mode='MOCK')
        self.assertEqual(provider.mode, 'MOCK')

    def test_mode_case_insensitive(self):
        provider_lower = HistoricalContextProvider(mode='mock')
        provider_upper = HistoricalContextProvider(mode='MOCK')
        provider_mixed = HistoricalContextProvider(mode='Mock')
        self.assertEqual(provider_lower.mode, 'MOCK')
        self.assertEqual(provider_upper.mode, 'MOCK')
        self.assertEqual(provider_mixed.mode, 'MOCK')

    def test_invalid_mode_raises_error(self):
        with self.assertRaises(ValueError) as context:
            HistoricalContextProvider(mode='INVALID')
        self.assertIn('Invalid mode', str(context.exception))
        self.assertIn('MOCK', str(context.exception))
        self.assertIn('REAL', str(context.exception))

    def test_real_mode_without_backend_raises_error(self):
        with self.assertRaises(RuntimeError) as context:
            HistoricalContextProvider(mode='REAL')
        self.assertIn('REAL mode requires a backend', str(context.exception))

    def test_mock_mode_works_without_backend(self):
        provider = HistoricalContextProvider(mode='MOCK', backend=None)
        self.assertEqual(provider.mode, 'MOCK')
        history = provider.get_kpi_history('test_kpi', date(2026, 1, 1), date(2026, 1, 10))
        self.assertEqual(len(history), 10)

class TestSeasonalityDetection(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider()

    def test_seasonal_decomposition_additive(self):
        decomp = self.provider.get_seasonal_decomposition('default_rate', model='additive')
        self.assertIn('trend', decomp)
        self.assertIn('seasonal', decomp)
        self.assertIn('residual', decomp)
        self.assertEqual(len(decomp['trend']), 366)

    def test_seasonal_decomposition_multiplicative(self):
        decomp = self.provider.get_seasonal_decomposition('default_rate', model='multiplicative')
        self.assertIn('trend', decomp)
        self.assertIn('seasonal', decomp)
        self.assertIn('residual', decomp)

    def test_monthly_pattern_detection(self):
        seasonality = self.provider.get_seasonality('default_rate')
        self.assertEqual(seasonality.cycle_length_months, 12)
        self.assertGreater(len(seasonality.peak_months), 0)
        self.assertGreater(len(seasonality.trough_months), 0)

    def test_seasonal_index_calculation(self):
        seasonality = self.provider.get_seasonality('default_rate')
        self.assertGreater(len(seasonality.adjustment_factors), 0)
        for factor in seasonality.adjustment_factors.values():
            self.assertGreater(factor, 0.5)
            self.assertLess(factor, 1.5)

    def test_deseasonalization(self):
        value = 100.0
        deseasonalized = self.provider.deseasonalize('default_rate', value, month=6)
        self.assertGreater(deseasonalized, 0)
        self.assertIsNotNone(deseasonalized)

    def test_seasonal_adjustment_factors(self):
        seasonality = self.provider.get_seasonality('default_rate', periods_years=1)
        self.assertGreaterEqual(len(seasonality.adjustment_factors), 1)

class TestForecasting(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider()

    def test_exponential_smoothing_forecast(self):
        projections = self.provider.get_forecast('default_rate', steps=10, method='exponential_smoothing')
        self.assertEqual(len(projections), 10)
        self.assertEqual(projections[0].method, 'exponential_smoothing')
        self.assertGreater(projections[0].predicted_value, 0)

    def test_linear_forecast(self):
        projections = self.provider.get_forecast('default_rate', steps=10, method='linear')
        self.assertEqual(len(projections), 10)
        self.assertEqual(projections[0].method, 'linear')

    def test_arima_forecasting(self):
        projections = self.provider.get_forecast('default_rate', steps=10, method='arima')
        self.assertEqual(len(projections), 10)
        self.assertEqual(projections[0].method, 'arima')
        self.assertGreater(projections[0].predicted_value, 0)

    def test_forecast_confidence_intervals(self):
        projections = self.provider.get_forecast('default_rate', steps=10)
        widths = [p.upper_bound - p.lower_bound for p in projections]
        for i in range(1, len(widths)):
            self.assertGreaterEqual(widths[i], widths[i - 1])

    def test_scenario_projection(self):
        scenarios = {'growth': 1.1, 'recession': 0.8}
        results = self.provider.get_scenario_projection('default_rate', scenarios, steps=5)
        self.assertIn('base', results)
        self.assertIn('growth', results)
        self.assertIn('recession', results)
        self.assertGreater(results['growth'][0].predicted_value, results['base'][0].predicted_value)
        self.assertLess(results['recession'][0].predicted_value, results['base'][0].predicted_value)

    def test_forecast_validation(self):
        projections = self.provider.get_forecast('default_rate', steps=10)
        for p in projections:
            p.projection_date = p.projection_date - timedelta(days=10)
        metrics = self.provider.validate_forecast('default_rate', projections)
        self.assertIn('mae', metrics)
        self.assertIn('rmse', metrics)
        self.assertIn('mape', metrics)

    def test_forecast_accuracy_metrics(self):
        projections = self.provider.get_forecast('default_rate', steps=7, method='exponential_smoothing')
        for p in projections:
            p.projection_date = p.projection_date - timedelta(days=7)
        metrics = self.provider.validate_forecast('default_rate', projections)
        self.assertIn('mae', metrics)
        self.assertIn('rmse', metrics)
        self.assertIn('mape', metrics)
        self.assertIn('bias', metrics)
        self.assertGreaterEqual(metrics['mae'], 0.0)
        self.assertGreaterEqual(metrics['rmse'], 0.0)
        self.assertGreaterEqual(metrics['mape'], 0.0)

    def test_validate_forecast_empty_projections_raises(self):
        with self.assertRaises(ValueError) as context:
            self.provider.validate_forecast('default_rate', [])
        self.assertIn('empty projections', str(context.exception))

class TestHistoricalContextFailFast(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider(mode='REAL', backend=EmptyHistoricalBackend())

    def test_standard_deviation_bands_without_history_raises(self):
        with self.assertRaises(ValueError) as context:
            self.provider.get_standard_deviation_bands('default_rate', window_days=30)
        self.assertIn('No historical data available', str(context.exception))

    def test_validate_forecast_without_actuals_raises(self):
        projections = [KpiProjection(kpi_id='default_rate', projection_date=date.today() - timedelta(days=1), predicted_value=100.0, lower_bound=95.0, upper_bound=105.0, confidence_level=0.95, method='linear')]
        with self.assertRaises(ValueError) as context:
            self.provider.validate_forecast('default_rate', projections)
        self.assertIn('No actual values available', str(context.exception))

class TestBenchmarking(unittest.TestCase):

    def setUp(self):
        self.provider = HistoricalContextProvider()

    def test_peer_comparison_logic(self):
        rank = self.provider.get_percentile_ranking('disbursements', 150.0)
        self.assertGreaterEqual(rank, 0.0)
        self.assertLessEqual(rank, 1.0)

    def test_percentile_ranking(self):
        rank_high = self.provider.get_percentile_ranking('disbursements', 500.0)
        rank_low = self.provider.get_percentile_ranking('disbursements', 10.0)
        self.assertGreater(rank_high, rank_low)

    def test_z_score_calculation(self):
        z = self.provider.get_z_score('default_rate', 0.05)
        self.assertAlmostEqual(z, 0.0, places=1)

    def test_gap_analysis(self):
        gap = self.provider.get_gap_analysis('default_rate', 0.07)
        self.assertIn('gap', gap)
        self.assertIn('status', gap)
        self.assertEqual(gap['status'], 'at_risk')

    def test_regulatory_threshold_checks(self):
        violations = self.provider.check_regulatory_thresholds('default_rate', 0.12)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0]['status'], 'violation')

    def test_benchmark_data_loading(self):
        benchmarks = self.provider.get_benchmarks('default_rate')
        self.assertIn('industry_avg', benchmarks)
        self.assertIn('regulatory_max', benchmarks)
if __name__ == '__main__':
    unittest.main()
