#!/usr/bin/env python
"""
Zencoder Bootstrap Helper for abaco-loans-analytics

Purpose:
- Give code agents (Zencoder, CI helpers, etc.) a single Python entrypoint
  to verify the Abaco dual-engine KPI platform status.
- Wraps tools/check_kpi_sync.py and interprets its result into clear, actionable guidance.

Run from repo root:

  python tools/zencoder_bootstrap.py
  python tools/zencoder_bootstrap.py --print-json-only

"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Data models for typed access (mirrors tools/check_kpi_sync.py report)
# ---------------------------------------------------------------------------


@dataclass
class GitStatus:
    branch: Optional[str]
    commit: Optional[str]
    tags: List[str]
    dirty: bool


@dataclass
class FileCheck:
    path: str
    exists: bool
    mtime: Optional[str]


@dataclass
class JsonCheck:
    path: str
    exists: bool
    valid_json: bool
    has_extended_kpis: bool
    kpi_groups: List[str]
    mtime: Optional[str]


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
    git: GitStatus
    file_checks: List[FileCheck]
    json_check: JsonCheck
    regenerate_json: Optional[CommandResult]
    pytest_result: Optional[CommandResult]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_check_kpi_sync(repo_root: Path) -> Dict[str, Any]:
    """
    Call tools/check_kpi_sync.py --print-json and return parsed JSON.
    """
    script = repo_root / "tools" / "check_kpi_sync.py"
    if not script.is_file():
        raise FileNotFoundError(f"Missing tools/check_kpi_sync.py at {script}")

    # Use argument list, never shell=True, and do not interpolate untrusted input
    proc = subprocess.Popen(
        [sys.executable, str(script), "--print-json"],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
    )
    stdout, stderr = proc.communicate()
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError as e:
        if proc.returncode != 0:
            raise RuntimeError(
                f"check_kpi_sync failed with code {proc.returncode}:\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            )
        raise RuntimeError(
            f"Failed to parse JSON from check_kpi_sync: {e}\nRaw output:\n{stdout}"
        ) from e

    return report


def _pytest_was_skipped(result: Optional[CommandResult]) -> bool:
    """Return True when check_kpi_sync ran pytest but no tests were collected.

    In this repo, KPI parity tests are opt-in and may be entirely skipped,
    which pytest reports as return code 5.
    """

    if not result:
        return False
    if result.returncode != 5:
        return False
    text = (result.stdout or "") + "\n" + (result.stderr or "")
    return "skipped" in text.lower()


def _as_git_status(data: Dict[str, Any]) -> GitStatus:
    return GitStatus(
        branch=data.get("branch"),
        commit=data.get("commit"),
        tags=list(data.get("tags") or []),
        dirty=bool(data.get("dirty", False)),
    )


def _as_file_checks(data: List[Dict[str, Any]]) -> List[FileCheck]:
    return [
        FileCheck(
            path=item.get("path", ""),
            exists=bool(item.get("exists", False)),
            mtime=item.get("mtime"),
        )
        for item in data
    ]


def _as_json_check(data: Dict[str, Any]) -> JsonCheck:
    return JsonCheck(
        path=data.get("path", ""),
        exists=bool(data.get("exists", False)),
        valid_json=bool(data.get("valid_json", False)),
        has_extended_kpis=bool(data.get("has_extended_kpis", False)),
        kpi_groups=list(data.get("kpi_groups") or []),
        mtime=data.get("mtime"),
    )


def _as_command_result(data: Optional[Dict[str, Any]]) -> Optional[CommandResult]:
    if not data:
        return None
    return CommandResult(
        command=data.get("command", ""),
        success=bool(data.get("success", False)),
        returncode=int(data.get("returncode", 0)),
        stdout=data.get("stdout", ""),
        stderr=data.get("stderr", ""),
    )


def _as_report(raw: Dict[str, Any]) -> KpiSyncReport:
    return KpiSyncReport(
        repo_root=raw.get("repo_root", ""),
        git=_as_git_status(raw.get("git") or {}),
        file_checks=_as_file_checks(raw.get("file_checks") or []),
        json_check=_as_json_check(raw.get("json_check") or {}),
        regenerate_json=_as_command_result(raw.get("regenerate_json")),
        pytest_result=_as_command_result(raw.get("pytest_result")),
    )


def find_repo_root(start: Path) -> Path:
    """
    Walk up to find the repo root (directory with .git or README.md).
    """
    cur = start.resolve()
    for _ in range(10):
        if (cur / ".git").is_dir() or (cur / "README.md").is_file():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve()


# ---------------------------------------------------------------------------
# High-level guidance for Zencoder / agent
# ---------------------------------------------------------------------------


def print_high_level_summary(report: KpiSyncReport) -> None:
    print("=== ABACO KPI PLATFORM STATUS (Zencoder Bootstrap) ===")
    print(f"Repo root: {report.repo_root}")
    print(f"Git branch: {report.git.branch}")
    print(f"Git commit: {report.git.commit}")
    tags = ", ".join(report.git.tags) if report.git.tags else "-"
    print(f"Tags on HEAD: {tags}")
    print(f"Working tree dirty: {report.git.dirty}")

    print("\n[Core Files]")
    for fc in report.file_checks:
        status = "OK" if fc.exists else "MISSING"
        mtime = f" (mtime: {fc.mtime})" if fc.mtime else ""
        print(f"  - {fc.path}: {status}{mtime}")

    jc = report.json_check
    print("\n[Analytics JSON]")
    print(f"  - path: {jc.path}")
    print(f"  - exists: {jc.exists}")
    print(f"  - valid_json: {jc.valid_json}")
    print(f"  - has_extended_kpis: {jc.has_extended_kpis}")
    print(f"  - mtime: {jc.mtime}")
    if jc.kpi_groups:
        print(f"  - KPI groups: {', '.join(jc.kpi_groups)}")

    if report.regenerate_json:
        r = report.regenerate_json
        print("\n[Regeneration]")
        print(f"  - command: {r.command}")
        print(f"  - success: {r.success}")
        print(f"  - returncode: {r.returncode}")
        if r.stderr:
            print(f"  - stderr (truncated):\n{r.stderr[:500]}")

    if report.pytest_result:
        p = report.pytest_result
        print("\n[Parity Tests]")
        print(f"  - command: {p.command}")
        if _pytest_was_skipped(p):
            print("  - success: skipped (opt-in)")
        else:
            print(f"  - success: {p.success}")
        print(f"  - returncode: {p.returncode}")
        if p.stderr:
            print(f"  - stderr (truncated):\n{p.stderr[:500]}")

    print("\n[Agent Guidance]")
    if not all(fc.exists for fc in report.file_checks):
        print("  - One or more core files are missing. Focus first on creating/fixing those files.")
        print(
            "  - Priority files: docs/KPI_CATALOG.md, migration SQL, kpi_catalog_processor, parity tests, JSON export."
        )
    elif not report.json_check.valid_json or not report.json_check.has_extended_kpis:
        print(
            "  - JSON export is missing or malformed. Re-run run_complete_analytics.py and re-check."
        )
    elif report.pytest_result and _pytest_was_skipped(report.pytest_result):
        print("  - KPI parity tests are opt-in and were skipped.")
        print("  - To run them: set RUN_KPI_PARITY_TESTS=1 (and provide DATABASE_URL if needed).")
    elif report.pytest_result and not report.pytest_result.success:
        print(
            "  - KPI parity tests are failing. Investigate tests/test_kpi_parity.py and SQL views in analytics.*."
        )
    else:
        print("  - All KPI governance checks are passing.")
        print("  - Safe next steps for the agent:")
        print("      * Extend KPIs or views according to docs/KPI_CATALOG.md.")
        print("      * Modify dashboard pages to consume analytics.* views.")
        print("      * Implement new tests or ML features on top of the KPIs.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Zencoder helper for Abaco KPI dual-engine validation."
    )
    parser.add_argument(
        "--print-json-only",
        action="store_true",
        help="Only print raw JSON report from tools/check_kpi_sync.py.",
    )
    args = parser.parse_args(argv)

    repo_root = find_repo_root(Path.cwd())
    raw = run_check_kpi_sync(repo_root)
    report = _as_report(raw)

    if args.print_json_only:
        print(json.dumps(raw, indent=2))
    else:
        print_high_level_summary(report)

    # Exit code mirrors parity status if available
    if report.pytest_result and _pytest_was_skipped(report.pytest_result):
        return 0
    if report.pytest_result and not report.pytest_result.success:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
