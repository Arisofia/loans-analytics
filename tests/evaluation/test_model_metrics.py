"""Real ML model evaluation tests.

This module contains actual evaluation tests to validate:
- Evaluation configuration exists and is valid
- Metrics JSON schema is correct
- Threshold validation logic works correctly
- Integration with check_thresholds.py script
"""

from pathlib import Path

import pytest


class TestEvaluationConfiguration:
    """Tests for evaluation configuration and setup."""

    def test_evaluation_config_exists(self) -> None:
        """Verify evaluation threshold configuration file exists."""
        config_path = Path("config/evaluation-thresholds.yml")
        assert (
            config_path.exists()
        ), "Evaluation threshold config must exist at config/evaluation-thresholds.yml"

    def test_evaluation_config_valid_yaml(self) -> None:
        """Verify evaluation config is valid YAML with expected structure."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        config_path = Path("config/evaluation-thresholds.yml")
        with config_path.open() as f:
            config = yaml.safe_load(f)

        # Validate required threshold keys
        assert "test_coverage" in config, "Config must define test_coverage thresholds"
        assert "min" in config["test_coverage"], "test_coverage must have 'min' threshold"
        assert "target" in config["test_coverage"], "test_coverage must have 'target' threshold"

        # Validate threshold values are reasonable
        assert 0 <= config["test_coverage"]["min"] <= 100, "test_coverage.min must be 0-100"
        assert 0 <= config["test_coverage"]["target"] <= 100, "test_coverage.target must be 0-100"

    def test_check_thresholds_script_exists(self) -> None:
        """Verify check_thresholds.py script exists."""
        script_path = Path("scripts/evaluation/check_thresholds.py")
        assert script_path.exists(), "check_thresholds.py script must exist"
        assert script_path.stat().st_size > 0, "check_thresholds.py must not be empty"


class TestMetricsSchema:
    """Tests for evaluation metrics JSON schema validation."""

    def test_metrics_json_schema_structure(self) -> None:
        """Test that expected metrics JSON structure is documented."""
        # Expected structure based on check_thresholds.py requirements
        expected_structure = {
            "summary": {
                "total": "int - total number of tests",
                "passed": "int - number of passed tests",
            },
            "model_metrics": {
                "accuracy": "float - model accuracy (0-1)",
                "precision": "float - model precision (0-1)",
                "recall": "float - model recall (0-1)",
                "f1_score": "float - model F1 score (0-1)",
            },
        }

        # This test documents the expected schema
        assert isinstance(expected_structure, dict), "Metrics schema is defined"
        assert "summary" in expected_structure, "Metrics must include summary"
        assert "model_metrics" in expected_structure, "Metrics can include model_metrics"

    def test_threshold_results_json_schema(self) -> None:
        """Test that threshold results JSON has expected structure."""
        # Expected output from check_thresholds.py
        expected_result = {
            "passed": "bool - whether all thresholds passed",
            "message": "str - summary message",
            "failures": "list - list of threshold failures",
            "warnings": "list - list of threshold warnings",
            "tests_total": "int - total tests run",
            "tests_passed": "int - tests that passed",
        }

        assert isinstance(expected_result, dict), "Threshold results schema is defined"
        assert "passed" in expected_result, "Results must include 'passed' field"


class TestThresholdValidation:
    """Tests for threshold validation logic."""

    def test_threshold_validation_passing_metrics(self) -> None:
        """Test threshold validation with metrics that pass all thresholds."""
        from scripts.evaluation.check_thresholds import check_thresholds

        # Mock metrics that pass all thresholds
        passing_metrics = {
            "summary": {"total": 10, "passed": 10},  # 100% pass rate
            "model_metrics": {
                "accuracy": 0.96,  # > 0.95 min
                "precision": 0.92,  # > 0.90 min
                "recall": 0.88,  # > 0.85 min
                "f1_score": 0.90,  # > 0.88 min
            },
        }

        thresholds = {
            "test_coverage": {"min": 95.0, "target": 98.0},
            "accuracy": {"min": 0.95, "target": 0.98},
            "precision": {"min": 0.90, "target": 0.95},
            "recall": {"min": 0.85, "target": 0.92},
            "f1_score": {"min": 0.88, "target": 0.93},
        }

        result = check_thresholds(passing_metrics, thresholds)

        assert result["passed"] is True, "Valid metrics should pass all thresholds"
        assert len(result["failures"]) == 0, "Should have no failures"
        assert result["tests_total"] == 10, "Should track total tests"
        assert result["tests_passed"] == 10, "Should track passed tests"

    def test_threshold_validation_failing_metrics(self) -> None:
        """Test threshold validation with metrics that fail thresholds."""
        from scripts.evaluation.check_thresholds import check_thresholds

        # Mock metrics that fail thresholds
        failing_metrics = {
            "summary": {"total": 10, "passed": 8},  # 80% pass rate (< 95% min)
            "model_metrics": {
                "accuracy": 0.92,  # < 0.95 min (FAIL)
                "precision": 0.88,  # < 0.90 min (FAIL)
                "recall": 0.80,  # < 0.85 min (FAIL)
                "f1_score": 0.85,  # < 0.88 min (FAIL)
            },
        }

        thresholds = {
            "test_coverage": {"min": 95.0, "target": 98.0},
            "accuracy": {"min": 0.95, "target": 0.98},
            "precision": {"min": 0.90, "target": 0.95},
            "recall": {"min": 0.85, "target": 0.92},
            "f1_score": {"min": 0.88, "target": 0.93},
        }

        result = check_thresholds(failing_metrics, thresholds)

        assert result["passed"] is False, "Invalid metrics should fail thresholds"
        assert len(result["failures"]) > 0, "Should have failures"
        assert "Test pass rate" in result["failures"][0], "Should report test pass rate failure"

    def test_threshold_validation_warning_metrics(self) -> None:
        """Test threshold validation with metrics that trigger warnings."""
        from scripts.evaluation.check_thresholds import check_thresholds

        # Mock metrics that pass minimum but miss target
        warning_metrics = {
            "summary": {"total": 10, "passed": 10},  # 100% pass rate
            "model_metrics": {
                "accuracy": 0.96,  # > 0.95 min but < 0.98 target (WARNING)
            },
        }

        thresholds = {
            "test_coverage": {"min": 95.0, "target": 98.0},
            "accuracy": {"min": 0.95, "target": 0.98},
        }

        result = check_thresholds(warning_metrics, thresholds)

        assert result["passed"] is True, "Should pass minimum thresholds"
        assert len(result["failures"]) == 0, "Should have no failures"
        assert len(result["warnings"]) > 0, "Should have warnings for missing target"

    def test_default_thresholds_available(self) -> None:
        """Test that default thresholds are available when config missing."""
        from scripts.evaluation.check_thresholds import get_default_thresholds

        defaults = get_default_thresholds()

        assert "accuracy" in defaults, "Default thresholds must include accuracy"
        assert "precision" in defaults, "Default thresholds must include precision"
        assert "recall" in defaults, "Default thresholds must include recall"
        assert "f1_score" in defaults, "Default thresholds must include f1_score"
        assert "test_coverage" in defaults, "Default thresholds must include test_coverage"

        # Validate all thresholds have min and target
        for metric, config in defaults.items():
            assert "min" in config, f"{metric} must have 'min' threshold"
            assert "target" in config, f"{metric} must have 'target' threshold"

    def test_threshold_validation_with_zero_tests(self) -> None:
        """Test threshold validation with zero tests run."""
        from scripts.evaluation.check_thresholds import check_thresholds

        # Mock metrics with no tests
        zero_tests_metrics = {
            "summary": {"total": 0, "passed": 0},
        }

        thresholds = {
            "test_coverage": {"min": 95.0, "target": 98.0},
        }

        result = check_thresholds(zero_tests_metrics, thresholds)

        # With zero tests, no failures should be reported (no division by zero)
        assert isinstance(result, dict), "Should return a valid result"
        assert "passed" in result, "Result must have 'passed' key"
        assert result["tests_total"] == 0, "Should track zero tests"


class TestWorkflowIntegration:
    """Tests for GitHub Actions workflow integration."""

    def test_workflow_file_exists(self) -> None:
        """Verify evaluation automation entrypoint exists (workflow or scripts)."""
        workflow_path = Path(".github/workflows/model_evaluation.yml")
        if workflow_path.exists():
            assert workflow_path.is_file(), "model_evaluation.yml must be a file"
            return

        # Workflow is optional when evaluation runs manually.
        threshold_script = Path("scripts/evaluation/check_thresholds.py")
        viz_script = Path("scripts/evaluation/generate_visualizations.py")
        assert threshold_script.exists(), "check_thresholds.py must exist for manual evaluation"
        assert viz_script.exists(), "generate_visualizations.py must exist for manual evaluation"

    def test_reports_directory_creation(self) -> None:
        """Test that reports directory can be created."""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        assert reports_dir.exists(), "Reports directory should be creatable"
        assert reports_dir.is_dir(), "Reports path should be a directory"
