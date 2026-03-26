"""Data-quality engine — run all registered rules + anomaly checks on mart bundle.

Entry-point: ``run_quality_engine(marts)`` returns a full DQ report including
pass/fail per rule, anomaly scan, and blocking decision.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

from backend.src.data_quality.anomaly_detection import AnomalyReport, run_anomaly_scan
from backend.src.data_quality.blocking_policy import evaluate_blocking
from backend.src.data_quality.rules import RuleResult, list_rules

# Force registration of built-in validators on first import
import backend.src.data_quality.validators as _validators  # noqa: F401

logger = logging.getLogger(__name__)


def run_quality_engine(
    marts: Dict[str, pd.DataFrame],
    anomaly_method: str = "zscore",
) -> Dict[str, Any]:
    """Execute all DQ rules and anomaly detection across all marts.

    Returns
    -------
    dict
        Keys: ``rule_results``, ``anomaly_reports``, ``blocking``, ``mart_summaries``.
    """
    all_results: List[RuleResult] = []
    all_anomalies: List[AnomalyReport] = []
    mart_summaries: Dict[str, Dict[str, Any]] = {}

    for mart_name, df in marts.items():
        if df.empty:
            logger.debug("Skipping empty mart: %s", mart_name)
            continue

        # Run applicable rules
        rules = list_rules(mart=mart_name) + list_rules(mart=None)
        # Deduplicate by rule_id
        seen_ids: set[str] = set()
        unique_rules = []
        for r in rules:
            if r.rule_id not in seen_ids:
                unique_rules.append(r)
                seen_ids.add(r.rule_id)

        mart_results: List[RuleResult] = []
        for rule in unique_rules:
            try:
                result = rule.check_fn(df)
                mart_results.append(result)
            except Exception:
                logger.exception("Rule %s failed on %s", rule.rule_id, mart_name)
                mart_results.append(RuleResult(
                    rule_id=rule.rule_id,
                    passed=False,
                    severity=rule.severity,
                    detail={"error": "rule execution failed"},
                ))

        all_results.extend(mart_results)

        # Anomaly scan on numeric columns
        anomalies = run_anomaly_scan(df, method=anomaly_method)
        all_anomalies.extend(anomalies)

        mart_summaries[mart_name] = {
            "row_count": len(df),
            "rules_run": len(mart_results),
            "rules_failed": sum(1 for r in mart_results if not r.passed),
            "anomalies_found": sum(a.outlier_count for a in anomalies),
        }

    blocking = evaluate_blocking(all_results)

    logger.info(
        "DQ engine: %d rules, %d failed, blocked=%s",
        len(all_results),
        sum(1 for r in all_results if not r.passed),
        blocking["blocked"],
    )

    return {
        "rule_results": [
            {
                "rule_id": r.rule_id,
                "passed": r.passed,
                "severity": r.severity.value,
                "detail": r.detail,
                "affected_rows": r.affected_rows,
            }
            for r in all_results
        ],
        "anomaly_reports": [
            {
                "column": a.column,
                "method": a.method,
                "outlier_count": a.outlier_count,
                "total_count": a.total_count,
                "outlier_pct": a.outlier_pct,
            }
            for a in all_anomalies
        ],
        "blocking": blocking,
        "mart_summaries": mart_summaries,
    }
