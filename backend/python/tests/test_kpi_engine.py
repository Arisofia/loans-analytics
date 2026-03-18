"""Tests for KPIEngineV2 audit trail functionality."""

import unittest
from datetime import datetime
from decimal import Decimal

import pandas as pd

from backend.python.kpis.engine import KPIEngineV2


class TestKPIEngineV2(unittest.TestCase):
    """Test KPIEngineV2 class and audit trail functionality."""

    def setUp(self):
        """Set up test data before each test."""
        # Create sample data for KPI calculations
        self.sample_df = pd.DataFrame(
            {
                "dpd_30_60_usd": [100.0, 200.0, 150.0],
                "dpd_60_90_usd": [50.0, 75.0, 100.0],
                "dpd_90_plus_usd": [25.0, 50.0, 75.0],
                "total_receivable_usd": [5000.0, 6000.0, 7000.0],
            }
        )

        self.empty_df = pd.DataFrame()

    def test_engine_initialization(self):
        """Test KPIEngineV2 initialization."""
        engine = KPIEngineV2(self.sample_df, actor="test_user", run_id="test_run_001")

        self.assertEqual(engine.actor, "test_user")
        self.assertEqual(engine.run_id, "test_run_001")
        self.assertIsInstance(engine.df, pd.DataFrame)
        self.assertEqual(len(engine._audit_records), 0)

    def test_engine_initialization_with_defaults(self):
        """Test KPIEngineV2 initialization with default values."""
        engine = KPIEngineV2(self.sample_df)

        self.assertEqual(engine.actor, "system")
        self.assertIsNotNone(engine.run_id)
        # Run ID should be in YYYYMMDD_HHMMSS format
        self.assertRegex(engine.run_id, r"\d{8}_\d{6}")

    def test_calculate_par_30(self):
        """Test PAR30 calculation with audit trail."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")

        value, context = engine.calculate_par_30()

        # Check that value is calculated correctly
        self.assertIsInstance(value, Decimal)
        self.assertGreaterEqual(value, 0.0)

        # Check context structure
        self.assertIn("formula", context)
        self.assertIn("rows_processed", context)
        self.assertEqual(context["rows_processed"], 3)

        # Check audit trail was recorded
        self.assertEqual(len(engine._audit_records), 1)
        audit_record = engine._audit_records[0]
        self.assertEqual(audit_record["kpi_name"], "PAR30")
        self.assertEqual(audit_record["status"], "success")
        self.assertEqual(audit_record["value"], value)

    def test_calculate_collection_rate(self):
        """Test collection rate calculation with audit trail."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")

        value, context = engine.calculate_collection_rate()

        # Check that value is calculated
        self.assertIsInstance(value, Decimal)

        # Check context structure
        self.assertIn("formula", context)
        self.assertIn("rows_processed", context)

        # Check audit trail
        self.assertEqual(len(engine._audit_records), 1)
        audit_record = engine._audit_records[0]
        self.assertEqual(audit_record["kpi_name"], "COLLECTION_RATE")
        self.assertEqual(audit_record["status"], "success")

    def test_calculate_ltv(self):
        """Test LTV calculation (on-demand KPI)."""
        # Create data with loan and collateral columns
        df_with_ltv = pd.DataFrame(
            {
                "loan_amount": [1000.0, 2000.0, 3000.0],
                "collateral_value": [1500.0, 2500.0, 4000.0],
            }
        )

        engine = KPIEngineV2(df_with_ltv, actor="test_user")
        value, context = engine.calculate_ltv()

        # Check calculation
        self.assertIsInstance(value, float)
        self.assertGreaterEqual(value, 0.0)

        # Check audit trail
        self.assertEqual(len(engine._audit_records), 1)
        audit_record = engine._audit_records[0]
        self.assertEqual(audit_record["kpi_name"], "LTV")

    def test_calculate_all(self):
        """Test calculate_all method."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")

        results = engine.calculate_all()

        # Check results structure
        self.assertIsInstance(results, dict)
        self.assertIn("PAR30", results)
        self.assertIn("COLLECTION_RATE", results)
        self.assertIn("LTV", results)

        # Each KPI should have value and context
        for _kpi_name, kpi_data in results.items():
            self.assertIn("value", kpi_data)
            self.assertIn("context", kpi_data)

        # Check that audit trail has records for standard KPIs
        self.assertGreaterEqual(len(engine._audit_records), 3)

    def test_get_audit_trail(self):
        """Test get_audit_trail method returns proper DataFrame."""
        engine = KPIEngineV2(self.sample_df, actor="test_user", run_id="test_run_001")

        # Calculate some KPIs to populate audit trail
        engine.calculate_all()

        # Get audit trail
        audit_df = engine.get_audit_trail()

        # Check DataFrame structure
        self.assertIsInstance(audit_df, pd.DataFrame)
        self.assertGreater(len(audit_df), 0)

        # Check required columns
        required_columns = [
            "timestamp",
            "run_id",
            "actor",
            "kpi_name",
            "value",
            "context",
            "error",
            "status",
        ]
        for col in required_columns:
            self.assertIn(col, audit_df.columns)

        # Check data consistency
        self.assertTrue(all(audit_df["run_id"] == "test_run_001"))
        self.assertTrue(all(audit_df["actor"] == "test_user"))

    def test_get_audit_trail_empty(self):
        """Test get_audit_trail when no calculations have been performed."""
        engine = KPIEngineV2(self.sample_df)

        audit_df = engine.get_audit_trail()

        # Should return empty DataFrame with correct columns
        self.assertIsInstance(audit_df, pd.DataFrame)
        self.assertEqual(len(audit_df), 0)

        # Check columns exist even when empty
        required_columns = [
            "timestamp",
            "run_id",
            "actor",
            "kpi_name",
            "value",
            "context",
            "error",
            "status",
        ]
        for col in required_columns:
            self.assertIn(col, audit_df.columns)

    def test_error_handling_in_calculations(self):
        """Test that errors raise ValueError per fail-fast mandate."""
        # Create data missing required columns for PAR30
        invalid_df = pd.DataFrame(
            {
                "some_column": [1, 2, 3],
            }
        )

        engine = KPIEngineV2(invalid_df, actor="test_user")

        # Calculate PAR30 (should raise ValueError due to missing columns)
        with self.assertRaises(ValueError) as cm:
            engine.calculate_par_30()
        
        self.assertIn("CRITICAL: PAR30 calculation failed", str(cm.exception))

    def test_individual_kpi_failure_isolation(self):
        """Test that individual KPI failures are still reported in calculate_all."""
        # Use invalid data that will cause PAR30 to fail
        invalid_df = pd.DataFrame(
            {
                "some_column": [1, 2, 3],
            }
        )

        engine = KPIEngineV2(invalid_df, actor="test_user")

        # If calculate_all catches exceptions, it should still return results
        # However, per our new fail-fast refactor, if we want it to crash the whole batch,
        # we would let it raise. If we want it to be isolated, we catch it inside calculate_all.
        # Currently KPIEngineV2.calculate_all DOES NOT catch exceptions for standard KPIs,
        # so it should raise.
        
        with self.assertRaises(ValueError):
            engine.calculate_all()

    def test_audit_trail_timestamp_format(self):
        """Test that timestamps in audit trail are properly formatted."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")
        engine.calculate_par_30()

        audit_df = engine.get_audit_trail()
        timestamp_str = audit_df.iloc[0]["timestamp"]

        # Should be ISO format timestamp
        self.assertIsInstance(timestamp_str, str)
        # Should be parseable as datetime
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        self.assertIsInstance(parsed_timestamp, datetime)

    def test_context_serialization(self):
        """Test that context dictionaries are properly serialized in audit trail."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")
        engine.calculate_par_30()

        audit_df = engine.get_audit_trail()
        context_str = audit_df.iloc[0]["context"]

        # Context should be converted to string for CSV export
        self.assertIsInstance(context_str, str)


if __name__ == "__main__":
    unittest.main()

