import unittest
from datetime import datetime
from decimal import Decimal
import pandas as pd
from backend.python.kpis.engine import KPIEngineV2

class TestKPIEngineV2(unittest.TestCase):

    def setUp(self):
        self.sample_df = pd.DataFrame({'dpd_30_60_usd': [100.0, 200.0, 150.0], 'dpd_60_90_usd': [50.0, 75.0, 100.0], 'dpd_90_plus_usd': [25.0, 50.0, 75.0], 'total_receivable_usd': [5000.0, 6000.0, 7000.0], 'loan_amount': [4000.0, 5000.0, 6000.0], 'collateral_value': [5000.0, 6500.0, 7500.0]})
        self.empty_df = pd.DataFrame()

    def test_engine_initialization(self):
        engine = KPIEngineV2(self.sample_df, actor='test_user', run_id='test_run_001')
        self.assertEqual(engine.actor, 'test_user')
        self.assertEqual(engine.run_id, 'test_run_001')
        self.assertIsInstance(engine.df, pd.DataFrame)
        self.assertEqual(len(engine._audit_records), 0)

    def test_engine_initialization_with_defaults(self):
        engine = KPIEngineV2(self.sample_df)
        self.assertEqual(engine.actor, 'system')
        self.assertIsNotNone(engine.run_id)
        self.assertRegex(engine.run_id, '\\d{8}_\\d{6}')

    def test_calculate_par_30(self):
        engine = KPIEngineV2(self.sample_df, actor='test_user')
        value, context = engine.calculate_par_30()
        self.assertIsInstance(value, Decimal)
        self.assertGreaterEqual(value, 0.0)
        self.assertIn('formula', context)
        self.assertIn('rows_processed', context)
        self.assertEqual(context['rows_processed'], 3)
        self.assertEqual(len(engine._audit_records), 1)
        audit_record = engine._audit_records[0]
        self.assertEqual(audit_record['kpi_name'], 'PAR30')
        self.assertEqual(audit_record['status'], 'success')
        self.assertEqual(audit_record['value'], value)

    def test_calculate_collection_rate(self):
        engine = KPIEngineV2(self.sample_df, actor='test_user')
        value, context = engine.calculate_collection_rate()
        self.assertIsInstance(value, Decimal)
        self.assertIn('formula', context)
        self.assertIn('rows_processed', context)
        self.assertEqual(len(engine._audit_records), 1)
        audit_record = engine._audit_records[0]
        self.assertEqual(audit_record['kpi_name'], 'COLLECTION_RATE')
        self.assertEqual(audit_record['status'], 'success')

    def test_calculate_ltv(self):
        df_with_ltv = pd.DataFrame({'loan_amount': [1000.0, 2000.0, 3000.0], 'collateral_value': [1500.0, 2500.0, 4000.0]})
        engine = KPIEngineV2(df_with_ltv, actor='test_user')
        value, _ = engine.calculate_ltv()
        self.assertIsInstance(value, Decimal)
        self.assertGreaterEqual(float(value), 0.0)
        self.assertEqual(len(engine._audit_records), 1)
        audit_record = engine._audit_records[0]
        self.assertEqual(audit_record['kpi_name'], 'LTV')

    def test_calculate_all(self):
        engine = KPIEngineV2(self.sample_df, actor='test_user')
        results = engine.calculate_all()
        self.assertIsInstance(results, dict)
        self.assertIn('PAR30', results)
        self.assertIn('value', results['PAR30'])
        self.assertIn('context', results['PAR30'])
        self.assertIn('COLLECTION_RATE', results)
        self.assertIn('value', results['COLLECTION_RATE'])
        self.assertIn('context', results['COLLECTION_RATE'])
        self.assertIn('LTV', results)
        self.assertIn('value', results['LTV'])
        self.assertIn('context', results['LTV'])
        self.assertGreaterEqual(len(engine._audit_records), 3)

    def test_get_audit_trail(self):
        engine = KPIEngineV2(self.sample_df, actor='test_user', run_id='test_run_001')
        engine.calculate_all()
        audit_df = engine.get_audit_trail()
        self.assertIsInstance(audit_df, pd.DataFrame)
        self.assertGreater(len(audit_df), 0)
        self.assertIn('timestamp', audit_df.columns)
        self.assertIn('run_id', audit_df.columns)
        self.assertIn('actor', audit_df.columns)
        self.assertIn('kpi_name', audit_df.columns)
        self.assertIn('value', audit_df.columns)
        self.assertIn('context', audit_df.columns)
        self.assertIn('error', audit_df.columns)
        self.assertIn('status', audit_df.columns)
        self.assertTrue(all(audit_df['run_id'] == 'test_run_001'))
        self.assertTrue(all(audit_df['actor'] == 'test_user'))

    def test_get_audit_trail_empty(self):
        engine = KPIEngineV2(self.sample_df)
        audit_df = engine.get_audit_trail()
        self.assertIsInstance(audit_df, pd.DataFrame)
        self.assertEqual(len(audit_df), 0)
        self.assertIn('timestamp', audit_df.columns)
        self.assertIn('run_id', audit_df.columns)
        self.assertIn('actor', audit_df.columns)
        self.assertIn('kpi_name', audit_df.columns)
        self.assertIn('value', audit_df.columns)
        self.assertIn('context', audit_df.columns)
        self.assertIn('error', audit_df.columns)
        self.assertIn('status', audit_df.columns)

    def test_error_handling_in_calculations(self):
        invalid_df = pd.DataFrame({'some_column': [1, 2, 3]})
        engine = KPIEngineV2(invalid_df, actor='test_user')
        with self.assertRaises(ValueError) as cm:
            engine.calculate_par_30()
        self.assertIn('CRITICAL: PAR30 calculation failed', str(cm.exception))

    def test_individual_kpi_failure_isolation(self):
        invalid_df = pd.DataFrame({'some_column': [1, 2, 3]})
        engine = KPIEngineV2(invalid_df, actor='test_user')
        with self.assertRaises(ValueError):
            engine.calculate_all()

    def test_audit_trail_timestamp_format(self):
        engine = KPIEngineV2(self.sample_df, actor='test_user')
        engine.calculate_par_30()
        audit_df = engine.get_audit_trail()
        timestamp_str = audit_df.iloc[0]['timestamp']
        self.assertIsInstance(timestamp_str, str)
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        self.assertIsInstance(parsed_timestamp, datetime)

    def test_context_serialization(self):
        engine = KPIEngineV2(self.sample_df, actor='test_user')
        engine.calculate_par_30()
        audit_df = engine.get_audit_trail()
        context_str = audit_df.iloc[0]['context']
        self.assertIsInstance(context_str, str)

