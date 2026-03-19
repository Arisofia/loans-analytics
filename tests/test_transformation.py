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

from backend.src.pipeline.transformation import TransformationPhase


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

    def test_smart_strategy_forces_zero_for_cashflow_fields(self):
        """Cash-flow nulls should be zero-filled, not median/imputed."""
        config = {"null_handling": {"strategy": "smart"}}
        transformer = TransformationPhase(config)
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002", "L003", "L004"],
                "last_payment_amount": [100.0, None, 50.0, None],
                "recovery_value": [None, 10.0, None, 0.0],
            }
        )

        out, metrics = transformer._handle_nulls(df)

        assert out["last_payment_amount"].tolist() == [100.0, 0.0, 50.0, 0.0]
        assert out["recovery_value"].tolist() == [0.0, 10.0, 0.0, 0.0]
        actions = metrics.get("smart_actions", {})
        assert actions.get("last_payment_amount") == "filled_zero (cashflow_semantics)"
        assert actions.get("recovery_value") == "filled_zero (cashflow_semantics)"

    def test_smart_strategy_uses_structural_zero_not_median(self):
        """Financial null values below LOW_NULL_THRESHOLD must use structural zeros + opacity
        flags instead of median imputation."""
        config = {"null_handling": {"strategy": "smart"}}
        transformer = TransformationPhase(config)
        # Build a dataset where null_pct is strictly below LOW_NULL_THRESHOLD_PCT (5.0).
        # 1 null out of 40 rows = 2.5%  <  LOW_NULL_THRESHOLD_PCT → structural-zero path.
        threshold = TransformationPhase.LOW_NULL_THRESHOLD_PCT  # 5.0
        total_rows = int(100 / threshold) * 2  # 40 rows → 2.5% null rate
        values = [float(i) for i in range(1, total_rows)] + [None]
        df = pd.DataFrame({"loan_id": [f"L{i}" for i in range(total_rows)], "amount": values})

        out, metrics = transformer._handle_nulls(df)

        # Null must be filled with 0, not the median
        assert out["amount"].iloc[-1] == 0.0, "Expected structural zero, not median imputation"
        # An opacity flag column must be created
        assert "amount_is_missing" in out.columns
        assert bool(out["amount_is_missing"].iloc[-1]) is True
        # Non-null rows must have flag = False
        assert not out["amount_is_missing"].iloc[0]
        actions = metrics.get("smart_actions", {})
        assert "filled_structural_zero+flag" in actions.get("amount", "")

    def test_structural_zero_flag_preserves_non_null_values(self):
        """Structural-zero fill must not alter existing non-null values."""
        config = {"null_handling": {"strategy": "smart"}}
        transformer = TransformationPhase(config)
        values = [100.0, None, 200.0, 300.0] + [float(i) for i in range(400, 420)]
        df = pd.DataFrame({"loan_id": [f"L{i}" for i in range(24)], "dpd": values})

        out, _ = transformer._handle_nulls(df)

        assert out["dpd"].iloc[0] == 100.0
        assert out["dpd"].iloc[2] == 200.0
        assert out["dpd"].iloc[3] == 300.0


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


