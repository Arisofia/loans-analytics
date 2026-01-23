#!/usr/bin/env python
"""
Helper script for Zencoder / code agents to validate the Abaco dual-engine (Python + SQL) KPI setup.

Features:
- Detect repository root.
- Check presence of core files (KPI catalog, SQL migration, Python processor, parity tests).
- Optionally regenerate exports/complete_kpi_dashboard.json via run_complete_analytics.py.
- Validate JSON structure (extended_kpis.* keys).
- Optionally run pytest parity tests.

Usage examples:

  python tools/check_kpi_sync.py
  python tools/check_kpi_sync.py --no-regenerate --no-tests
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class FileCheckResult:
    path: str
    exists: bool


@dataclass
class JsonCheckResult:
    path: str
    exists: bool
    valid_json: bool
    has_extended_kpis: bool
    kpi_groups: List[str]


@dataclass
class CommandResult:
    command: str
    success: bool
    returncode: int
    stdout: str
    stderr: str


@dataclass
class KpiSyncReport:
    repo_root: str
    file_checks: List[FileCheckResult]
    json_check: Optional[JsonCheckResult]
    regenerate_json: Optional[CommandResult]
    pytest_result: Optional[CommandResult]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def find_repo_root(start: Path) -> Path:
    """
    Walk up from `start` until we find a directory that looks like the repo root
    (contains .git or README.md). Fallback: `start`.
    """
    current = start.resolve()
    for _ in range(10):
        if (current / ".git").is_dir() or (current / "README.md").is_file():
            return current
        if current.parent == current:
            break
        current = current.parent
    return start.resolve()


def run_command(cmd: List[str], cwd: Path) -> CommandResult:
    # Use argument list, never shell=True, and do not interpolate untrusted input
    proc = subprocess.Popen(
        cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False
    )
    stdout, stderr = proc.communicate()
    return CommandResult(
        command=" ".join(cmd),
        success=(proc.returncode == 0),
        returncode=proc.returncode,
        stdout=stdout.strip(),
        stderr=stderr.strip(),
    )


def check_files(repo_root: Path) -> List[FileCheckResult]:
    """
    Check presence of the core files required for the dual-engine analytics setup.
    """
    paths = [
        "docs/KPI_CATALOG.md",
        "docs/DATA_DICTIONARY.md",
        "supabase/migrations/20260101_analytics_kpi_views.sql",
        "src/analytics/kpi_catalog_processor.py",
        "run_complete_analytics.py",
        "tests/test_kpi_parity.py",
        "exports/complete_kpi_dashboard.json",
    ]
    results: List[FileCheckResult] = []
    for rel in paths:
        p = repo_root / rel
        results.append(FileCheckResult(path=str(p.relative_to(repo_root)), exists=p.is_file()))
    return results


def check_json_structure(repo_root: Path) -> JsonCheckResult:
    json_path = repo_root / "exports" / "complete_kpi_dashboard.json"
    if not json_path.is_file():
        return JsonCheckResult(
            path=str(json_path.relative_to(repo_root)),
            exists=False,
            valid_json=False,
            has_extended_kpis=False,
            kpi_groups=[],
        )

    try:
        with json_path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        valid = True
    except Exception:
        return JsonCheckResult(
            path=str(json_path.relative_to(repo_root)),
            exists=True,
            valid_json=False,
            has_extended_kpis=False,
            kpi_groups=[],
        )

    extended = obj.get("extended_kpis") or {}
    has_extended = isinstance(extended, dict)
    groups = sorted(extended.keys()) if has_extended else []

    return JsonCheckResult(
        path=str(json_path.relative_to(repo_root)),
        exists=True,
        valid_json=valid,
        has_extended_kpis=has_extended,
        kpi_groups=groups,
    )


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate KPI dual-engine setup for Zencoder/code agents."
    )
    parser.add_argument(
        "--no-regenerate",
        action="store_true",
        help="Do not run run_complete_analytics.py even if JSON is missing.",
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Do not run pytest parity tests.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print the report as JSON for consumption by other agents.",
    )

    args = parser.parse_args(argv)

    cwd = Path.cwd()
    repo_root = find_repo_root(cwd)

    file_checks = check_files(repo_root)
    json_check = check_json_structure(repo_root)

    regenerate_result: Optional[CommandResult] = None
    pytest_result: Optional[CommandResult] = None

    # Decide whether to regenerate JSON
    if not args.no_regenerate:
        if not json_check.exists or not json_check.valid_json:
            run_script = repo_root / "run_complete_analytics.py"
            if run_script.is_file():
                regenerate_result = run_command(
                    [sys.executable, "run_complete_analytics.py"],
                    cwd=repo_root,
                )
                # re-check JSON after regeneration
                json_check = check_json_structure(repo_root)
            else:
                regenerate_result = CommandResult(
                    command=f"{sys.executable} run_complete_analytics.py",
                    success=False,
                    returncode=1,
                    stdout="",
                    stderr="run_complete_analytics.py not found",
                )

    # Optionally run pytest parity tests
    if not args.no_tests:
        test_file = repo_root / "tests" / "test_kpi_parity.py"
        if test_file.is_file():
            pytest_result = run_command(
                [sys.executable, "-m", "pytest", "-q", "tests/test_kpi_parity.py"],
                cwd=repo_root,
            )
        else:
            pytest_result = CommandResult(
                command=f"{sys.executable} -m pytest -q tests/test_kpi_parity.py",
                success=False,
                returncode=1,
                stdout="",
                stderr="tests/test_kpi_parity.py not found",
            )

    report = KpiSyncReport(
        repo_root=str(repo_root),
        file_checks=file_checks,
        json_check=json_check,
        regenerate_json=regenerate_result,
        pytest_result=pytest_result,
    )

    if args.print_json:
        print(json.dumps(asdict(report), indent=2, default=str))
    else:
        # Human-readable summary for Zencoder logs
        print(f"[INFO] Repo root: {report.repo_root}")
        print("\n[INFO] File checks:")
        for fc in report.file_checks:
            status = "OK" if fc.exists else "MISSING"
            print(f"  - {fc.path}: {status}")

        if report.json_check:
            jc = report.json_check
            print(f"\n[INFO] JSON export: {jc.path}")
            print(f"  - exists: {jc.exists}")
            print(f"  - valid_json: {jc.valid_json}")
            print(f"  - has_extended_kpis: {jc.has_extended_kpis}")
            if jc.kpi_groups:
                print(f"  - kpi_groups: {', '.join(jc.kpi_groups)}")

        if report.regenerate_json:
            r = report.regenerate_json
            print("\n[INFO] Regenerate JSON command:")
            print(f"  - cmd: {r.command}")
            print(f"  - success: {r.success}")
            print(f"  - returncode: {r.returncode}")
            if r.stdout:
                print(f"  - stdout:\n{r.stdout}")
            if r.stderr:
                print(f"  - stderr:\n{r.stderr}")

        if report.pytest_result:
            p = report.pytest_result
            print("\n[INFO] Pytest parity result:")
            print(f"  - cmd: {p.command}")
            print(f"  - success: {p.success}")
            print(f"  - returncode: {p.returncode}")
            if p.stdout:
                print(f"  - stdout:\n{p.stdout}")
            if p.stderr:
                print(f"  - stderr:\n{p.stderr}")

    # Exit code: fail if pytest failed or regenerate failed
    if report.pytest_result and not report.pytest_result.success:
        return 1
    if report.regenerate_json and not report.regenerate_json.success:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
