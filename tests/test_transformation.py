"""
Tests for the TransformationPhase module.

Validates:
- Null handling strategies
- Type normalization
- Business rule application
- Outlier detection
- Referential integrity checks
"""

import pandas as pd
import pytest

from src.pipeline.transformation import TransformationPhase


@pytest.fixture
def default_config():
    """Default transformation configuration."""
    return {
        "null_handling": {
            "strategy": "smart",
            "fill_values": {"numeric": 0, "categorical": "unknown"},
        },
        "type_normalization": {"enabled": True, "date_format": "%Y-%m-%d"},
        "outlier_detection": {"enabled": True, "method": "iqr", "threshold": 3.0},
    }


@pytest.fixture
def sample_loan_data():
    """Sample loan data for testing."""
    return pd.DataFrame(
        {
            "loan_id": ["L001", "L002", "L003", "L004", "L005"],
            "amount": [10000, 25000, 50000, 75000, 100000],
            "status": ["Active", "DELINQUENT", "active", "Closed", "defaulted"],
            "dpd": [0, 45, 0, 0, 120],
            "borrower_id": ["B001", "B002", "B003", "B004", "B005"],
        }
    )


@pytest.fixture
def data_with_nulls():
    """Sample data with null values."""
    return pd.DataFrame(
        {
            "loan_id": ["L001", "L002", "L003", "L004"],
            "amount": [10000, None, 50000, None],
            "status": ["active", None, "closed", "active"],
            "dpd": [0, 30, None, 60],
        }
    )


class TestTransformationPhaseInit:
    """Test TransformationPhase initialization."""

    def test_init_with_default_config(self, default_config):
        """Test initialization with default configuration."""
        transformer = TransformationPhase(default_config)
        assert transformer.null_strategy == "smart"
        assert transformer.outlier_enabled is True
        assert transformer.outlier_method == "iqr"

    def test_init_with_empty_config(self):
        """Test initialization with empty configuration."""
        transformer = TransformationPhase({})
        assert transformer.null_strategy == "smart"
        assert transformer.outlier_enabled is True

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = {
            "null_handling": {"strategy": "drop"},
            "outlier_detection": {"enabled": False, "method": "zscore", "threshold": 2.0},
        }
        transformer = TransformationPhase(config)
        assert transformer.null_strategy == "drop"
        assert transformer.outlier_enabled is False
        assert transformer.outlier_method == "zscore"


class TestNullHandling:
    """Test null handling functionality."""

    def test_no_nulls_returns_unchanged(self, default_config, sample_loan_data):
        """Test that data without nulls is returned unchanged."""
        transformer = TransformationPhase(default_config)
        df, metrics = transformer._handle_nulls(sample_loan_data)

        assert len(df) == len(sample_loan_data)
        assert metrics["total_nulls"] == 0
        assert metrics["strategy_applied"] == "none"

    def test_drop_strategy(self, data_with_nulls):
        """Test drop strategy removes rows with nulls."""
        config = {"null_handling": {"strategy": "drop"}}
        transformer = TransformationPhase(config)
        df, metrics = transformer._handle_nulls(data_with_nulls)

        # 3 of 4 rows have at least one null (L002, L003, L004), L001 has no nulls
        assert metrics["strategy_applied"] == "drop"
        assert "rows_dropped" in metrics
        assert metrics["rows_dropped"] == 3
        assert len(df) == 1

    def test_fill_strategy(self, data_with_nulls):
        """Test fill strategy fills nulls with defaults."""
        config = {
            "null_handling": {
                "strategy": "fill",
                "fill_values": {"numeric": -1, "categorical": "missing"},
            }
        }
        transformer = TransformationPhase(config)
        df, metrics = transformer._handle_nulls(data_with_nulls)

        assert metrics["strategy_applied"] == "fill"
        assert df["amount"].isnull().sum() == 0
        assert df["status"].isnull().sum() == 0

    def test_smart_strategy(self, data_with_nulls):
        """Test smart strategy applies intelligent null handling."""
        config = {"null_handling": {"strategy": "smart"}}
        transformer = TransformationPhase(config)
        df, metrics = transformer._handle_nulls(data_with_nulls)

        assert metrics["strategy_applied"] == "smart"
        assert "smart_actions" in metrics
        assert metrics["final_total_nulls"] == 0


