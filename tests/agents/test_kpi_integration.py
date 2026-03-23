import unittest
from datetime import datetime
from backend.python.models.kpi_models import KpiDefinition, KpiRegistry, KpiValidationConfig
from backend.python.multi_agent.kpi_integration import KpiContextProvider, KpiValue

class TestKpiIntegration(unittest.TestCase):

    def setUp(self):
        self.kpi_defs = [KpiDefinition(name='default_rate', formula='defaults / total_loans', source_table='loan_portfolio', description='Percentage of loans in default', validation=KpiValidationConfig(validation_range=(0.0, 0.05), precision=4)), KpiDefinition(name='net_interest_margin', formula='(interest_income - interest_expense) / earning_assets', source_table='financial_statements', description='Net interest margin percentage', validation=KpiValidationConfig(validation_range=(0.02, 0.08), precision=4)), KpiDefinition(name='loan_to_value_ratio', formula='loan_amount / collateral_value', source_table='loan_details', description='Average loan-to-value ratio', validation=KpiValidationConfig(validation_range=(0.0, 0.8), precision=2))]
        self.registry = KpiRegistry(kpis=self.kpi_defs)
        self.kpi_provider = KpiContextProvider(self.registry)

    def test_kpi_value_creation(self):
        kpi_value = KpiValue(kpi_name='default_rate', value=0.03, metadata={'source': 'daily_report'})
        self.assertEqual(kpi_value.kpi_name, 'default_rate')
        self.assertEqual(kpi_value.value, 0.03)
        self.assertIsInstance(kpi_value.timestamp, datetime)
        self.assertEqual(kpi_value.metadata['source'], 'daily_report')

    def test_update_kpi_value(self):
        self.kpi_provider.update_kpi_value('default_rate', 0.03)
        self.assertIn('default_rate', self.kpi_provider.current_values)
        self.assertEqual(self.kpi_provider.current_values['default_rate'].value, 0.03)

    def test_get_kpi_definition(self):
        kpi_def = self.kpi_provider.get_kpi_definition('default_rate')
        self.assertEqual(kpi_def.name, 'default_rate')
        self.assertEqual(kpi_def.formula, 'defaults / total_loans')
        self.assertEqual(kpi_def.source_table, 'loan_portfolio')

    def test_get_kpi_definition_not_found(self):
        with self.assertRaises(KeyError):
            self.kpi_provider.get_kpi_definition('nonexistent_kpi')

    def test_validate_kpi_value_within_range(self):
        result = self.kpi_provider.validate_kpi_value('default_rate', 0.03)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, 0.03)
        self.assertIsNone(result.breach_type)
        self.assertEqual(result.validation_message, 'Value within acceptable range')

    def test_validate_kpi_value_above_max(self):
        result = self.kpi_provider.validate_kpi_value('default_rate', 0.08)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.breach_type, 'upper_bound')
        self.assertIn('above maximum', result.validation_message)

    def test_validate_kpi_value_below_min(self):
        result = self.kpi_provider.validate_kpi_value('net_interest_margin', 0.01)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.breach_type, 'lower_bound')
        self.assertIn('below minimum', result.validation_message)

    def test_validate_unknown_kpi(self):
        result = self.kpi_provider.validate_kpi_value('unknown_kpi', 0.5)
        self.assertFalse(result.is_valid)
        self.assertIn('not found in registry', result.validation_message)

    def test_detect_anomalies_none(self):
        kpi_values = {'default_rate': 0.03, 'net_interest_margin': 0.05, 'loan_to_value_ratio': 0.7}
        anomalies = self.kpi_provider.detect_anomalies(kpi_values)
        self.assertEqual(len(anomalies), 0)

    def test_detect_anomalies_single(self):
        kpi_values = {'default_rate': 0.08, 'net_interest_margin': 0.05, 'loan_to_value_ratio': 0.7}
        anomalies = self.kpi_provider.detect_anomalies(kpi_values)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0].kpi_name, 'default_rate')
        self.assertEqual(anomalies[0].current_value, 0.08)
        self.assertIn(anomalies[0].severity, ['critical', 'warning', 'info'])

    def test_detect_anomalies_multiple(self):
        kpi_values = {'default_rate': 0.1, 'net_interest_margin': 0.01, 'loan_to_value_ratio': 0.7}
        anomalies = self.kpi_provider.detect_anomalies(kpi_values)
        self.assertEqual(len(anomalies), 2)
        anomaly_names = [a.kpi_name for a in anomalies]
        self.assertIn('default_rate', anomaly_names)
        self.assertIn('net_interest_margin', anomaly_names)

    def test_severity_determination_critical(self):
        severity = self.kpi_provider._determine_severity(value=0.1, expected_range=(0.0, 0.05), breach_type='upper_bound')
        self.assertEqual(severity, 'critical')

    def test_severity_determination_warning(self):
        severity = self.kpi_provider._determine_severity(value=0.06, expected_range=(0.0, 0.05), breach_type='upper_bound')
        self.assertEqual(severity, 'warning')

    def test_severity_determination_info(self):
        severity = self.kpi_provider._determine_severity(value=0.054, expected_range=(0.0, 0.05), breach_type='upper_bound')
        self.assertEqual(severity, 'info')

    def test_get_kpi_context_for_agent(self):
        self.kpi_provider.update_kpi_value('default_rate', 0.03)
        self.kpi_provider.update_kpi_value('net_interest_margin', 0.05)
        context = self.kpi_provider.get_kpi_context_for_agent(['default_rate', 'net_interest_margin'])
        self.assertIn('kpis', context)
        self.assertIn('timestamp', context)
        self.assertEqual(context['total_kpis'], 2)
        self.assertIn('default_rate', context['kpis'])
        dr_context = context['kpis']['default_rate']
        self.assertEqual(dr_context['current_value'], 0.03)
        self.assertTrue(dr_context['is_valid'])

    def test_get_kpi_context_without_values(self):
        context = self.kpi_provider.get_kpi_context_for_agent(['default_rate'])
        self.assertIn('default_rate', context['kpis'])
        dr_context = context['kpis']['default_rate']
        self.assertNotIn('current_value', dr_context)
        self.assertIn('definition', dr_context)

    def test_format_kpi_summary(self):
        self.kpi_provider.update_kpi_value('default_rate', 0.03)
        summary = self.kpi_provider.format_kpi_summary(['default_rate'])
        self.assertIn('📊 KPI Summary', summary)
        self.assertIn('default_rate', summary)
        self.assertIn('Current Value: 0.03', summary)
        self.assertIn('✅', summary)

    def test_format_kpi_summary_with_breach(self):
        self.kpi_provider.update_kpi_value('default_rate', 0.08)
        summary = self.kpi_provider.format_kpi_summary(['default_rate'])
        self.assertIn('❌', summary)
        self.assertIn('above maximum', summary)
if __name__ == '__main__':
    unittest.main()
