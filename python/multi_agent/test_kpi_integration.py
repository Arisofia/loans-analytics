"""Tests for KPI integration with multi-agent system."""

import unittest
from datetime import datetime

from python.models.kpi_models import KpiDefinition, KpiRegistry, KpiValidationConfig
from python.multi_agent.kpi_integration import (
    KpiAnomaly,
    KpiContextProvider,
    KpiValidationResult,
    KpiValue,
)


class TestKpiIntegration(unittest.TestCase):
    """Test KPI integration functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test KPI definitions
        self.kpi_defs = [
            KpiDefinition(
                name="default_rate",
                formula="defaults / total_loans",
                source_table="loan_portfolio",
                description="Percentage of loans in default",
                validation=KpiValidationConfig(
                    validation_range=(0.0, 0.05),  # 0-5% acceptable
                    precision=4
                )
            ),
            KpiDefinition(
                name="net_interest_margin",
                formula="(interest_income - interest_expense) / earning_assets",
                source_table="financial_statements",
                description="Net interest margin percentage",
                validation=KpiValidationConfig(
                    validation_range=(0.02, 0.08),  # 2-8% acceptable
                    precision=4
                )
            ),
            KpiDefinition(
                name="loan_to_value_ratio",
                formula="loan_amount / collateral_value",
                source_table="loan_details",
                description="Average loan-to-value ratio",
                validation=KpiValidationConfig(
                    validation_range=(0.0, 0.80),  # 0-80% acceptable
                    precision=2
                )
            )
        ]

        self.registry = KpiRegistry(kpis=self.kpi_defs)
        self.kpi_provider = KpiContextProvider(self.registry)

    def test_kpi_value_creation(self):
        """Test creating KPI values."""
        kpi_value = KpiValue(
            kpi_name="default_rate",
            value=0.03,
            metadata={"source": "daily_report"}
        )

        self.assertEqual(kpi_value.kpi_name, "default_rate")
        self.assertEqual(kpi_value.value, 0.03)
        self.assertIsInstance(kpi_value.timestamp, datetime)
        self.assertEqual(kpi_value.metadata["source"], "daily_report")

    def test_update_kpi_value(self):
        """Test updating KPI values in provider."""
        self.kpi_provider.update_kpi_value("default_rate", 0.03)

        self.assertIn("default_rate", self.kpi_provider.current_values)
        self.assertEqual(self.kpi_provider.current_values["default_rate"].value, 0.03)

    def test_get_kpi_definition(self):
        """Test retrieving KPI definitions."""
        kpi_def = self.kpi_provider.get_kpi_definition("default_rate")

        self.assertEqual(kpi_def.name, "default_rate")
        self.assertEqual(kpi_def.formula, "defaults / total_loans")
        self.assertEqual(kpi_def.source_table, "loan_portfolio")

    def test_get_kpi_definition_not_found(self):
        """Test retrieving non-existent KPI."""
        with self.assertRaises(KeyError):
            self.kpi_provider.get_kpi_definition("nonexistent_kpi")

    def test_validate_kpi_value_within_range(self):
        """Test validating KPI value within acceptable range."""
        result = self.kpi_provider.validate_kpi_value("default_rate", 0.03)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, 0.03)
        self.assertIsNone(result.breach_type)
        self.assertEqual(result.validation_message, "Value within acceptable range")

    def test_validate_kpi_value_above_max(self):
        """Test validating KPI value above maximum."""
        result = self.kpi_provider.validate_kpi_value("default_rate", 0.08)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.breach_type, "upper_bound")
        self.assertIn("above maximum", result.validation_message)

    def test_validate_kpi_value_below_min(self):
        """Test validating KPI value below minimum."""
        result = self.kpi_provider.validate_kpi_value("net_interest_margin", 0.01)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.breach_type, "lower_bound")
        self.assertIn("below minimum", result.validation_message)

    def test_validate_unknown_kpi(self):
        """Test validating value for unknown KPI."""
        result = self.kpi_provider.validate_kpi_value("unknown_kpi", 0.5)

        self.assertFalse(result.is_valid)
        self.assertIn("not found in registry", result.validation_message)

    def test_detect_anomalies_none(self):
        """Test anomaly detection with all values valid."""
        kpi_values = {
            "default_rate": 0.03,
            "net_interest_margin": 0.05,
            "loan_to_value_ratio": 0.70
        }

        anomalies = self.kpi_provider.detect_anomalies(kpi_values)

        self.assertEqual(len(anomalies), 0)

    def test_detect_anomalies_single(self):
        """Test anomaly detection with one breach."""
        kpi_values = {
            "default_rate": 0.08,  # Above 5% max
            "net_interest_margin": 0.05,
            "loan_to_value_ratio": 0.70
        }

        anomalies = self.kpi_provider.detect_anomalies(kpi_values)

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0].kpi_name, "default_rate")
        self.assertEqual(anomalies[0].current_value, 0.08)
        self.assertIn(anomalies[0].severity, ["critical", "warning", "info"])

    def test_detect_anomalies_multiple(self):
        """Test anomaly detection with multiple breaches."""
        kpi_values = {
            "default_rate": 0.10,  # Above max
            "net_interest_margin": 0.01,  # Below min
            "loan_to_value_ratio": 0.70  # Valid
        }

        anomalies = self.kpi_provider.detect_anomalies(kpi_values)

        self.assertEqual(len(anomalies), 2)
        anomaly_names = [a.kpi_name for a in anomalies]
        self.assertIn("default_rate", anomaly_names)
        self.assertIn("net_interest_margin", anomaly_names)

    def test_severity_determination_critical(self):
        """Test severity determination for critical breach (>20%)."""
        severity = self.kpi_provider._determine_severity(
            value=0.10,  # 100% over max of 0.05
            expected_range=(0.0, 0.05),
            breach_type="upper_bound"
        )

        self.assertEqual(severity, "critical")

    def test_severity_determination_warning(self):
        """Test severity determination for warning breach (10-20%)."""
        severity = self.kpi_provider._determine_severity(
            value=0.06,  # 20% over max of 0.05
            expected_range=(0.0, 0.05),
            breach_type="upper_bound"
        )

        self.assertEqual(severity, "warning")

    def test_severity_determination_info(self):
        """Test severity determination for info breach (<10%)."""
        severity = self.kpi_provider._determine_severity(
            value=0.054,  # 8% over max of 0.05
            expected_range=(0.0, 0.05),
            breach_type="upper_bound"
        )

        self.assertEqual(severity, "info")

    def test_get_kpi_context_for_agent(self):
        """Test generating KPI context for agents."""
        # Update some values
        self.kpi_provider.update_kpi_value("default_rate", 0.03)
        self.kpi_provider.update_kpi_value("net_interest_margin", 0.05)

        context = self.kpi_provider.get_kpi_context_for_agent(["default_rate", "net_interest_margin"])

        self.assertIn("kpis", context)
        self.assertIn("timestamp", context)
        self.assertEqual(context["total_kpis"], 2)

        # Check default_rate context
        self.assertIn("default_rate", context["kpis"])
        dr_context = context["kpis"]["default_rate"]
        self.assertEqual(dr_context["current_value"], 0.03)
        self.assertTrue(dr_context["is_valid"])

    def test_get_kpi_context_without_values(self):
        """Test generating KPI context when no values are set."""
        context = self.kpi_provider.get_kpi_context_for_agent(["default_rate"])

        self.assertIn("default_rate", context["kpis"])
        dr_context = context["kpis"]["default_rate"]
        self.assertNotIn("current_value", dr_context)
        self.assertIn("definition", dr_context)

    def test_format_kpi_summary(self):
        """Test generating human-readable KPI summary."""
        self.kpi_provider.update_kpi_value("default_rate", 0.03)

        summary = self.kpi_provider.format_kpi_summary(["default_rate"])

        self.assertIn("📊 KPI Summary", summary)
        self.assertIn("default_rate", summary)
        self.assertIn("Current Value: 0.03", summary)
        self.assertIn("✅", summary)  # Valid indicator

    def test_format_kpi_summary_with_breach(self):
        """Test generating KPI summary with breach."""
        self.kpi_provider.update_kpi_value("default_rate", 0.08)  # Above max

        summary = self.kpi_provider.format_kpi_summary(["default_rate"])

        self.assertIn("❌", summary)  # Invalid indicator
        self.assertIn("above maximum", summary)


if __name__ == "__main__":
    unittest.main()
