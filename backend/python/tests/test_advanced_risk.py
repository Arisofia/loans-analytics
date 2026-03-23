import asyncio
import unittest
from unittest.mock import patch
import pandas as pd
from backend.python.apps.analytics.api.models import AdvancedRiskResponse, LoanRecord
from backend.python.apps.analytics.api.service import KPIService
from backend.python.kpis.advanced_risk import calculate_advanced_risk_metrics

class TestAdvancedRiskMetrics(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({'loan_id': ['L1', 'L2', 'L3', 'L4'], 'borrower_id': ['B1', 'B1', 'B2', 'B3'], 'loan_status': ['current', '30-59 days past due', '60-89 days past due', 'default'], 'days_past_due': [0, 45, 75, 120], 'principal_balance': [100.0, 200.0, 300.0, 400.0], 'loan_amount': [120.0, 220.0, 320.0, 420.0], 'interest_rate': [0.1, 0.2, 0.3, 0.4], 'origination_fee': [1.0, 2.0, 3.0, 4.0], 'origination_fee_taxes': [0.1, 0.2, 0.3, 0.4], 'last_payment_amount': [10.0, 20.0, 30.0, 40.0], 'total_scheduled': [20.0, 40.0, 60.0, 80.0], 'recovery_value': [0.0, 0.0, 0.0, 50.0], 'credit_score': [600.0, 650.0, 700.0, 750.0]})

    def test_calculate_advanced_risk_metrics_values(self):
        metrics = calculate_advanced_risk_metrics(self.df)
        self.assertEqual(metrics['total_loans'], 4)
        self.assertEqual(metrics['par30'], 90.0)
        self.assertEqual(metrics['par60'], 70.0)
        self.assertEqual(metrics['par90'], 40.0)
        self.assertEqual(metrics['default_rate'], 25.0)
        self.assertEqual(metrics['collections_coverage'], 50.0)
        self.assertAlmostEqual(metrics['fee_yield'], 1.02, places=2)
        self.assertAlmostEqual(metrics['total_yield'], 31.02, places=2)
        self.assertEqual(metrics['recovery_rate'], 12.5)
        self.assertEqual(metrics['concentration_hhi'], 3400.0)
        self.assertEqual(metrics['repeat_borrower_rate'], 33.33)
        self.assertEqual(metrics['credit_quality_index'], 68.18)
        buckets = {bucket['bucket']: bucket for bucket in metrics['dpd_buckets']}
        self.assertEqual(buckets['current']['loan_count'], 1)
        self.assertEqual(buckets['31_60']['loan_count'], 1)
        self.assertEqual(buckets['61_90']['loan_count'], 1)
        self.assertEqual(buckets['90_plus']['loan_count'], 1)
        self.assertEqual(buckets['90_plus']['balance'], 400.0)

    def test_calculate_advanced_risk_metrics_empty_dataframe(self):
        metrics = calculate_advanced_risk_metrics(pd.DataFrame())
        self.assertEqual(metrics['total_loans'], 0)
        self.assertEqual(metrics['par30'], 0.0)
        self.assertEqual(metrics['par60'], 0.0)
        self.assertEqual(metrics['par90'], 0.0)
        self.assertEqual(metrics['dpd_buckets'], [])

    def test_par_metrics_use_ssot_formula_engine(self):
        with patch('backend.python.kpis.ssot_asset_quality.KPIFormulaEngine.calculate_kpi') as mock_calc:
            mock_calc.side_effect = [{'value': 11.11}, {'value': 22.22}, {'value': 33.33}]
            metrics = calculate_advanced_risk_metrics(self.df)
        self.assertEqual(metrics['par30'], 11.11)
        self.assertEqual(metrics['par60'], 22.22)
        self.assertEqual(metrics['par90'], 33.33)
        self.assertEqual(mock_calc.call_count, 3)

class TestAdvancedRiskService(unittest.TestCase):

    def test_service_returns_advanced_risk_response(self):
        service = KPIService(actor='test_user')
        loans = [LoanRecord(id='L1', borrower_id='B1', loan_amount=1000.0, principal_balance=900.0, interest_rate=0.2, loan_status='current', days_past_due=0, total_scheduled=200.0, last_payment_amount=150.0, origination_fee=20.0, origination_fee_taxes=2.0, credit_score=710.0), LoanRecord(id='L2', borrower_id='B1', loan_amount=1200.0, principal_balance=1000.0, interest_rate=0.3, loan_status='default', days_past_due=110, total_scheduled=200.0, last_payment_amount=50.0, recovery_value=100.0, origination_fee=25.0, origination_fee_taxes=2.5, credit_score=660.0)]
        response = asyncio.run(service.calculate_advanced_risk(loans))
        self.assertIsInstance(response, AdvancedRiskResponse)
        self.assertEqual(response.total_loans, 2)
        self.assertEqual(response.par30, 52.63)
        self.assertEqual(response.par60, 52.63)
        self.assertEqual(response.par90, 52.63)
        self.assertEqual(response.default_rate, 50.0)
        self.assertEqual(response.repeat_borrower_rate, 100.0)
        self.assertGreater(response.total_yield, 0.0)
if __name__ == '__main__':
    unittest.main()
