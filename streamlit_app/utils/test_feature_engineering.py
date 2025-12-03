import unittest
import pandas as pd
from .feature_engineering import FeatureEngineer

class TestFeatureEngineering(unittest.TestCase):
    """Unit tests for the FeatureEngineer class."""

    def setUp(self):
        """Set up sample data for testing."""
        self.sample_data = pd.DataFrame({
            'revenue': [40000, 80000, 120000],
            'balance': [10000, 25000, 75000],
            'limit': [20000, 100000, 100000],
            'dpd': [0, 45, 91]
        })
        self.sparse_data = pd.DataFrame({
            'revenue': [40000, 80000, 120000]
        })

    def test_enrichment_adds_all_columns(self):
        """Test that enrichment adds utilization, dpd_bucket, and segment columns."""
        enriched_df = FeatureEngineer.enrich_portfolio(self.sample_data)
        self.assertIn('utilization', enriched_df.columns)
        self.assertIn('dpd_bucket', enriched_df.columns)
        self.assertIn('segment', enriched_df.columns)

    def test_enrichment_values_are_correct(self):
        """Test that sample rows map to expected segment, bucket, and utilization values."""
        enriched_df = FeatureEngineer.enrich_portfolio(self.sample_data)

        # Test utilization
        self.assertAlmostEqual(enriched_df.loc[0, 'utilization'], 0.5)
        self.assertAlmostEqual(enriched_df.loc[1, 'utilization'], 0.25)
        self.assertAlmostEqual(enriched_df.loc[2, 'utilization'], 0.75)

        # Test DPD bucket
        self.assertEqual(enriched_df.loc[0, 'dpd_bucket'], 'Current')
        self.assertEqual(enriched_df.loc[1, 'dpd_bucket'], '31-60 DPD')
        self.assertEqual(enriched_df.loc[2, 'dpd_bucket'], '90+ DPD')

        # Test segment
        self.assertEqual(enriched_df.loc[0, 'segment'], 'Bronze')
        self.assertEqual(enriched_df.loc[1, 'segment'], 'Silver')
        self.assertEqual(enriched_df.loc[2, 'segment'], 'Gold')

    def test_enrichment_graceful_with_sparse_inputs(self):
        """Test that enrichment only adds segment when other columns are missing."""
        enriched_df = FeatureEngineer.enrich_portfolio(self.sparse_data)
        self.assertIn('segment', enriched_df.columns)
        self.assertNotIn('utilization', enriched_df.columns)
        self.assertNotIn('dpd_bucket', enriched_df.columns)
        self.assertEqual(enriched_df.loc[0, 'segment'], 'Bronze')

    def test_enrichment_does_not_mutate_original_dataframe(self):
        """Test that the original dataframe is not mutated."""
        original_columns = self.sample_data.columns.tolist()
        FeatureEngineer.enrich_portfolio(self.sample_data)
        self.assertEqual(self.sample_data.columns.tolist(), original_columns)

if __name__ == '__main__':
    unittest.main()
