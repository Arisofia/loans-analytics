"""Formula parsing helpers for KPI expressions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedFormula:
    """Structured metadata for a parsed formula string."""

    raw: str
    is_comparison: bool
    is_arithmetic: bool


class FormulaParser:
    """Small parser facade for classifying KPI formulas."""

    def parse(self, formula: str) -> ParsedFormula:
        normalized = formula.strip()
        return ParsedFormula(
            raw=normalized,
            is_comparison=("current_month" in normalized or "previous_month" in normalized),
            is_arithmetic=any(op in normalized for op in [" + ", " - ", " * ", " / "])
            and "(" in normalized,
        )