class TestTypeNormalization:
    """Test type normalization functionality."""

    def test_status_normalization(self, default_config, sample_loan_data):
        """Test status column normalization."""
        transformer = TransformationPhase(default_config)
        df, metrics = transformer._normalize_types(sample_loan_data)

        # All status values should be lowercase
        assert all(s.islower() for s in df["status"].dropna())
        assert "active" in df["status"].values
        assert "delinquent" in df["status"].values
        assert "defaulted" in df["status"].values

    def test_date_normalization(self, default_config):
        """Test date column normalization."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002"],
                "origination_date": ["2024-01-15", "2024-02-20"],
            }
        )
        transformer = TransformationPhase(default_config)
        result_df, metrics = transformer._normalize_types(df)

        assert pd.api.types.is_datetime64_any_dtype(result_df["origination_date"])

    def test_normalization_disabled(self, sample_loan_data):
        """Test that normalization can be disabled."""
        config = {"type_normalization": {"enabled": False}}
        transformer = TransformationPhase(config)
        df, metrics = transformer._normalize_types(sample_loan_data)

        assert metrics["enabled"] is False


class TestBusinessRules:
    """Test business rules application."""

    def test_dpd_bucket_assignment(self, default_config, sample_loan_data):
        """Test DPD bucket assignment."""
        transformer = TransformationPhase(default_config)
        df, metrics = transformer._apply_business_rules(sample_loan_data)

        assert "dpd_bucket" in df.columns
        assert "dpd_bucket_assignment" in metrics["rule_names"]
        # L001 has dpd=0, should be "current"
        assert df[df["loan_id"] == "L001"]["dpd_bucket"].values[0] == "current"
        # L002 has dpd=45, should be "30-59"
        assert df[df["loan_id"] == "L002"]["dpd_bucket"].values[0] == "30-59"
        # L005 has dpd=120, should be "90-179"
        assert df[df["loan_id"] == "L005"]["dpd_bucket"].values[0] == "90-179"

    def test_risk_categorization(self, default_config, sample_loan_data):
        """Test risk category assignment."""
        # Normalize status first
        transformer = TransformationPhase(default_config)
        sample_loan_data, _ = transformer._normalize_types(sample_loan_data)
        df, metrics = transformer._apply_business_rules(sample_loan_data)

        assert "risk_category" in df.columns
        assert "risk_categorization" in metrics["rule_names"]

    def test_amount_tier_classification(self, default_config, sample_loan_data):
        """Test amount tier classification."""
        transformer = TransformationPhase(default_config)
        df, metrics = transformer._apply_business_rules(sample_loan_data)

        assert "amount_tier" in df.columns
        assert "amount_tier_classification" in metrics["rule_names"]
        # 10000 should be "small"
        assert df[df["loan_id"] == "L001"]["amount_tier"].values[0] == "small"
        # 100000 should be "large" (>= 100000 and < 500000)
        assert df[df["loan_id"] == "L005"]["amount_tier"].values[0] == "large"


class TestCustomRules:
    """Test custom business rule application."""

    def test_valid_column_mapping_rule(self, default_config):
        """Test valid column_mapping rule applies correctly."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002", "L003"],
                "status_code": ["A", "D", "C"],
            }
        )
        business_rules = {
            "transformations": [
                {
                    "name": "status_mapping",
                    "type": "column_mapping",
                    "source_column": "status_code",
                    "target_column": "status_full",
                    "mapping": {"A": "Active", "D": "Delinquent", "C": "Closed"},
                }
            ]
        }
        transformer = TransformationPhase(default_config, business_rules=business_rules)
        df_result, metrics = transformer._apply_business_rules(df)

        assert "status_full" in df_result.columns
        assert df_result[df_result["loan_id"] == "L001"]["status_full"].values[0] == "Active"
        assert "status_mapping" in metrics["rule_names"]

    def test_valid_derived_field_rule(self, default_config):
        """Test valid derived_field rule with simple arithmetic."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002"],
                "principal": [10000, 20000],
                "interest": [1000, 2000],
            }
        )
        business_rules = {
            "transformations": [
                {
                    "name": "total_amount",
                    "type": "derived_field",
                    "target_column": "total",
                    "expression": "principal + interest",
                }
            ]
        }
        transformer = TransformationPhase(default_config, business_rules=business_rules)
        df_result, metrics = transformer._apply_business_rules(df)

        assert "total" in df_result.columns
        assert df_result[df_result["loan_id"] == "L001"]["total"].values[0] == 11000
        assert "total_amount" in metrics["rule_names"]

    def test_dangerous_pattern_rejected(self, default_config):
        """Test derived_field rule with dangerous patterns is rejected."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001"],
                "amount": [10000],
            }
        )
        business_rules = {
            "transformations": [
                {
                    "name": "malicious_rule",
                    "type": "derived_field",
                    "target_column": "result",
                    "expression": "__import__('os').system('ls')",
                }
            ]
        }
        transformer = TransformationPhase(default_config, business_rules=business_rules)
        df_result, metrics = transformer._apply_business_rules(df)

        # The dangerous rule should be skipped, so 'result' column should not exist
        assert "result" not in df_result.columns

    def test_invalid_column_mapping_configuration(self, default_config):
        """Test handling of missing/invalid configuration parameters."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001"],
                "status": ["active"],
            }
        )
        business_rules = {
            "transformations": [
                {
                    "name": "invalid_mapping",
                    "type": "column_mapping",
                    # Missing source_column and target_column
                    "mapping": {"A": "Active"},
                }
            ]
        }
        transformer = TransformationPhase(default_config, business_rules=business_rules)
        # Should not raise an error, just log warning and skip the rule
        df_result, metrics = transformer._apply_business_rules(df)

        # Original data should be unchanged (apart from standard business rules)
        assert "loan_id" in df_result.columns


class TestOutlierDetection:
    """Test outlier detection functionality."""

    def test_outlier_detection_iqr(self, default_config):
        """Test IQR outlier detection."""
        # Create data with clear outlier
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002", "L003", "L004", "L005"],
                "amount": [100, 110, 105, 108, 10000],  # 10000 is an outlier
            }
        )
        transformer = TransformationPhase(default_config)
        result_df, metrics = transformer._detect_outliers(df)

        assert metrics["enabled"] is True
        assert metrics["method"] == "iqr"
        assert metrics["total_outlier_rows"] > 0

    def test_outlier_detection_zscore(self):
        """Test Z-score outlier detection."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002", "L003", "L004", "L005"],
                "amount": [100, 110, 105, 108, 10000],
            }
        )
        config = {"outlier_detection": {"enabled": True, "method": "zscore", "threshold": 2.0}}
        transformer = TransformationPhase(config)
        result_df, metrics = transformer._detect_outliers(df)

        assert metrics["method"] == "zscore"

    def test_outlier_detection_disabled(self, sample_loan_data):
        """Test that outlier detection can be disabled."""
        config = {"outlier_detection": {"enabled": False}}
        transformer = TransformationPhase(config)
        df, metrics = transformer._detect_outliers(sample_loan_data)

        assert metrics["enabled"] is False


