#!/usr/bin/env python3
"""Audit surviving production files for silent failures and finance-safety issues."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path.cwd()
AUTO_FIX = "--fix" in sys.argv
FINANCIAL_PRECISION_MODULE = "backend/python/financial_precision.py"
XIRR_MODULE = "backend/src/zero_cost/xirr.py"

BARE_EXCEPT = re.compile(r"except\s*:\s*\n\s*pass", re.MULTILINE)
EXCEPT_PASS = re.compile(r"except\s+Exception\s*(?:as\s+\w+)?\s*:\s*\n\s*pass", re.MULTILINE)
EXCEPT_BROAD_RETURN_EMPTY = re.compile(
    r"except\s+Exception.*?:\s*\n(?:\s+.*\n)*?\s+return\s+(?:\{\}|\[\]|None|pd\.DataFrame\(\))",
    re.MULTILINE,
)
FLOAT_IN_FINANCE = re.compile(
    r"(?:float|np\.float|\.astype\(float\))\s*\(.*?(?:amount|capital|balance|interest|rate|payment|saldo|monto|tasa|mora)",
    re.IGNORECASE,
)
IMPUTATION = re.compile(
    r"(?:fillna|fill_value|impute|SimpleImputer|median\(\)|mean\(\)|mode\(\)).*?(?:dpd|par|npl|risk|mora|collection|ltv|capital|balance)",
    re.IGNORECASE,
)
CONFIG_SILENT = re.compile(
    r"(?:\bconfig\b|\bself\.config\b|\bcfg\b|\bsettings\b)"
    r"(?:\[[^\]]+\]|\.[A-Za-z_][A-Za-z0-9_]*)*"
    r"\.get\s*\(\s*['\"][^'\"]+['\"]\s*,\s*\{\}\s*\)"
)
YAML_UNSAFE = re.compile(r"yaml\.load\s*\(")

AUDIT_PATHS = [
    "backend/python/kpis/",
    "backend/python/apps/analytics/api/",
    "backend/python/models/",
    "backend/python/multi_agent/",
    "backend/src/pipeline/",
    "backend/src/zero_cost/",
    "backend/src/utils/",
    FINANCIAL_PRECISION_MODULE,
    "backend/python/validation.py",
    "backend/python/supabase_pool.py",
    "backend/src/infrastructure/",
]

FINANCIAL_FILES = [
    "backend/python/kpis/ltv.py",
    "backend/python/kpis/unit_economics.py",
    "backend/python/kpis/collection_rate.py",
    "backend/python/kpis/dpd_calculator.py",
    "backend/python/kpis/ssot_asset_quality.py",
    "backend/python/kpis/portfolio_analytics.py",
    "backend/python/kpis/lending_kpis.py",
    XIRR_MODULE,
]


def get_python_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for path_str in paths:
        full_path = REPO_ROOT / path_str
        if full_path.is_dir():
            files.extend(full_path.rglob("*.py"))
        elif full_path.is_file() and full_path.suffix == ".py":
            files.append(full_path)
    return [file_path for file_path in files if "__pycache__" not in str(file_path)]


Findings = list[dict[str, object]]


def scan_file(path: Path) -> Findings:
    findings: Findings = []
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return findings

    rel = str(path.relative_to(REPO_ROOT))

    for match in BARE_EXCEPT.finditer(source):
        line = source[: match.start()].count("\n") + 1
        findings.append({
            "file": rel,
            "line": line,
            "severity": "CRITICAL",
            "type": "BARE_EXCEPT_PASS",
            "detail": "Bare except: pass swallows all errors silently",
            "auto_fix": False,
            "fix": "Raise explicit exception or log and re-raise",
        })

    for match in EXCEPT_PASS.finditer(source):
        line = source[: match.start()].count("\n") + 1
        findings.append({
            "file": rel,
            "line": line,
            "severity": "CRITICAL",
            "type": "EXCEPT_EXCEPTION_PASS",
            "detail": "except Exception: pass swallows all errors",
            "auto_fix": False,
            "fix": "Re-raise or raise RuntimeError with context",
        })

    for match in EXCEPT_BROAD_RETURN_EMPTY.finditer(source):
        line = source[: match.start()].count("\n") + 1
        findings.append({
            "file": rel,
            "line": line,
            "severity": "HIGH",
            "type": "SILENT_EMPTY_FALLBACK",
            "detail": "Exception caught and returns empty fallback",
            "auto_fix": False,
            "fix": "Remove the silent fallback and raise with context",
        })

    for match in CONFIG_SILENT.finditer(source):
        line = source[: match.start()].count("\n") + 1
        findings.append({
            "file": rel,
            "line": line,
            "severity": "HIGH",
            "type": "CONFIG_SILENT_FALLBACK",
            "detail": "Config .get(key, {}) masks a missing required key",
            "auto_fix": False,
            "fix": "Use config[key] or raise a config error if missing",
        })

    for match in YAML_UNSAFE.finditer(source):
        line = source[: match.start()].count("\n") + 1
        findings.append({
            "file": rel,
            "line": line,
            "severity": "HIGH",
            "type": "YAML_UNSAFE_LOAD",
            "detail": "yaml.load() without safe loader",
            "auto_fix": True,
            "fix": "Replace yaml.load( with yaml.safe_load(",
        })

    financial_names = {Path(file_path).name for file_path in FINANCIAL_FILES}
    if path.name in financial_names:
        for match in FLOAT_IN_FINANCE.finditer(source):
            line = source[: match.start()].count("\n") + 1
            findings.append({
                "file": rel,
                "line": line,
                "severity": "HIGH",
                "type": "FLOAT_IN_FINANCIAL_CALC",
                "detail": "float() used in financial calculation context",
                "auto_fix": False,
                "fix": "Use Decimal or backend.python.financial_precision utilities",
            })

    for match in IMPUTATION.finditer(source):
        line = source[: match.start()].count("\n") + 1
        findings.append({
            "file": rel,
            "line": line,
            "severity": "CRITICAL",
            "type": "IMPUTATION_IN_RISK_PATH",
            "detail": "Imputation used in risk-critical path",
            "auto_fix": False,
            "fix": "Encode missingness explicitly; never impute risk-critical values",
        })

    return findings


def apply_auto_fixes(path: Path, findings: Findings) -> bool:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return False
    original = source
    for finding in findings:
        if finding.get("auto_fix") and finding["type"] == "YAML_UNSAFE_LOAD":
            source = source.replace("yaml.load(", "yaml.safe_load(")
    if source != original:
        path.write_text(source, encoding="utf-8")
        return True
    return False


def check_xirr_convergence(path: Path) -> Findings:
    findings: Findings = []
    if not path.exists():
        findings.append({
            "file": XIRR_MODULE,
            "line": 0,
            "severity": "CRITICAL",
            "type": "XIRR_FILE_MISSING",
            "detail": "xirr.py not found",
            "auto_fix": False,
            "fix": "Implement XIRR with explicit convergence failure handling",
        })
        return findings

    source = path.read_text(encoding="utf-8")
    if "ConvergenceError" not in source and "convergence" not in source.lower():
        findings.append({
            "file": XIRR_MODULE,
            "line": 0,
            "severity": "CRITICAL",
            "type": "XIRR_NO_CONVERGENCE_ERROR",
            "detail": "xirr.py does not raise or document convergence failure",
            "auto_fix": False,
            "fix": "Raise a specific convergence error instead of silent fallback",
        })
    if "return 0" in source or "return 0.0" in source:
        findings.append({
            "file": XIRR_MODULE,
            "line": 0,
            "severity": "CRITICAL",
            "type": "XIRR_SILENT_ZERO_RETURN",
            "detail": "xirr.py returns 0 / 0.0, likely hiding convergence failure",
            "auto_fix": False,
            "fix": "Remove silent zero fallback; raise convergence error instead",
        })
    return findings


def check_financial_precision(path: Path) -> Findings:
    findings: Findings = []
    if not path.exists():
        findings.append({
            "file": FINANCIAL_PRECISION_MODULE,
            "line": 0,
            "severity": "CRITICAL",
            "type": "FINANCIAL_PRECISION_MISSING",
            "detail": "financial_precision.py not found",
            "auto_fix": False,
            "fix": "Create module with Decimal rounding utilities",
        })
        return findings

    for file_path in FINANCIAL_FILES:
        full_path = REPO_ROOT / file_path
        if not full_path.exists():
            continue
        source = full_path.read_text(encoding="utf-8")
        if "financial_precision" not in source and "Decimal" not in source:
            findings.append({
                "file": file_path,
                "line": 1,
                "severity": "HIGH",
                "type": "MISSING_DECIMAL_PRECISION",
                "detail": "Financial module does not import Decimal or financial_precision",
                "auto_fix": False,
                "fix": "Add Decimal or financial_precision utilities explicitly",
            })
    return findings


def write_report(findings: Findings, auto_fixed: int) -> Path:
    reports_dir = REPO_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True, parents=True)
    report_path = reports_dir / "HARDENING_FINDINGS.md"
    critical = [finding for finding in findings if finding["severity"] == "CRITICAL"]
    high = [finding for finding in findings if finding["severity"] == "HIGH"]
    with report_path.open("w", encoding="utf-8") as file_handle:
        file_handle.write("# Hardening Findings Report\n\n")
        file_handle.write(f"Total findings: {len(findings)}\n")
        file_handle.write(f"- CRITICAL: {len(critical)}\n")
        file_handle.write(f"- HIGH: {len(high)}\n\n")
        if AUTO_FIX:
            file_handle.write(f"Auto-fixed: {auto_fixed} files\n\n")
        for item in findings:
            file_handle.write(f"### [{item['severity']}] {item['type']}\n")
            file_handle.write(f"- **File:** `{item['file']}:{item['line']}`\n")
            file_handle.write(f"- **Detail:** {item['detail']}\n")
            file_handle.write(f"- **Fix:** {item['fix']}\n\n")
    return report_path


def main() -> None:
    files = get_python_files(AUDIT_PATHS)
    all_findings: Findings = []
    auto_fixed = 0

    print("=" * 70)
    print(f"PHASE 2 - HARDEN SURVIVORS  {'[AUTO-FIX ENABLED]' if AUTO_FIX else '[AUDIT ONLY]'}")
    print(f"Auditing {len(files)} files")
    print("=" * 70)

    for file_path in files:
        findings = scan_file(file_path)
        if findings:
            all_findings.extend(findings)
            if AUTO_FIX and apply_auto_fixes(file_path, findings):
                auto_fixed += 1

    all_findings.extend(check_xirr_convergence(REPO_ROOT / XIRR_MODULE))
    all_findings.extend(check_financial_precision(REPO_ROOT / FINANCIAL_PRECISION_MODULE))

    critical = [finding for finding in all_findings if finding["severity"] == "CRITICAL"]
    high = [finding for finding in all_findings if finding["severity"] == "HIGH"]

    print(f"\nFindings: {len(critical)} CRITICAL, {len(high)} HIGH\n")
    for severity, items in (("CRITICAL", critical), ("HIGH", high)):
        if not items:
            continue
        print("-" * 60)
        print(f"{severity} ({len(items)})")
        print("-" * 60)
        for item in items:
            print(f"  [{item['file']}:{item['line']}]")
            print(f"    {item['type']}: {item['detail']}")
            print(f"    FIX: {item['fix']}\n")

    report_path = write_report(all_findings, auto_fixed)
    print(f"Report written to: {report_path}")
    if AUTO_FIX:
        print(f"Auto-fixed: {auto_fixed} files")
    if critical:
        print(f"\nWARNING: {len(critical)} CRITICAL issues require manual fix before production merge.")
        sys.exit(1)


if __name__ == "__main__":
    main()