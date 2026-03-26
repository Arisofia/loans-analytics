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


if __name__ == '__main__':
    unittest.main()
