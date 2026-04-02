from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ParsedFormula:
    raw: str
    is_comparison: bool
    is_arithmetic: bool

class FormulaParser:

    def parse(self, formula: str) -> ParsedFormula:
        normalized = formula.strip()
        return ParsedFormula(raw=normalized, is_comparison='current_month' in normalized or 'previous_month' in normalized, is_arithmetic=any((op in normalized for op in [' + ', ' - ', ' * ', ' / '])) and '(' in normalized)
