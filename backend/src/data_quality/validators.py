"""Built-in validators — concrete DQ checks for loan portfolio marts.

Each validator is a function ``(pd.DataFrame) -> RuleResult`` that is
auto-registered into the rule catalogue on import.
"""

from __future__ import annotations

import pandas as pd

from backend.src.data_quality.rules import RULE_REGISTRY, Rule, RuleResult, Severity, register
from backend.src.pipeline.transformation import CANONICAL_LOAN_STATUSES

__all__ = ["RULE_REGISTRY"]


# ── Completeness checks ─────────────────────────────────────────────────
def _check_required_fields(df: pd.DataFrame) -> RuleResult:
    required = {"loan_id", "borrower_id", "amount", "status"}
    missing = required - set(df.columns)
    if missing:
        return RuleResult(
            rule_id="required_fields",
            passed=False,
            severity=Severity.BLOCKING,
            detail={"missing_columns": sorted(missing)},
        )
    null_counts = {c: int(df[c].isna().sum()) for c in required if c in df.columns}
    bad = {k: v for k, v in null_counts.items() if v > 0}
    return RuleResult(
        rule_id="required_fields",
        passed=len(bad) == 0,
        severity=Severity.BLOCKING,
        detail={"null_counts": bad},
        affected_rows=sum(bad.values()),
    )


register(
    Rule(
        rule_id="required_fields",
        description="All required columns must be present and non-null",
        severity=Severity.BLOCKING,
        check_fn=_check_required_fields,
    )
)


# ── Uniqueness checks ───────────────────────────────────────────────────
def _check_loan_id_unique(df: pd.DataFrame) -> RuleResult:
    if "loan_id" not in df.columns:
        return RuleResult(rule_id="loan_id_unique", passed=True, severity=Severity.CRITICAL)
    dupes = int(df["loan_id"].duplicated().sum())
    return RuleResult(
        rule_id="loan_id_unique",
        passed=dupes == 0,
        severity=Severity.CRITICAL,
        detail={"duplicate_count": dupes},
        affected_rows=dupes,
    )


register(
    Rule(
        rule_id="loan_id_unique",
        description="loan_id must be unique within the mart",
        severity=Severity.CRITICAL,
        check_fn=_check_loan_id_unique,
        mart="portfolio_mart",
    )
)


# ── Range checks ────────────────────────────────────────────────────────
def _check_amount_positive(df: pd.DataFrame) -> RuleResult:
    if "amount" not in df.columns:
        return RuleResult(rule_id="amount_positive", passed=True, severity=Severity.WARNING)
    amt = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    bad = int((amt <= 0).sum())
    return RuleResult(
        rule_id="amount_positive",
        passed=bad == 0,
        severity=Severity.WARNING,
        detail={"non_positive_count": bad},
        affected_rows=bad,
    )


register(
    Rule(
        rule_id="amount_positive",
        description="Loan amount must be > 0",
        severity=Severity.WARNING,
        check_fn=_check_amount_positive,
    )
)


def _check_interest_rate_range(df: pd.DataFrame) -> RuleResult:
    if "interest_rate" not in df.columns:
        return RuleResult(rule_id="interest_rate_range", passed=True, severity=Severity.WARNING)
    rate = pd.to_numeric(df["interest_rate"], errors="coerce").fillna(0)
    out_of_range = int(((rate < 0) | (rate > 100)).sum())
    return RuleResult(
        rule_id="interest_rate_range",
        passed=out_of_range == 0,
        severity=Severity.WARNING,
        detail={"out_of_range_count": out_of_range},
        affected_rows=out_of_range,
    )


register(
    Rule(
        rule_id="interest_rate_range",
        description="Interest rate must be between 0% and 100%",
        severity=Severity.WARNING,
        check_fn=_check_interest_rate_range,
    )
)


# ── Status enum check ───────────────────────────────────────────────────
def _check_valid_status(df: pd.DataFrame) -> RuleResult:
    allowed = CANONICAL_LOAN_STATUSES
    if "status" not in df.columns:
        return RuleResult(rule_id="valid_status", passed=True, severity=Severity.CRITICAL)
    invalid = df[~df["status"].str.lower().isin(allowed)]
    return RuleResult(
        rule_id="valid_status",
        passed=len(invalid) == 0,
        severity=Severity.CRITICAL,
        detail={"invalid_values": invalid["status"].unique().tolist()[:10]} if len(invalid) else {},
        affected_rows=len(invalid),
    )


register(
    Rule(
        rule_id="valid_status",
        description="Status must be one of: active, delinquent, defaulted, closed",
        severity=Severity.CRITICAL,
        check_fn=_check_valid_status,
    )
)
