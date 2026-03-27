from __future__ import annotations

from typing import Any, List

import pandas as pd

from backend.src.data_quality.rules import (
    RULE_REGISTRY,
    RuleResult,
    find_duplicate_loans,
    find_impossible_dpd,
    find_missing_required_ids,
)


def run_data_quality(loans_df: pd.DataFrame) -> dict[str, Any]:
    missing = find_missing_required_ids(loans_df)
    duplicates = find_duplicate_loans(loans_df)
    impossible = find_impossible_dpd(loans_df)

    blocking_issues: list[str] = []
    warnings: list[str] = []

    if missing:
        blocking_issues.append(f"missing_ids: {missing}")
    if duplicates > 0:
        warnings.append(f"duplicate_loans: {duplicates}")
    if impossible > 0:
        warnings.append(f"impossible_dpd: {impossible}")

    total_checks = 3
    passed = total_checks - len(blocking_issues) - len(warnings)
    quality_score = round(passed / total_checks, 2) if total_checks else 1.0

    return {
        "quality_score": quality_score,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
    }


def run_quality_engine(df: pd.DataFrame) -> List[RuleResult]:
    """Run all registered DQ rules and return list of RuleResult."""
    # Ensure validators are registered
    import backend.src.data_quality.validators  # noqa: F401

    results: List[RuleResult] = []
    for rule in RULE_REGISTRY:
        result = rule.check_fn(df)
        results.append(result)
    return results
