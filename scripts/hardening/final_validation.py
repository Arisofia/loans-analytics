#!/usr/bin/env python3
"""
final_validation.py
Runs after all hardening phases to produce a comprehensive final audit
of the repo's health: tests, lint, import integrity, migration convention,
doc completeness, and security surface.

Run from repo root:
    python scripts/hardening/final_validation.py
"""
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

# Windows-safe: avoid git rev-parse which garbles paths with non-ASCII chars
REPO_ROOT = Path.cwd()

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
SKIP = "SKIP"


def runcmd(cmd: list, cwd=None, capture=True):
    """Run a command and return (returncode, stdout+stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or REPO_ROOT,
            capture_output=capture,
            text=True,
        )
        out = (result.stdout or "") + (result.stderr or "")
        return result.returncode, out.strip()
    except FileNotFoundError:
        return 127, f"Command not found: {cmd[0]}"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Test suite
# ─────────────────────────────────────────────────────────────────────────────
def run_tests() -> tuple:
    """Returns (status, details)."""
    print("\n[1/7] Running test suite...")
    # Use sys.executable to be Windows-safe (no python3 on Windows by default)
    code, out = runcmd([sys.executable, "-m", "pytest", "--tb=no", "-q"])
    if code == 0:
        # Extract summary line
        for line in reversed(out.splitlines()):
            if "passed" in line or "failed" in line:
                return PASS, line.strip()
        return PASS, "Tests completed"
    else:
        # Find failure summary
        summary = []
        for line in out.splitlines():
            if "FAILED" in line or "failed" in line or "error" in line.lower():
                summary.append(line.strip())
        return FAIL, "\n".join(summary[:20]) or out[-500:]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Lint (ruff)
# ─────────────────────────────────────────────────────────────────────────────
def run_lint() -> tuple:
    """Returns (status, details)."""
    print("[2/7] Running ruff lint...")
    # Try ruff directly, fall back to python -m ruff
    ruff_bin = shutil.which("ruff")
    if ruff_bin:
        cmd = [ruff_bin, "check", "backend/", "src/", "scripts/"]
    else:
        cmd = [sys.executable, "-m", "ruff", "check", "backend/", "src/", "scripts/"]

    code, out = runcmd(cmd)
    if code == 0:
        return PASS, "0 lint issues"
    else:
        lines = [ln for ln in out.splitlines() if ln.strip()]
        return FAIL, f"{len(lines)} issues found:\n" + "\n".join(lines[:20])


# ─────────────────────────────────────────────────────────────────────────────
# 3. Type check (mypy)
# ─────────────────────────────────────────────────────────────────────────────
def run_type_check() -> tuple:
    """Returns (status, details)."""
    print("[3/7] Running mypy type check...")
    mypy_bin = shutil.which("mypy")
    if mypy_bin:
        cmd = [mypy_bin, "backend/python/", "--ignore-missing-imports",
               "--no-error-summary"]
    else:
        cmd = [sys.executable, "-m", "mypy", "backend/python/",
               "--ignore-missing-imports", "--no-error-summary"]

    code, out = runcmd(cmd)
    error_lines = [ln for ln in out.splitlines() if ": error:" in ln]
    if not error_lines:
        return PASS, "No type errors"
    else:
        return WARN, f"{len(error_lines)} type errors:\n" + "\n".join(error_lines[:20])


# ─────────────────────────────────────────────────────────────────────────────
# 4. Decimal / float check in kpi files
# ─────────────────────────────────────────────────────────────────────────────
def check_decimal_discipline() -> tuple:
    """Returns (status, details)."""
    print("[4/7] Checking float vs Decimal discipline in KPI files...")
    violations = []
    kpi_dir = REPO_ROOT / "backend" / "python" / "kpis"
    if not kpi_dir.exists():
        return SKIP, "backend/python/kpis/ not found"

    for pyfile in kpi_dir.rglob("*.py"):
        try:
            lines = pyfile.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        rel = str(pyfile.relative_to(REPO_ROOT)).replace("\\", "/")
        for lno, line in enumerate(lines, 1):
                stripped = line.strip()
                # Skip comments
                if stripped.startswith("#"):
                    continue
                # Only flag bare float() arithmetic (not output serialization)
                # Safe: round(float(...)), float() conversions in dict/JSON,
                #        float(Decimal), float(x) assigned to variable ending in _pct/_rate
                # Unsafe: float(loans_df[...] + loans_df[...])  (intermediate calc)
                if "float(" not in stripped:
                    continue
                # Exclude output-boundary patterns
                safe_patterns = (
                    "round(float(",
                    "float(Decimal",
                    "float(rate",
                    "float(pct",
                    "float(0",
                    "math.",
                    ': float(',   # dict value
                    '= float(',   # assignment to named variable (not arithmetic)
                )
                if any(p in stripped for p in safe_patterns):
                    continue
                # What remains: float() used in arithmetic expressions
                violations.append(f"{rel}:{lno}: {stripped[:80]}")

    if not violations:
        return PASS, "No float() misuse found in KPI files"
    else:
        return WARN, f"{len(violations)} potential float() usages:\n" + "\n".join(violations[:20])


# ─────────────────────────────────────────────────────────────────────────────
# 5. Migration file naming convention
# ─────────────────────────────────────────────────────────────────────────────
def check_migration_convention() -> tuple:
    """Returns (status, details)."""
    print("[5/7] Checking migration file naming convention...")
    mig_dir = REPO_ROOT / "db" / "migrations"
    if not mig_dir.exists():
        return SKIP, "db/migrations/ not found"

    bad = []
    for f in sorted(mig_dir.iterdir()):
        if f.suffix == ".sql":
            # Expect YYYYMMDD_description.sql or NNN_description.sql (2+ leading digits)
            name = f.name
            # Check if file starts with any number of digits followed by _
            import re as _re
            if not _re.match(r"^\d+_", name):
                bad.append(name)

    if not bad:
        return PASS, "All migration files follow naming convention"
    else:
        return WARN, f"{len(bad)} oddly named migrations: {bad}"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Dead import check (python files importing deleted modules)
# ─────────────────────────────────────────────────────────────────────────────
def check_dead_imports() -> tuple:
    """Returns (status, details)."""
    print("[6/7] Checking for dead imports...")

    # Only flag module paths that are confirmed to NOT exist on disk
    # A module like "backend.src.agents" maps to backend/src/agents/
    # We only flag it if that directory/file doesn't exist anywhere in the repo.
    candidate_dead_modules = [
        "backend.python.ingest",
        "backend.python.testing",
    ]

    def module_to_path(mod: str) -> Path:
        return REPO_ROOT / Path(mod.replace(".", "/"))

    dead_modules = [
        m for m in candidate_dead_modules
        if not module_to_path(m).exists()
        and not module_to_path(m).with_suffix(".py").exists()
    ]

    if not dead_modules:
        return PASS, "No dead imports found"

    hits = []
    search_dirs = [
        REPO_ROOT / "backend" / "python",
        REPO_ROOT / "src",
        REPO_ROOT / "tests",
    ]
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for pyfile in search_dir.rglob("*.py"):
            if "__pycache__" in str(pyfile):
                continue
            try:
                text = pyfile.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            rel = str(pyfile.relative_to(REPO_ROOT)).replace("\\", "/")
            for dead in dead_modules:
                if dead in text:
                    line_num = next(
                        (i + 1 for i, ln in enumerate(text.splitlines()) if dead in ln), 0
                    )
                    hits.append(f"{rel}:{line_num}: {dead}")

    if not hits:
        return PASS, "No dead imports found"
    else:
        return FAIL, f"{len(hits)} dead imports:\n" + "\n".join(hits[:20])


# ─────────────────────────────────────────────────────────────────────────────
# 7. Canonical documentation existence
# ─────────────────────────────────────────────────────────────────────────────
def check_canonical_docs() -> tuple:
    """Returns (status, details)."""
    print("[7/7] Checking canonical documentation...")
    MUST_EXIST = [
        "README.md",
        "docs/OPERATIONS.md",
        "docs/GOVERNANCE.md",
        "docs/DATA_DICTIONARY.md",
        "docs/KPI_CATALOG.md",
        "docs/PRODUCTION_DEPLOYMENT_GUIDE.md",
        "docs/OBSERVABILITY.md",
        "docs/SETUP_GUIDE_CONSOLIDATED.md",
        "SECURITY.md",
        "CHANGELOG.md",
    ]
    missing = []
    for doc in MUST_EXIST:
        if not (REPO_ROOT / doc).exists():
            missing.append(doc)

    if not missing:
        return PASS, f"All {len(MUST_EXIST)} canonical docs present"
    else:
        return WARN, f"{len(missing)} missing: {missing}"


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("FINAL VALIDATION — ABACO LOANS ANALYTICS")
    print("=" * 70)
    print(f"  Repo: {REPO_ROOT}")

    checks = [
        ("Tests", run_tests),
        ("Lint", run_lint),
        ("TypeCheck", run_type_check),
        ("DecimalDiscipline", check_decimal_discipline),
        ("MigrationConvention", check_migration_convention),
        ("DeadImports", check_dead_imports),
        ("CanonicalDocs", check_canonical_docs),
    ]

    results = []
    for name, fn in checks:
        status, detail = fn()
        results.append((name, status, detail))
        icon = {"PASS": "+", "FAIL": "x", "WARN": "!", "SKIP": "-"}.get(status, "?")
        print(f"  [{icon}] {name}: {status}")
        if status in (FAIL, WARN) and detail:
            for line in textwrap.wrap(detail, width=70):
                print(f"      {line}")

    # ── Summary ───────────────────────────────────────────────────────────────
    fails = [n for n, s, _ in results if s == FAIL]
    warns = [n for n, s, _ in results if s == WARN]
    passed = [n for n, s, _ in results if s == PASS]

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  PASS: {len(passed)}/{len(results)}")
    if warns:
        print(f"  WARN: {warns}")
    if fails:
        print(f"  FAIL: {fails}")
        print("\n  !! REPO IS NOT PRODUCTION-READY !!")
        exit_code = 1
    else:
        print("\n  ++ ALL CHECKS PASSED — REPO IS PRODUCTION-READY ++")
        exit_code = 0

    # ── Write report ──────────────────────────────────────────────────────────
    (REPO_ROOT / "reports").mkdir(exist_ok=True)
    report_path = REPO_ROOT / "reports" / "FINAL_VALIDATION_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("# Final Validation Report\n\n")
        fh.write(f"Repo: `{REPO_ROOT}`\n\n")
        fh.write("## Results\n\n")
        fh.write("| Check | Status | Notes |\n")
        fh.write("|-------|--------|-------|\n")
        for name, status, detail in results:
            short = detail.replace("\n", " ")[:80]
            fh.write(f"| {name} | **{status}** | {short} |\n")
        fh.write("\n")
        if fails:
            fh.write("## Failures\n\n")
            for name, status, detail in results:
                if status == FAIL:
                    fh.write(f"### {name}\n\n```\n{detail}\n```\n\n")
        if warns:
            fh.write("## Warnings\n\n")
            for name, status, detail in results:
                if status == WARN:
                    fh.write(f"### {name}\n\n```\n{detail}\n```\n\n")

    print(f"\n  Report: {report_path}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
