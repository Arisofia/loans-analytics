"""
PHASE 1 — CRITICAL STABILIZATION TEST SUITE

Regulatory-grade scrutiny applied to fintech lending analytics system.
All defects that cause silent failures, incorrect financial output, or runtime crashes
are tested here before any analyst sees a number.

Test Categories:
- FormulaExecutionError: Ensures formula failures raise exceptions (F1.3)
- Dependency versions: Validates pip-resolvable package versions (F1.1, F1.4)
- Makefile configuration: Ensures kpis target requires explicit input (F1.2)
- Package namespace: Validates no interpreter shadowing (F1.5)
- Pytest configuration: Confirms LLM agent tests don't run by default (F1.6)
"""
