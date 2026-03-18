#!/usr/bin/env python3
"""AFL++ harness for KPIFormulaEngine formula parsing.

Usage example:
  afl-fuzz -i fuzz_inputs -o fuzz_out -- python scripts/testing/kpi_formula_afl_harness.py
"""

from __future__ import annotations

import sys

import pandas as pd

from backend.src.pipeline.calculation import KPIFormulaEngine


def main() -> int:
    payload = sys.stdin.buffer.read().decode("utf-8", errors="ignore")
    if not payload:
        return 0

    df = pd.DataFrame(
        {
            "origination_date": ["2025-01-01", "2025-02-01"],
            "outstanding_balance": [100.0, 120.0],
            "status": ["Current", "Late"],
        }
    )
    engine = KPIFormulaEngine(df)
    _ = engine.calculate(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
