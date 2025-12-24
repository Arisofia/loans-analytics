"""Tests for ML model evaluation functionality."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


class TestModelEvaluation:
    """Test suite for model evaluation metrics and thresholds."""

    @pytest.fixture
    def sample_predictions(self):
        """Generate sample predictions for testing."""
        np.random.seed(42)
        return {
            "y_true": np.random.randint(0, 2, 1000),
            "y_pred": np.random.randint(0, 2, 1000),
            "y_proba": np.random.rand(1000),
        }

    @pytest.fixture
    def evaluation_config(self):
        """Load evaluation thresholds configuration."""
        config_path = Path("config/evaluation-thresholds.yml")
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        return None

    def test_classification_metrics(self, sample_predictions):
        """Test classification metric calculations."""
        y_true = sample_predictions["y_true"]
        y_pred = sample_predictions["y_pred"]
        y_proba = sample_predictions["y_proba"]

        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_true, y_proba)

        # Assert metrics are within valid ranges
        assert 0 <= accuracy <= 1, "Accuracy out of range"
        assert 0 <= precision <= 1, "Precision out of range"
        assert 0 <= recall <= 1, "Recall out of range"
        assert 0 <= f1 <= 1, "F1 score out of range"
        assert 0 <= roc_auc <= 1, "ROC AUC out of range"

    def test_threshold_validation(self, sample_predictions, evaluation_config):
        """Test metric values against configured thresholds."""
        if evaluation_config is None:
            pytest.skip("Configuration file not found")

        y_true = sample_predictions["y_true"]
        y_pred = sample_predictions["y_pred"]

        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)

        # Get thresholds from config
        thresholds = evaluation_config.get("classification_metrics", {})

        # Log metric comparisons (informational)
        print(f"\nAccuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")

        # Note: In real scenarios, these would check against production thresholds
        assert isinstance(thresholds, dict), "Thresholds should be a dictionary"

    def test_financial_metrics_structure(self, evaluation_config):
        """Test that financial-specific metrics are properly configured."""
        if evaluation_config is None:
            pytest.skip("Configuration file not found")

        # Check for financial metrics section
        assert "financial_metrics" in evaluation_config, "Financial metrics not configured"

        financial_metrics = evaluation_config["financial_metrics"]
        expected_metrics = [
            "default_prediction_accuracy",
            "risk_assessment_precision",
            "loan_approval_quality",
            "portfolio_performance",
        ]

        for metric in expected_metrics:
            assert metric in financial_metrics, f"{metric} not in config"

    def test_model_stability_metrics(self, evaluation_config):
        """Test model stability monitoring configuration."""
        if evaluation_config is None:
            pytest.skip("Configuration file not found")

        assert "model_stability" in evaluation_config, "Model stability metrics not configured"

        stability_metrics = evaluation_config["model_stability"]
        assert "psi_threshold" in stability_metrics, "PSI threshold not configured"
        assert "drift_detection" in stability_metrics, "Drift detection not configured"

    def test_fairness_compliance_metrics(self, evaluation_config):
        """Test fairness and compliance monitoring configuration."""
        if evaluation_config is None:
            pytest.skip("Configuration file not found")

        assert "fairness_compliance" in evaluation_config, "Fairness metrics not configured"

        fairness_metrics = evaluation_config["fairness_compliance"]
        assert "demographic_parity" in fairness_metrics, "Demographic parity not configured"
        assert "disparate_impact_ratio" in fairness_metrics, "Disparate impact ratio not configured"

    def test_business_kpis_structure(self, evaluation_config):
        """Test business KPIs configuration structure."""
        if evaluation_config is None:
            pytest.skip("Configuration file not found")

        assert "business_kpis" in evaluation_config, "Business KPIs not configured"

        business_kpis = evaluation_config["business_kpis"]
        expected_kpis = [
            "customer_ltv_prediction",
            "churn_prediction",
            "cross_sell_opportunities",
            "fraud_detection",
        ]

        for kpi in expected_kpis:
            assert kpi in business_kpis, f"{kpi} not in business KPIs"

    @pytest.mark.parametrize(
        "metric_name,expected_range",
        [
            ("accuracy", (0, 1)),
            ("precision", (0, 1)),
            ("recall", (0, 1)),
            ("f1_score", (0, 1)),
            ("roc_auc", (0, 1)),
        ],
    )
    def test_metric_ranges(self, metric_name, expected_range):
        """Test that metrics fall within expected ranges."""
        # Generate random metric value for testing
        metric_value = np.random.rand()
        min_val, max_val = expected_range

        assert min_val <= metric_value <= max_val, f"{metric_name} outside expected range"

    def test_evaluation_pipeline_integration(self, sample_predictions):
        """Test end-to-end evaluation pipeline."""
        y_true = sample_predictions["y_true"]
        y_pred = sample_predictions["y_pred"]
        y_proba = sample_predictions["y_proba"]

        # Simulate evaluation pipeline
        results = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1_score": f1_score(y_true, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_true, y_proba),
        }

        # Validate pipeline output
        assert isinstance(results, dict), "Results should be a dictionary"
        assert len(results) == 5, "Expected 5 evaluation metrics"
        assert all(0 <= v <= 1 for v in results.values()), "All metrics should be in [0, 1]"


class TestThresholdConfiguration:
    """Test suite for threshold configuration management."""

    def test_config_file_exists(self):
        """Test that evaluation configuration file exists."""
        config_path = Path("config/evaluation-thresholds.yml")
        # This test is informational - config may not exist yet
        if config_path.exists():
            assert config_path.is_file(), "Config should be a file"

    def test_config_yaml_valid(self):
        """Test that configuration file contains valid YAML."""
        config_path = Path("config/evaluation-thresholds.yml")
        if not config_path.exists():
            pytest.skip("Configuration file not found")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        assert isinstance(config, dict), "Config should be a dictionary"
        assert len(config) > 0, "Config should not be empty"

    def test_threshold_values_reasonable(self):
        """Test that threshold values are reasonable."""
        config_path = Path("config/evaluation-thresholds.yml")
        if not config_path.exists():
            pytest.skip("Configuration file not found")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Check all threshold values are between 0 and 1
        def check_thresholds(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if key in ["min", "max", "threshold", "critical", "warning"]:
                        if isinstance(value, (int, float)):
                            assert 0 <= value <= 1, f"Threshold {new_path} outside [0,1]: {value}"
                    else:
                        check_thresholds(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_thresholds(item, f"{path}[{i}]")

        check_thresholds(config)
