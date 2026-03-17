"""Tests for strategic reporting utility module."""

import json
import tempfile
import unittest
from pathlib import Path

from python.kpis.strategic_reporting import (
    build_strategic_summary,
    load_dashboard_metrics,
    write_strategic_report,
)


class TestStrategicReporting(unittest.TestCase):
    """Validate strategic report generation with dashboard links and confirmations."""

    def test_writes_report_artifacts_and_contains_links(self):
        metrics = {
            "extended_kpis": {
                "strategic_confirmations": {
                    "cac_confirmed": True,
                    "ltv_confirmed": True,
                    "margin_confirmed": True,
                    "revenue_forecast_confirmed": True,
                    "latest_cac_usd": 120.0,
                    "latest_ltv_usd": 480.0,
                    "latest_gross_margin_pct": 0.34,
                    "next_month_revenue_forecast_usd": 2600.0,
                },
                "unit_economics": [{"cac_usd": 120.0, "ltv_realized_usd": 480.0}],
                "revenue_forecast_6m": [{"forecast_revenue_usd": 2600.0}],
                "opportunity_prioritization": [
                    {
                        "client_segment": "SME",
                        "priority_score": 88.0,
                        "Portfolio_Value": 100000.0,
                        "Delinquency_Rate": 0.08,
                    }
                ],
                "data_governance": {
                    "quality_score": 0.92,
                    "duplicate_rate": 0.01,
                    "freshness_days": 1,
                    "governance_status": "green",
                },
            }
        }

        summary = build_strategic_summary(metrics)

        links = {
            "streamlit_local": "http://localhost:8501",
            "grafana_local": "http://localhost:3001/dashboards",
            "streamlit_prod": "https://abaco-analytics-dashboard.azurewebsites.net",
            "dashboard_docs": "docs/analytics/dashboards.md",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path, md_path = write_strategic_report(summary, links, Path(temp_dir))
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("Dashboard Links", markdown)
            self.assertIn("http://localhost:8501", markdown)
            self.assertIn("CAC", markdown)

    def test_load_dashboard_metrics_from_exports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            exports_dir = root / "exports"
            exports_dir.mkdir(parents=True, exist_ok=True)
            dashboard_path = exports_dir / "complete_kpi_dashboard.json"
            payload = {"extended_kpis": {"strategic_confirmations": {}}}
            dashboard_path.write_text(json.dumps(payload), encoding="utf-8")

            loaded = load_dashboard_metrics(root)
            self.assertEqual(loaded, payload)


if __name__ == "__main__":
    unittest.main()