class TestReferentialIntegrity:
    """Test referential integrity checking."""

    def test_duplicate_loan_id_detection(self, default_config):
        """Test detection of duplicate loan IDs."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L001", "L002"],  # L001 is duplicated
                "amount": [10000, 15000, 20000],
            }
        )
        transformer = TransformationPhase(default_config)
        result_df, metrics = transformer._check_referential_integrity(df)

        assert metrics["issues_found"] > 0
        assert any(i["type"] == "duplicate_primary_key" for i in metrics["issues"])

    def test_null_borrower_id_detection(self, default_config):
        """Test detection of null borrower IDs."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002"],
                "borrower_id": ["B001", None],
            }
        )
        transformer = TransformationPhase(default_config)
        result_df, metrics = transformer._check_referential_integrity(df)

        assert any(i["type"] == "null_foreign_key" for i in metrics["issues"])

    def test_negative_amount_detection(self, default_config):
        """Test detection of negative amounts."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002"],
                "amount": [10000, -5000],  # Negative amount
            }
        )
        transformer = TransformationPhase(default_config)
        result_df, metrics = transformer._check_referential_integrity(df)

        assert any(i["type"] == "negative_value" for i in metrics["issues"])

    def test_clean_data_passes_integrity(self, default_config, sample_loan_data):
        """Test that clean data passes all integrity checks."""
        transformer = TransformationPhase(default_config)
        result_df, metrics = transformer._check_referential_integrity(sample_loan_data)

        assert metrics["integrity_status"] == "pass"
        assert metrics["issues_found"] == 0


class TestExecute:
    """Test the execute method."""

    def test_execute_with_dataframe(self, default_config, sample_loan_data):
        """Test execution with DataFrame input."""
        transformer = TransformationPhase(default_config)
        results = transformer.execute(df=sample_loan_data)

        assert results["status"] == "success"
        assert results["initial_rows"] == 5
        assert results["final_rows"] == 5  # No rows should be removed with smart null handling
        assert "transformation_metrics" in results

    def test_execute_no_data_raises_error(self, default_config):
        """Test that execute raises error when no data provided."""
        transformer = TransformationPhase(default_config)
        results = transformer.execute()

        assert results["status"] == "failed"
        assert "error" in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