class TestCanonicalRiskState:
    """Test canonical upstream kiting/DPD derivation."""

    def test_derive_canonical_risk_state_flags_kiting_and_adjusts_dpd(self, default_config):
        transformer = TransformationPhase(default_config)
        df = pd.DataFrame(
            {
                "dpd": [10.0, 45.0],
                "last_payment_amount": [50.0, 100.0],
                "total_scheduled": [100.0, 100.0],
            }
        )

        out, metrics = transformer._derive_canonical_risk_state(df)

        assert out.loc[0, "ratio_pago_real"] == pytest.approx(0.5)
        assert out.loc[0, "is_kiting_suspected"] == 1
        assert out.loc[0, "dpd_adjusted"] == pytest.approx(90.0)

        assert out.loc[1, "is_kiting_suspected"] == 0
        assert out.loc[1, "dpd_adjusted"] == pytest.approx(45.0)
        assert metrics["kiting_rows"] == 1

    def test_derive_canonical_risk_state_marks_ratio_opaque_when_scheduled_non_positive(
        self, default_config
    ):
        transformer = TransformationPhase(default_config)
        df = pd.DataFrame(
            {
                "dpd": [5.0, 5.0],
                "last_payment_amount": [10.0, 10.0],
                "total_scheduled": [0.0, -1.0],
            }
        )

        out, metrics = transformer._derive_canonical_risk_state(df)

        assert out["ratio_pago_real"].isna().all()
        assert (out["is_kiting_suspected"] == 0).all()
        assert (out["dpd_adjusted"] == out["dpd"]).all()
        assert metrics["opaque_ratio_rows"] == 2

    def test_derive_canonical_risk_state_does_not_flag_new_origination_as_kiting(
        self, default_config
    ):
        """New originations have ratio_pago_real = 0 (no payment received yet).
        They must NOT be flagged as kiting — kiting requires 0 < ratio < 1 (partial payment),
        not zero payment on a new loan whose first payment isn't due yet."""
        transformer = TransformationPhase(default_config)
        df = pd.DataFrame(
            {
                "dpd": [0.0, 10.0],
                "last_payment_amount": [0.0, 0.0],
                "total_scheduled": [100.0, 100.0],
            }
        )

        out, metrics = transformer._derive_canonical_risk_state(df)

        # ratio_pago_real = 0 for both rows
        assert out["ratio_pago_real"].iloc[0] == pytest.approx(0.0)
        assert out["ratio_pago_real"].iloc[1] == pytest.approx(0.0)
        # Neither should be flagged as kiting (no payment was made, not a token payment)
        assert not out["is_kiting_suspected"].iloc[0], "new origination (dpd=0) must not be kiting"
        assert not out["is_kiting_suspected"].iloc[1], "new origination (dpd=10) must not be kiting"
        assert metrics["kiting_rows"] == 0

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

    def test_non_negative_balance_enforcement(self, default_config):
        """Negative current/outstanding balances should be clipped to zero."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002"],
                "amount": [10000, 12000],
                "status": ["active", "delinquent"],
                "dpd": [0, 35],
                "outstanding_balance": [1000.0, -25.0],
                "current_balance": [500.0, -10.0],
            }
        )
        transformer = TransformationPhase(default_config)
        out, metrics = transformer._apply_business_rules(df)

        assert (out["outstanding_balance"] >= 0).all()
        assert (out["current_balance"] >= 0).all()
        assert "non_negative_balance_enforcement" in metrics["rule_names"]


class TestControlMoraDerivations:
    """Test fail-fast and deterministic behavior in control-mora derivations."""

    def test_derive_control_mora_fields_requires_as_of_or_dpd_signal(self, default_config):
        transformer = TransformationPhase(default_config)
        df = pd.DataFrame(
            {
                "loan_id": ["L001"],
                "origination_date": ["2025-01-01"],
                "due_date": ["2025-02-01"],
                # Intentionally no as_of/snapshot/reporting date and no dpd source.
            }
        )

        with pytest.raises(ValueError, match="requires either as_of_date-like columns"):
            transformer._derive_control_mora_fields(df)


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
        # The malicious rule should NOT be in the applied rules list
        assert "malicious_rule" not in metrics["rule_names"]

    def test_derived_field_rejected_when_referencing_pii_column(self, default_config):
        """Derived expressions must not evaluate when they reference PII-like columns."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001"],
                "name": ["Alice"],
                "principal": [10000],
            }
        )
        business_rules = {
            "transformations": [
                {
                    "name": "pii_rule",
                    "type": "derived_field",
                    "target_column": "risk_feature",
                    "expression": "principal + name",
                }
            ]
        }
        transformer = TransformationPhase(default_config, business_rules=business_rules)
        df_result, metrics = transformer._apply_business_rules(df)

        assert "risk_feature" not in df_result.columns
        assert "pii_rule" not in metrics["rule_names"]

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
        # The invalid rule should NOT be in the applied rules list
        assert "invalid_mapping" not in metrics["rule_names"]


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

    def test_outlier_detection_with_nan_values(self, default_config):
        """Test that outlier detection handles NaN values gracefully."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002", "L003", "L004", "L005"],
                "amount": [100, None, 105, None, 10000],  # Contains NaN values
            }
        )
        transformer = TransformationPhase(default_config)
        result_df, metrics = transformer._detect_outliers(df)

        # Should not fail with NaN values
        assert metrics["enabled"] is True
        # NaN values should not be flagged as outliers
        if "amount_outlier" in result_df.columns:
            # Check that NaN positions in original data are False (not outliers)
            nan_positions = df["amount"].isna()
            assert not result_df.loc[nan_positions, "amount_outlier"].any()

    def test_outlier_detection_iqr_identical_values(self, default_config):
        """Test IQR detection when all values are identical (IQR = 0)."""
        df = pd.DataFrame(
            {
                "loan_id": ["L001", "L002", "L003", "L004", "L005"],
                "amount": [100, 100, 100, 100, 100],  # All identical
            }
        )
        transformer = TransformationPhase(default_config)
        result_df, metrics = transformer._detect_outliers(df)

        # When IQR = 0, no values should be flagged as outliers
        assert metrics["enabled"] is True
        # No outliers should be detected when all values are identical
        assert metrics["total_outlier_rows"] == 0


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
        with pytest.raises(ValueError, match="No data provided for transformation"):
            transformer.execute()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
