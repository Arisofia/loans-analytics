import json
import tempfile
import unittest
from pathlib import Path
from backend.python.kpis.strategic_reporting import build_strategic_summary, generate_strategic_report, load_dashboard_metrics, write_strategic_report

class TestStrategicReporting(unittest.TestCase):

    def test_writes_report_artifacts_and_contains_links(self):
        metrics = {'extended_kpis': {'strategic_confirmations': {'cac_confirmed': True, 'ltv_confirmed': True, 'margin_confirmed': True, 'revenue_forecast_confirmed': True, 'latest_cac_usd': 120.0, 'latest_ltv_usd': 480.0, 'latest_gross_margin_pct': 0.34, 'next_month_revenue_forecast_usd': 2600.0}, 'unit_economics': [{'cac_usd': 120.0, 'ltv_realized_usd': 480.0}], 'revenue_forecast_6m': [{'forecast_revenue_usd': 2600.0}], 'opportunity_prioritization': [{'client_segment': 'SME', 'priority_score': 88.0, 'Portfolio_Value': 100000.0, 'Delinquency_Rate': 0.08}], 'data_governance': {'quality_score': 0.92, 'duplicate_rate': 0.01, 'freshness_days': 1, 'governance_status': 'green'}}}
        summary = build_strategic_summary(metrics)
        links = {'streamlit_local': 'http://localhost:8501', 'grafana_local': 'http://localhost:3001/dashboards', 'streamlit_prod': 'https://analytics-dashboard.azurewebsites.net', 'dashboard_docs': 'docs/analytics/dashboards.md'}
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path, md_path = write_strategic_report(summary, links, Path(temp_dir))
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            markdown = md_path.read_text(encoding='utf-8')
            self.assertIn('Dashboard Links', markdown)
            self.assertIn('http://localhost:8501', markdown)
            self.assertIn('CAC', markdown)

    def test_load_dashboard_metrics_from_exports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            exports_dir = root / 'exports'
            exports_dir.mkdir(parents=True, exist_ok=True)
            dashboard_path = exports_dir / 'complete_kpi_dashboard.json'
            payload = {'extended_kpis': {'strategic_confirmations': {}}}
            dashboard_path.write_text(json.dumps(payload), encoding='utf-8')
            loaded = load_dashboard_metrics(root)
            self.assertEqual(loaded, payload)

    def test_generate_strategic_report_builds_dashboard_and_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / 'data' / 'raw'
            exports_dir = root / 'exports'
            data_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / 'loan_data.csv').write_text('loan_id,customer_id,origination_date,outstanding_loan_value,principal_amount,interest_rate_apr,days_past_due\nL1,C1,2025-01-15,1000,1200,0.2,5\nL2,C2,2025-02-10,2000,2200,0.25,35\n', encoding='utf-8')
            (data_dir / 'real_payment.csv').write_text('payment_date,customer_id,payment_amount,true_interest_payment,true_fee_payment\n2025-01-31,C1,120,80,40\n2025-02-28,C2,150,100,50\n', encoding='utf-8')
            (data_dir / 'customer_data.csv').write_text('customer_id,created_at,marketing_spend\nC1,2025-01-01,200\nC2,2025-02-01,300\n', encoding='utf-8')
            outputs = generate_strategic_report(data_dir, exports_dir)
            dashboard_json = Path(outputs['dashboard_json'])
            report_json = Path(outputs['strategic_report_json'])
            report_md = Path(outputs['strategic_report_md'])
            self.assertTrue(dashboard_json.exists())
            self.assertTrue(report_json.exists())
            self.assertTrue(report_md.exists())
            payload = json.loads(dashboard_json.read_text(encoding='utf-8'))
            self.assertIn('extended_kpis', payload)
            self.assertIn('executive_strip', payload['extended_kpis'])
            self.assertIn('nsm', payload)
            self.assertIn('guardrails', payload)
            self.assertIn('guardrail_status', payload)
            self.assertIn('sql_view_mirrors', payload)
if __name__ == '__main__':
    unittest.main()
