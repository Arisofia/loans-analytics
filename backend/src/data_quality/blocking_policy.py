"""Blocking policy — determines which DQ failures block pipeline progression.

If any blocking-severity rule fails, the pipeline MUST NOT proceed to the
agent/decision layer.  This enforces the hard rule: *No agent bypasses
DQ / covenant / liquidity / policy blocks*.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.src.data_quality.rules import RuleResult, Severity

logger = logging.getLogger(__name__)


def evaluate_blocking(results: List[RuleResult]) -> Dict[str, Any]:
    """Determine pipeline progression based on rule results.

    Returns
    -------
    dict
        ``blocked`` (bool), ``reason`` (list of blocking rule IDs),
        ``summary`` with counts by severity.
    """
    summary = {s.value: 0 for s in Severity}
    blocking_ids: List[str] = []

    for r in results:
        if not r.passed:
            summary[r.severity.value] += 1
            if r.severity == Severity.BLOCKING:
                blocking_ids.append(r.rule_id)

    blocked = len(blocking_ids) > 0

    if blocked:
        logger.warning(
            "Pipeline BLOCKED by %d DQ rule(s): %s",
            len(blocking_ids),
            ", ".join(blocking_ids),
        )
    else:
        logger.info(
            "DQ check passed — %d warnings, %d info",
            summary["warning"] + summary["critical"],
            summary["info"],
        )

    return {
        "blocked": blocked,
        "blocking_rules": blocking_ids,
        "summary": summary,
        "total_checks": len(results),
        "total_failed": sum(1 for r in results if not r.passed),
    }
