#!/usr/bin/env python3
"""Audit and optionally fix dead imports and duplicate logic after purge."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path


def _resolve_git_executable() -> str:
    git_in_path = shutil.which("git")
    if git_in_path:
        return git_in_path
    windows_candidate = Path(
        Path.home().parent / "AppData" / "Local" / "Programs" / "Git" / "cmd" / "git.exe"
    )
    if windows_candidate.exists():
        return str(windows_candidate)
    local_appdata = Path(__import__("os").environ.get("LOCALAPPDATA", ""))
    alt = local_appdata / "Programs" / "Git" / "cmd" / "git.exe"
    if alt.exists():
        return str(alt)
    raise FileNotFoundError("Unable to locate git executable")


REPO_ROOT = Path.cwd()
FIX_IMPORTS = "--fix-imports" in sys.argv

DELETED_IMPORT_PATHS = [
    "backend.src.agents.multi_agent.orchestrator",
    "backend.src.agents.multi_agent.guardrails",
    "backend.src.agents.multi_agent.protocol",
    "backend.src.agents.multi_agent.cli",
    "backend.src.agents.multi_agent.config_historical",
    "backend.src.zero_cost.dpd_calculator",
    "frontend.streamlit_app.fuzzy_table_mapping",
    "data.abaco",
]

IMPORT_REPLACEMENTS = {
    "backend.src.agents.multi_agent.orchestrator": "backend.python.multi_agent.orchestrator",
    "backend.src.agents.multi_agent.guardrails": "backend.python.multi_agent.guardrails",
    "backend.src.agents.multi_agent.protocol": "backend.python.multi_agent.protocol",
    "backend.src.agents.multi_agent.cli": "backend.python.multi_agent.cli",
    "backend.src.agents.multi_agent.config_historical": "backend.python.multi_agent.config_historical",
    "backend.src.zero_cost.dpd_calculator": "backend.python.kpis.dpd_calculator",
    "frontend.streamlit_app.fuzzy_table_mapping": "backend.src.zero_cost.fuzzy_matcher",
}

FRONTEND_SHADOW_PATTERNS = [
    re.compile(r"def\s+calculate_(?:dpd|par|npl|ltv|collection_rate|mora)", re.IGNORECASE),
    re.compile(r"def\s+compute_(?:risk|default|delinquency)", re.IGNORECASE),
    re.compile(r"\.fillna\(0\).*?(?:rate|ratio|score|risk)", re.IGNORECASE),
    re.compile(r"(?:dpd|days_past_due)\s*=\s*\(.*?date.*?-.*?date", re.IGNORECASE),
]

CANONICAL_KPI_FUNCTIONS = {
    "calculate_dpd": "backend/python/kpis/dpd_calculator.py",
    "calculate_par": "backend/python/kpis/ssot_asset_quality.py",
    "calculate_npl": "backend/python/kpis/ssot_asset_quality.py",
    "calculate_ltv_sintetico": "backend/python/kpis/ltv.py",
    "collection_rate": "backend/python/kpis/collection_rate.py",
    "calculate_xirr": "backend/src/zero_cost/xirr.py",
}


def get_all_python_files() -> list[Path]:
    return [
        file_path
        for file_path in REPO_ROOT.rglob("*.py")
        if ".git" not in str(file_path)
        and "__pycache__" not in str(file_path)
        and "scripts/hardening" not in str(file_path)
    ]


def find_function_definitions(files: list[Path], func_name: str) -> list[tuple[Path, int]]:
    results: list[tuple[Path, int]] = []
    pattern = re.compile(rf"^\s*def\s+{re.escape(func_name)}\s*\(", re.MULTILINE)
    for file_path in files:
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in pattern.finditer(source):
            line = source[: match.start()].count("\n") + 1
            results.append((file_path, line))
    return results


def find_dead_imports(files: list[Path]) -> list[dict[str, str | int]]:
    findings: list[dict[str, str | int]] = []
    for deleted_path in DELETED_IMPORT_PATHS:
        patterns = [
            re.compile(rf"from\s+{re.escape(deleted_path)}\s+import"),
            re.compile(rf"import\s+{re.escape(deleted_path)}"),
            re.compile(rf"from\s+{re.escape(deleted_path.replace('.', '/'))}\s+import"),
        ]
        for file_path in files:
            try:
                source = file_path.read_text(encoding="utf-8")
            except Exception:
                continue
            for pattern in patterns:
                for match in pattern.finditer(source):
                    line = source[: match.start()].count("\n") + 1
                    findings.append(
                        {
                            "file": str(file_path.relative_to(REPO_ROOT)),
                            "line": line,
                            "dead_import": deleted_path,
                            "replacement": IMPORT_REPLACEMENTS.get(deleted_path, "DELETE import"),
                            "match": match.group(0),
                        }
                    )
    return findings


def find_frontend_shadows(frontend_dir: Path) -> list[dict[str, str | int]]:
    findings: list[dict[str, str | int]] = []
    if not frontend_dir.exists():
        return findings
    for file_path in frontend_dir.rglob("*.py"):
        if "__pycache__" in str(file_path):
            continue
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception:
            continue
        for pattern in FRONTEND_SHADOW_PATTERNS:
            for match in pattern.finditer(source):
                line = source[: match.start()].count("\n") + 1
                findings.append(
                    {
                        "file": str(file_path.relative_to(REPO_ROOT)),
                        "line": line,
                        "pattern": pattern.pattern,
                        "match": match.group(0).strip(),
                    }
                )
    return findings


def fix_dead_imports(findings: list[dict[str, str | int]]) -> int:
    fixed = 0
    by_file: dict[str, list[dict[str, str | int]]] = {}
    for finding in findings:
        by_file.setdefault(str(finding["file"]), []).append(finding)

    for relative_path, items in by_file.items():
        file_path = REPO_ROOT / relative_path
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception:
            continue
        original = source
        for item in items:
            dead = str(item["dead_import"])
            replacement = str(item["replacement"])
            if replacement != "DELETE import":
                source = source.replace(dead, replacement)
            else:
                source = re.sub(rf"^.*(?:from|import)\s+{re.escape(dead)}.*\n?", "", source, flags=re.MULTILINE)
        if source != original:
            file_path.write_text(source, encoding="utf-8")
            fixed += 1
    return fixed


def write_report(total_issues: int, kpi_issues: list[dict[str, str]], dead_imports: list[dict[str, str | int]], shadows: list[dict[str, str | int]]) -> None:
    report_path = REPO_ROOT / "reports" / "DUPLICATION_REPORT.md"
    report_path.parent.mkdir(exist_ok=True, parents=True)
    with report_path.open("w", encoding="utf-8") as file_handle:
        file_handle.write("# Duplication Report\n\n")
        file_handle.write(f"Total issues: {total_issues}\n\n")
        if kpi_issues:
            file_handle.write("## KPI Function Duplicates\n\n")
            for issue in kpi_issues:
                file_handle.write(f"- `{issue['func']}` canonical: `{issue['canonical']}` duplicate: `{issue['duplicate']}`\n")
        if dead_imports:
            file_handle.write("\n## Dead Imports\n\n")
            for issue in dead_imports:
                file_handle.write(f"- `{issue['file']}:{issue['line']}` imports `{issue['dead_import']}` -> `{issue['replacement']}`\n")
        if shadows:
            file_handle.write("\n## Frontend Shadow Risk Engine\n\n")
            for issue in shadows:
                file_handle.write(f"- `{issue['file']}:{issue['line']}`: `{issue['match']}`\n")


def main() -> None:
    all_files = get_all_python_files()
    print("=" * 70)
    print(f"PHASE 3 - COLLAPSE DUPLICATION  {'[FIX IMPORTS]' if FIX_IMPORTS else '[AUDIT]'}")
    print(f"Scanning {len(all_files)} Python files")
    print("=" * 70)

    print("\n[1] KPI Function Duplication Scan")
    print("-" * 50)
    kpi_issues: list[dict[str, str]] = []
    for func_name, canonical_file in CANONICAL_KPI_FUNCTIONS.items():
        locations = find_function_definitions(all_files, func_name)
        canonical_path = (REPO_ROOT / canonical_file).resolve()
        non_canonical = [(file_path, line) for file_path, line in locations if file_path.resolve() != canonical_path]
        if not locations:
            print(f"  ! NOT FOUND: {func_name}() - canonical: {canonical_file}")
        elif non_canonical:
            print(f"  x DUPLICATE: {func_name}()")
            print(f"     Canonical: {canonical_file}")
            for duplicate_file, duplicate_line in non_canonical:
                relative = str(duplicate_file.relative_to(REPO_ROOT))
                print(f"     Duplicate: {relative}:{duplicate_line}")
                kpi_issues.append({"func": func_name, "canonical": canonical_file, "duplicate": f"{relative}:{duplicate_line}"})
        else:
            print(f"  ok {func_name}() - single implementation confirmed")

    print("\n[2] Dead Import Scan (deleted module references)")
    print("-" * 50)
    dead_imports = find_dead_imports(all_files)
    if dead_imports:
        for item in dead_imports:
            print(f"  x {item['file']}:{item['line']}")
            print(f"     Dead: {item['dead_import']}")
            print(f"     Fix:  {item['replacement']}")
    else:
        print("  ok No dead imports found")

    if FIX_IMPORTS and dead_imports:
        fixed = fix_dead_imports(dead_imports)
        print(f"\n  Auto-fixed imports in {fixed} files")

    print("\n[3] Frontend Shadow Risk Engine Scan")
    print("-" * 50)
    shadows = find_frontend_shadows(REPO_ROOT / "frontend")
    if shadows:
        for shadow in shadows:
            print(f"  x {shadow['file']}:{shadow['line']}")
            print(f"     Pattern: {shadow['match']}")
            print("     Fix: Remove local calculation; consume canonical API endpoint")
    else:
        print("  ok No shadow risk engine patterns in frontend")

    print("\n[4] Config Loader Duplication Scan")
    print("-" * 50)
    config_loaders = find_function_definitions(all_files, "load_config") + find_function_definitions(all_files, "get_config")
    locations = [f"{file_path.relative_to(REPO_ROOT)}:{line}" for file_path, line in config_loaders]
    if len(locations) > 1:
        print(f"  ! Config loader 'load_config/get_config' defined in {len(locations)} places:")
        for location in locations:
            print(f"     {location}")
        print("  Fix: Consolidate into backend/src/utils/config_loader.py")
    else:
        print(f"  ok load_config/get_config - {'single definition: ' + locations[0] if locations else 'not found'}")

    total_issues = len(kpi_issues) + len(dead_imports) + len(shadows)
    print("\n" + "=" * 70)
    print(f"DUPLICATION SUMMARY: {total_issues} issues found")
    print(f"  KPI duplicates:    {len(kpi_issues)}")
    print(f"  Dead imports:      {len(dead_imports)}")
    print(f"  Frontend shadows:  {len(shadows)}")
    print("=" * 70)

    write_report(total_issues, kpi_issues, dead_imports, shadows)
    print("\nReport: reports/DUPLICATION_REPORT.md")

    if total_issues > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()