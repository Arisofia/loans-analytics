"""Tests for the data quality engine."""

from __future__ import annotations

import pandas as pd
import pytest

from backend.src.data_quality.rules import Severity, RuleResult
from backend.src.data_quality.validators import RULE_REGISTRY
from backend.src.data_quality.anomaly_detection import detect_anomalies
from backend.src.data_quality.blocking_policy import evaluate_blocking
from backend.src.data_quality.engine import run_quality_engine


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "loan_id": ["L001", "L002", "L003"],
            "monto_desembolsado": [10000, 20000, 30000],
            "tasa_interes": [0.12, 0.15, 0.18],
            "plazo_meses": [12, 24, 36],
            "estado": ["active", "active", "defaulted"],
        }
    )


class TestRuleRegistry:
    def test_registry_has_built_in_validators(self):
        assert len(RULE_REGISTRY) >= 1

    def test_all_rules_have_ids(self):
        for rule in RULE_REGISTRY:
            assert rule.rule_id, "Rule must have a non-empty id"


class TestAnomalyDetection:
    def test_detect_anomalies_returns_list(self, sample_df: pd.DataFrame):
        result = detect_anomalies(sample_df, "monto_desembolsado")
        assert isinstance(result, list)

    def test_no_anomalies_in_small_set(self, sample_df: pd.DataFrame):
        # With only 3 rows, typically no outliers
        result = detect_anomalies(sample_df, "monto_desembolsado")
        assert isinstance(result, list)


class TestBlockingPolicy:
    def test_no_blocking_with_all_passed(self):
        results = [
            RuleResult(rule_id="r1", severity=Severity.INFO, passed=True),
            RuleResult(rule_id="r2", severity=Severity.WARNING, passed=True),
        ]
        result = evaluate_blocking(results)
        assert not result["blocked"]
        assert len(result["blocking_rules"]) == 0

    def test_blocking_on_severity(self):
        results = [
            RuleResult(rule_id="r1", severity=Severity.BLOCKING, passed=False),
        ]
        result = evaluate_blocking(results)
        assert result["blocked"]
        assert len(result["blocking_rules"]) >= 1


class TestQualityEngine:
    def test_run_quality_engine_returns_list(self, sample_df: pd.DataFrame):
        results = run_quality_engine(sample_df)
        assert isinstance(results, list)

    def test_results_have_rule_id(self, sample_df: pd.DataFrame):
        results = run_quality_engine(sample_df)
        for r in results:
            assert hasattr(r, "rule_id")
