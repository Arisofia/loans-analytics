import unittest
import pandas as pd
from backend.python.kpis.catalog_processor import KPICatalogProcessor

class TestKPICatalogProcessorStrategic(unittest.TestCase):

    def setUp(self):
        self.loans_df = pd.DataFrame({'loan_id': ['L1', 'L2', 'L3', 'L4', 'L5', 'L6'], 'customer_id': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'], 'origination_date': ['2025-01-10', '2025-02-12', '2025-03-15', '2025-04-11', '2025-05-09', '2025-06-18'], 'outstanding_loan_value': [12000, 14000, 16000, 15000, 18000, 19000], 'principal_amount': [13000, 15000, 17000, 16000, 19000, 20000], 'interest_rate_apr': [0.28, 0.26, 0.25, 0.24, 0.23, 0.22], 'origination_fee': [200, 250, 300, 260, 320, 340], 'origination_fee_taxes': [26, 33, 39, 34, 42, 44], 'days_past_due': [5, 12, 18, 25, 45, 60], 'product_type': ['SME', 'SME', 'Retail', 'Retail', 'SME', 'Auto'], 'sales_channel': ['Digital', 'Digital', 'KAM', 'KAM', 'Mixed', 'Mixed']})
        self.payments_df = pd.DataFrame({'payment_date': ['2025-01-31', '2025-02-28', '2025-03-31', '2025-04-30', '2025-05-31', '2025-06-30'], 'customer_id': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'], 'payment_amount': [1100, 1300, 1500, 1600, 1750, 1850], 'true_interest_payment': [700, 830, 960, 1010, 1100, 1180], 'true_fee_payment': [400, 470, 540, 590, 650, 670]})
        self.customers_df = pd.DataFrame({'customer_id': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'], 'created_at': ['2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-05-01', '2025-06-01'], 'marketing_spend': [500, 500, 600, 650, 700, 700]})

    def test_get_all_kpis_includes_strategic_outputs(self):
        processor = KPICatalogProcessor(self.loans_df, self.payments_df, self.customers_df)
        kpis = processor.get_all_kpis()
        self.assertIn('executive_strip', kpis)
        self.assertIn('revenue_forecast_6m', kpis)
        self.assertIn('opportunity_prioritization', kpis)
        self.assertIn('unit_economics', kpis)
        self.assertIn('data_governance', kpis)
        self.assertIn('strategic_confirmations', kpis)
        self.assertIn('nsm_customer_types', kpis)
        self.assertIn('portfolio_rotation', kpis)
        self.assertIn('concentration', kpis)
        self.assertIn('dpd_buckets', kpis)
        self.assertIn('weighted_apr', kpis)
        self.assertIn('weighted_fee_rate', kpis)
        self.assertIn('monthly_pricing', kpis)
        self.assertIn('lending_kpis', kpis)
        strategic = kpis['strategic_confirmations']
        self.assertTrue(strategic['cac_confirmed'])
        self.assertTrue(strategic['ltv_confirmed'])
        self.assertTrue(strategic['margin_confirmed'])
        self.assertTrue(strategic['revenue_forecast_confirmed'])
        nsm = kpis['nsm_customer_types']
        self.assertIn('recurrent_tpv_12m_usd', nsm)
        self.assertIn('recurrent_clients_12m', nsm)
        rotation = kpis['portfolio_rotation']
        self.assertIn('rotation_x', rotation)
        self.assertIn('aum_usd', rotation)
        lending = kpis['lending_kpis']
        self.assertIn('cdr_curves', lending)
        self.assertIn('liquidation_rate', lending)
        self.assertIn('mype_decisions', lending)
        self.assertIn('treasury_capacity', lending)
        # treasury_capacity is 'not_provided' when no cash_balance passed via get_all_kpis
        self.assertEqual(lending['treasury_capacity']['status'], 'not_provided')

    def test_forecast_prioritization_and_governance_are_populated(self):
        processor = KPICatalogProcessor(self.loans_df, self.payments_df, self.customers_df)
        forecast_rows = processor.get_revenue_forecast()
        self.assertEqual(len(forecast_rows), 6)
        self.assertIn('forecast_revenue_usd', forecast_rows[0])
        opportunities = processor.get_opportunity_prioritization()
        self.assertGreater(len(opportunities), 0)
        self.assertIn('priority_score', opportunities[0])
        governance = processor.get_data_governance()
        self.assertIn('quality_score', governance)
        self.assertGreaterEqual(governance['quality_score'], 0.0)
        self.assertLessEqual(governance['quality_score'], 1.0)

    def test_changelog_compatibility_aliases_exist_and_return_values(self):
        processor = KPICatalogProcessor(self.loans_df, self.payments_df, self.customers_df)
        monthly_pricing = processor.get_monthly_pricing()
        self.assertIn('current', monthly_pricing)
        self.assertIn('monthly', monthly_pricing)
        weighted_apr = processor.get_weighted_apr()
        weighted_fee_rate = processor.get_weighted_fee_rate()
        self.assertIsInstance(weighted_apr, float)
        self.assertIsInstance(weighted_fee_rate, float)
        self.assertGreaterEqual(weighted_apr, 0.0)
        concentration = processor.get_concentration()
        self.assertIn('top_1_pct', concentration)
        self.assertIn('top_10_pct', concentration)
        self.assertIn('top_1_debtor_pct', concentration)
        self.assertIn('top_10_debtor_pct', concentration)
        self.assertIn('hhi', concentration)
        dpd_buckets = processor.get_dpd_buckets()
        self.assertIn('dpd_0_7', dpd_buckets)
        self.assertIn('dpd_90_plus', dpd_buckets)
        self.assertIn('dpd_30_plus_pct', dpd_buckets)
        self.assertIn('dpd_180_plus_pct', dpd_buckets)
        customer_types = processor.get_customer_types()
        self.assertIn('new_count', customer_types)
        self.assertIn('recurrent_tpv_12m_pct', customer_types)
        rotation = processor.get_portfolio_rotation()
        self.assertIn('rotation_x', rotation)


class TestCashBalanceTreasury(unittest.TestCase):

    def setUp(self):
        self.loans_df = pd.DataFrame({
            'outstanding_loan_value': [10000, 20000, 15000],
            'interest_rate_apr': [0.28, 0.26, 0.30],
            'disbursement_amount': [11000, 21000, 16000],
        })

    def test_returns_ok_status(self):
        from backend.python.kpis.lending_kpis import cash_balance_treasury
        result = cash_balance_treasury(cash_balance_usd=200_000.0, loans_df=self.loans_df)
        self.assertEqual(result['status'], 'ok')

    def test_available_to_disburse_respects_reserve(self):
        from backend.python.kpis.lending_kpis import cash_balance_treasury
        result = cash_balance_treasury(cash_balance_usd=100_000.0, reserve_ratio=0.10, avg_portfolio_apr=0.28)
        self.assertAlmostEqual(result['capacity']['reserve_held_usd'], 10_000.0, places=1)
        self.assertAlmostEqual(result['capacity']['available_to_disburse_usd'], 90_000.0, places=1)

    def test_pending_disbursements_reduce_available(self):
        from backend.python.kpis.lending_kpis import cash_balance_treasury
        result = cash_balance_treasury(cash_balance_usd=100_000.0, pending_disbursements_usd=40_000.0, reserve_ratio=0.10, avg_portfolio_apr=0.28)
        # available = 100k - 10k reserve - 40k pending = 50k
        self.assertAlmostEqual(result['capacity']['available_to_disburse_usd'], 50_000.0, places=1)

    def test_opportunity_cost_is_positive(self):
        from backend.python.kpis.lending_kpis import cash_balance_treasury
        result = cash_balance_treasury(cash_balance_usd=500_000.0, pending_disbursements_usd=100_000.0, avg_portfolio_apr=0.28)
        self.assertGreater(result['opportunity_cost']['opp_cost_idle_monthly_usd'], 0)
        self.assertGreater(result['opportunity_cost']['pending_dis_opp_cost_monthly_usd'], 0)

    def test_alert_triggered_on_high_idle_cash(self):
        from backend.python.kpis.lending_kpis import cash_balance_treasury
        result = cash_balance_treasury(cash_balance_usd=1_000_000.0, avg_portfolio_apr=0.28)
        alert_msgs = ' '.join(result['alerts'])
        self.assertIn('HIGH_IDLE_CASH', alert_msgs)

    def test_insufficient_cash_alert(self):
        from backend.python.kpis.lending_kpis import cash_balance_treasury
        result = cash_balance_treasury(cash_balance_usd=10_000.0, pending_disbursements_usd=100_000.0, reserve_ratio=0.10, avg_portfolio_apr=0.28)
        alert_msgs = ' '.join(result['alerts'])
        self.assertIn('INSUFFICIENT_CASH', alert_msgs)

    def test_treasury_not_provided_when_no_cash_balance(self):
        from backend.python.kpis.lending_kpis import build_lending_kpi_report
        loans_df = self.loans_df.copy()
        payments_df = pd.DataFrame({
            'customer_id': ['C1'],
            'true_payment_date': ['2025-01-31'],
            'true_interest_payment': [500],
            'true_fee_payment': [100],
            'true_principal_payment': [800],
            'true_tax_payment': [50],
            'true_total_payment': [1400],
            'true_payment_status': ['On Time'],
        })
        report = build_lending_kpi_report(loans_df=loans_df, payments_df=payments_df)
        self.assertEqual(report['treasury_capacity']['status'], 'not_provided')

    def test_treasury_active_when_cash_balance_provided(self):
        from backend.python.kpis.lending_kpis import build_lending_kpi_report
        loans_df = self.loans_df.copy()
        payments_df = pd.DataFrame({
            'customer_id': ['C1'],
            'true_payment_date': ['2025-01-31'],
            'true_interest_payment': [500],
            'true_fee_payment': [100],
            'true_principal_payment': [800],
            'true_tax_payment': [50],
            'true_total_payment': [1400],
            'true_payment_status': ['On Time'],
        })
        report = build_lending_kpi_report(loans_df=loans_df, payments_df=payments_df, cash_balance_usd=250_000.0, pending_disbursements_usd=50_000.0)
        self.assertEqual(report['treasury_capacity']['status'], 'ok')
        self.assertIn('capacity', report['treasury_capacity'])
        self.assertIn('opportunity_cost', report['treasury_capacity'])


class TestCollectionEfficiency6M(unittest.TestCase):

    def _make_loans(self, due_offset_days: list[int], balances: list[float], collected: list[float] | None = None) -> pd.DataFrame:
        today = pd.Timestamp.now()
        data: dict = {
            'loan_id': [f'L{i}' for i in range(len(due_offset_days))],
            'due_date': [(today - pd.Timedelta(days=d)).strftime('%Y-%m-%d') for d in due_offset_days],
            'outstanding_loan_value': balances,
        }
        if collected is not None:
            data['capital_collected'] = collected
        return pd.DataFrame(data)

    def test_full_collection_returns_100_pct(self):
        loans = self._make_loans([30, 60, 90], [1000.0, 2000.0, 3000.0], collected=[1000.0, 2000.0, 3000.0])
        from backend.python.kpis.lending_kpis import collection_efficiency_6m
        r = collection_efficiency_6m(loans)
        self.assertEqual(r['status'], 'ok')
        self.assertAlmostEqual(r['ce_6m_pct'], 100.0, places=1)
        self.assertFalse(r['breach'])
        self.assertEqual(r['data_source'], 'direct_capital_collected')

    def test_partial_collection_breach(self):
        loans = self._make_loans([30, 60], [1000.0, 1000.0], collected=[500.0, 500.0])
        from backend.python.kpis.lending_kpis import collection_efficiency_6m
        r = collection_efficiency_6m(loans, target_ce=0.96)
        self.assertTrue(r['breach'])
        self.assertAlmostEqual(r['ce_6m_pct'], 50.0, places=1)

    def test_no_due_col_returns_insufficient_data(self):
        loans = pd.DataFrame({'loan_id': ['L1'], 'outstanding_loan_value': [1000.0]})
        from backend.python.kpis.lending_kpis import collection_efficiency_6m
        r = collection_efficiency_6m(loans)
        self.assertEqual(r['status'], 'insufficient_data')
        self.assertIsNone(r['ce_6m_pct'])

    def test_loans_outside_window_returns_no_loans(self):
        loans = self._make_loans([400], [5000.0], collected=[5000.0])  # 400 days ago = outside 180d
        from backend.python.kpis.lending_kpis import collection_efficiency_6m
        r = collection_efficiency_6m(loans)
        self.assertEqual(r['status'], 'no_loans_in_window')

    def test_payments_df_fallback(self):
        loans = self._make_loans([45], [2000.0])  # no capital_collected column
        payments = pd.DataFrame({'loan_id': ['L0'], 'true_principal_payment': [1800.0]})
        from backend.python.kpis.lending_kpis import collection_efficiency_6m
        r = collection_efficiency_6m(loans, payments_df=payments)
        self.assertEqual(r['status'], 'ok')
        self.assertAlmostEqual(r['ce_6m_pct'], 90.0, places=1)
        self.assertEqual(r['data_source'], 'payments_df_principal')


class TestSLATargets(unittest.TestCase):

    def test_target_mode_returns_targets(self):
        from backend.python.kpis.lending_kpis import sla_targets
        r = sla_targets()
        self.assertEqual(r['status'], 'ok')
        self.assertIn('targets', r)
        self.assertIn('decision_sla_hours', r['targets'])
        self.assertIn('funding_sla_hours', r['targets'])
        self.assertEqual(r['data_source'], 'target_only')

    def test_proxy_from_app_to_disbursement(self):
        from backend.python.kpis.lending_kpis import sla_targets
        loans = pd.DataFrame({
            'application_date': ['2025-01-01', '2025-02-01'],
            'disbursement_date': ['2025-01-02', '2025-02-02'],  # 24h each
        })
        r = sla_targets(loans)
        self.assertIn('actual', r)
        self.assertEqual(r['data_source'], 'proxy_app_to_disbursement')
        self.assertAlmostEqual(r['actual']['median_app_to_disbursement_hours'], 24.0, delta=1.0)

    def test_missing_app_date_stays_target_only(self):
        from backend.python.kpis.lending_kpis import sla_targets
        loans = pd.DataFrame({'disbursement_date': ['2025-01-02']})
        r = sla_targets(loans)
        self.assertEqual(r['data_source'], 'target_only')
        self.assertNotIn('actual', r)


class TestFinancingRateEIR(unittest.TestCase):

    def _make_loans(self) -> pd.DataFrame:
        return pd.DataFrame({
            'loan_id': ['L1', 'L2', 'L3'],
            'interest_rate_apr': [0.36, 0.38, 0.34],
            'outstanding_loan_value': [10_000.0, 20_000.0, 30_000.0],
        })

    def test_weighted_apr_computed(self):
        from backend.python.kpis.lending_kpis import financing_rate_eir
        r = financing_rate_eir(self._make_loans())
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['eir_type'], 'rate_charged_to_clients')
        # weighted: (0.36*10k + 0.38*20k + 0.34*30k) / 60k = 0.356...
        self.assertAlmostEqual(r['weighted_apr_pct'], 35.67, delta=0.5)

    def test_no_apr_col_returns_insufficient_data(self):
        from backend.python.kpis.lending_kpis import financing_rate_eir
        loans = pd.DataFrame({'loan_id': ['L1'], 'outstanding_loan_value': [1000.0]})
        r = financing_rate_eir(loans)
        self.assertEqual(r['status'], 'insufficient_data')

    def test_portfolio_yield_from_payments(self):
        from backend.python.kpis.lending_kpis import financing_rate_eir
        payments = pd.DataFrame({'true_interest_payment': [3000.0], 'true_fee_payment': [1000.0]})
        r = financing_rate_eir(self._make_loans(), payments_df=payments)
        self.assertIsNotNone(r['portfolio_yield_pct'])
        # 4000 interest+fees / 60000 AUM = 6.67%
        self.assertAlmostEqual(r['portfolio_yield_pct'], 6.67, delta=0.2)

    def test_all_zero_rates_returns_no_valid_rates(self):
        from backend.python.kpis.lending_kpis import financing_rate_eir
        loans = pd.DataFrame({'loan_id': ['L1'], 'outstanding_loan_value': [1000.0], 'interest_rate_apr': [0.0]})
        r = financing_rate_eir(loans)
        self.assertEqual(r['status'], 'no_valid_rates')


class TestCostOfDebtDSCR(unittest.TestCase):

    def _make_loans(self) -> pd.DataFrame:
        return pd.DataFrame({
            'loan_id': ['L1', 'L2'],
            'outstanding_loan_value': [500_000.0, 500_000.0],
            'interest_rate_apr': [0.36, 0.36],
        })

    def _make_payments(self) -> pd.DataFrame:
        return pd.DataFrame({
            'true_interest_payment': [30_000.0, 30_000.0],
            'true_fee_payment': [5_000.0, 5_000.0],
            'true_payment_date': ['2025-01-31', '2025-06-30'],
        })

    def test_dscr_above_target(self):
        from backend.python.kpis.lending_kpis import cost_of_debt_dscr
        r = cost_of_debt_dscr(self._make_loans(), self._make_payments(), cost_of_debt_pct=0.15)
        self.assertEqual(r['status'], 'ok')
        self.assertGreater(r['dscr'], 1.0)
        self.assertAlmostEqual(r['cost_of_debt_pct_used'], 15.0, places=1)
        self.assertEqual(r['data_source'], 'proxy')

    def test_dscr_breach_when_income_low(self):
        from backend.python.kpis.lending_kpis import cost_of_debt_dscr
        loans = pd.DataFrame({'outstanding_loan_value': [1_000_000.0], 'interest_rate_apr': [0.05]})
        payments = pd.DataFrame({
            'true_interest_payment': [1_000.0],
            'true_payment_date': ['2025-06-30'],
        })
        r = cost_of_debt_dscr(loans, payments, cost_of_debt_pct=0.15)
        self.assertTrue(r['dscr_breach'])

    def test_fallback_to_aum_x_apr(self):
        from backend.python.kpis.lending_kpis import cost_of_debt_dscr
        loans = self._make_loans()
        r = cost_of_debt_dscr(loans, cost_of_debt_pct=0.15)
        # No payments → falls back to AUM × APR
        self.assertIn('estimated_aum_x_avg_apr', r['income_source'])
        self.assertGreater(r['dscr'], 0)

    def test_proxy_note_in_output(self):
        from backend.python.kpis.lending_kpis import cost_of_debt_dscr
        r = cost_of_debt_dscr(self._make_loans())
        self.assertIn('PROXY', r['note'])
        self.assertIn('15.0%', r['note'])


if __name__ == '__main__':
    unittest.main()