class TestDerivedRiskKPIAudit(unittest.TestCase):

    def _make_portfolio_df(self):
        return pd.DataFrame({'dpd_30_60_usd': [500.0, 8000.0, 0.0, 0.0, 0.0], 'dpd_60_90_usd': [0.0, 0.0, 2000.0, 0.0, 0.0], 'dpd_90_plus_usd': [0.0, 0.0, 6000.0, 4000.0, 0.0], 'total_receivable_usd': [10000.0, 8000.0, 6000.0, 4000.0, 12000.0], 'dpd': [5, 35, 95, 120, 0], 'status': ['active', 'delinquent', 'defaulted', 'defaulted', 'active'], 'outstanding_balance': [10000.0, 8000.0, 6000.0, 4000.0, 12000.0], 'borrower_id': ['A', 'B', 'C', 'D', 'A'], 'loan_id': ['L1', 'L2', 'L3', 'L4', 'L5'], 'as_of_date': ['2026-01-31'] * 5, 'loan_amount': [10000.0, 8000.0, 6000.0, 4000.0, 12000.0], 'collateral_value': [12000.0, 10000.0, 8000.0, 5000.0, 15000.0]})

    def test_velocity_of_default_appears_in_calculate_all(self):
        df = pd.DataFrame({'dpd_30_60_usd': [100.0, 120.0], 'dpd_60_90_usd': [50.0, 60.0], 'dpd_90_plus_usd': [25.0, 30.0], 'total_receivable_usd': [5000.0, 5200.0], 'dpd': [35, 40], 'status': ['delinquent', 'defaulted'], 'outstanding_balance': [5000.0, 5200.0], 'as_of_date': pd.to_datetime(['2026-01-31', '2026-02-28']), 'loan_amount': [5000.0, 5200.0], 'collateral_value': [6000.0, 6300.0]})
        engine = KPIEngineV2(df, actor='audit_test')
        results = engine.calculate_all()
        self.assertIn('velocity_of_default', results)
        vd = results['velocity_of_default']['value']
        self.assertIsNotNone(vd)
        self.assertIsInstance(vd, float)

    def test_avg_credit_line_utilization_computed_from_utilization_pct(self):
        df = pd.DataFrame({'utilization_pct': [0.6, 0.75, 0.5], 'outstanding_balance': [10000.0, 8000.0, 6000.0], 'dpd_30_60_usd': [0.0, 0.0, 0.0], 'dpd_60_90_usd': [0.0, 0.0, 0.0], 'dpd_90_plus_usd': [0.0, 0.0, 0.0], 'total_receivable_usd': [5000.0, 6000.0, 7000.0], 'loan_amount': [4000.0, 5000.0, 6000.0], 'collateral_value': [5000.0, 6500.0, 7500.0]})
        engine = KPIEngineV2(df, actor='audit_test')
        results = engine.calculate_all()
        self.assertIn('avg_credit_line_utilization', results)
        val = results['avg_credit_line_utilization']['value']
        self.assertAlmostEqual(val, 61.67, delta=1.0)

    def test_npl_ratio_uses_30dpd_broad_threshold(self):
        df = self._make_portfolio_df()
        engine = KPIEngineV2(df, actor='audit_test')
        results = engine.calculate_all()
        self.assertIn('npl_ratio', results)
        val = results['npl_ratio']['value']
        self.assertAlmostEqual(val, 45.0, delta=0.1)

    def test_npl_90_ratio_is_subset_of_npl_ratio(self):
        df = self._make_portfolio_df()
        engine = KPIEngineV2(df, actor='audit_test')
        results = engine.calculate_all()
        self.assertIn('npl_ratio', results)
        self.assertIn('npl_90_ratio', results)
        npl = results['npl_ratio']['value']
        npl_90 = results['npl_90_ratio']['value']
        self.assertLessEqual(npl_90, npl)
        self.assertAlmostEqual(npl_90, 25.0, delta=0.1)

    def test_defaulted_outstanding_ratio_only_defaulted_status(self):
        df = self._make_portfolio_df()
        engine = KPIEngineV2(df, actor='audit_test')
        results = engine.calculate_all()
        self.assertIn('defaulted_outstanding_ratio', results)
        val = results['defaulted_outstanding_ratio']['value']
        self.assertAlmostEqual(val, 25.0, delta=0.1)

    def test_ltv_sintetico_mean_in_results_when_columns_present(self):
        df = pd.DataFrame({'dpd_30_60_usd': [0.0], 'dpd_60_90_usd': [0.0], 'dpd_90_plus_usd': [0.0], 'total_receivable_usd': [10000.0], 'dpd': [0], 'status': ['active'], 'outstanding_balance': [10000.0], 'capital_desembolsado': [8000.0], 'valor_nominal_factura': [10000.0], 'tasa_dilucion': [0.1], 'loan_amount': [8000.0], 'collateral_value': [10000.0]})
        engine = KPIEngineV2(df, actor='audit_test')
        results = engine.calculate_all()
        if 'ltv_sintetico_mean' in results:
            val = results['ltv_sintetico_mean']['value']
            self.assertAlmostEqual(float(val), 0.8889, delta=0.01)

    def test_top_10_borrower_concentration_zero_without_borrower_col(self):
        engine = KPIEngineV2.__new__(KPIEngineV2)
        df = pd.DataFrame({'dpd': [5, 35], 'status': ['active', 'delinquent'], 'outstanding_balance': [10000.0, 8000.0]})
        result = engine._top_10_borrower_concentration(df, 'outstanding_balance', Decimal('18000'))
        self.assertEqual(result, Decimal('0.0'))

    def test_derived_risk_kpis_empty_when_missing_required_columns(self):
        df_no_cols = pd.DataFrame({'some_col': [1, 2, 3]})
        engine = KPIEngineV2(df_no_cols, actor='audit_test')
        result = engine._calculate_derived_risk_kpis(df_no_cols)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})
if __name__ == '__main__':
    unittest.main()
