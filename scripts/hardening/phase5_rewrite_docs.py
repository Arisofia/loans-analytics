#!/usr/bin/env python3
"""
phase5_rewrite_docs.py
Scans all .md files for:
  1. References to deleted files/modules
  2. References to non-existent architecture
  3. References to deleted commands/scripts

Produces STALE_DOCS_REPORT.md with exact file:line findings.
Does NOT auto-rewrite docs (narrative content requires human judgment).

Run from repo root:
    python scripts/hardening/phase5_rewrite_docs.py
"""
import subprocess
from pathlib import Path

# Windows-safe: avoid git rev-parse which garbles paths with non-ASCII chars
REPO_ROOT = Path.cwd()

# ─────────────────────────────────────────────────────────────────────────────
# PATHS THAT NO LONGER EXIST (deleted in phases 1-4)
# Docs referencing these must be updated.
# ─────────────────────────────────────────────────────────────────────────────
DELETED_PATHS = [
    "backend/src/agents/multi_agent/orchestrator",
    "backend/src/agents/multi_agent/guardrails",
    "backend/src/agents/multi_agent/protocol",
    "backend/src/zero_cost/dpd_calculator",
    "frontend/streamlit_app/fuzzy_table_mapping",
    "data/abaco/",
    "data/abaco",
    "backend/python/ingest/",
    "backend/python/testing/",
    "pytest.ini",
    "htmlcov/",
    "READY_TO_DEPLOY.md",
    "MERGE_CONFLICT_RESOLUTION.md",
    "SETUP_STATUS.md",
    "GRAFANA_DATA_SETUP.md",
    "GRAFANA_LIVE.md",
    "backend/python/OPERATIONS.md",
    "backend/python/MIGRATION.md",
]

# ─────────────────────────────────────────────────────────────────────────────
# DOCS TO ALWAYS DELETE (not just update)
# ─────────────────────────────────────────────────────────────────────────────
DELETE_THESE_DOCS = [
    "docs/process-output-2026-02-26.md",
    "GRAFANA_DATA_SETUP.md",
    "GRAFANA_LIVE.md",
    "backend/python/OPERATIONS.md",
    "backend/python/MIGRATION.md",
    "backend/python/multi_agent/DATABASE_DESIGNER_USAGE.md",
    "backend/python/multi_agent/README.md",  # superseded by docs/
    "docs/runbook.md",  # singular, superseded by docs/runbooks/
    ".github/workflows/.workflow-management.md",
    ".github/agents/MICROSERVICE_DESIGNER_USAGE.md",
    ".github/agents/TESTCRAFTPRO_QUICKSTART.md",
    ".github/agents/TESTCRAFTPRO_USAGE.md",
    ".github/agents/USAGE_EXAMPLES.md",
    "reports/INSTITUTIONAL_AUDIT_ATTESTATION_2026-03-19.md",
    "READY_TO_DEPLOY.md",
    "MERGE_CONFLICT_RESOLUTION.md",
    "SETUP_STATUS.md",
]

# ─────────────────────────────────────────────────────────────────────────────
# DOCS THAT ARE CANONICAL — update references but do NOT delete
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL_DOCS = [
    "README.md",
    "docs/OPERATIONS.md",
    "docs/migration.md",
    "docs/SECURITY.md",
    "docs/DATA_GOVERNANCE.md",
    "docs/DATA_DICTIONARY.md",
    "docs/GOVERNANCE.md",
    "docs/KPI_CATALOG.md",
    "docs/PRODUCTION_DEPLOYMENT_GUIDE.md",
    "docs/GRAFANA_SETUP_GUIDE.md",
    "docs/SUPABASE_SETUP_GUIDE.md",
    "docs/OBSERVABILITY.md",
]


def get_all_md_files() -> list:
    return [
        f for f in REPO_ROOT.rglob("*.md")
        if ".git" not in str(f)
        and "__pycache__" not in str(f)
        and "/reports/" not in str(f).replace("\\", "/")
        and str(f).replace("\\", "/").split("/")[-2] != "reports"
    ]


def scan_doc(path: Path) -> list:
    findings = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return findings

    try:
        rel = str(path.relative_to(REPO_ROOT))
    except ValueError:
        rel = str(path)

    for ln, line in enumerate(lines, 1):
        for dead_path in DELETED_PATHS:
            if dead_path in line:
                findings.append({
                    "file": rel,
                    "line": ln,
                    "dead_reference": dead_path,
                    "context": line.strip()[:120],
                })
    return findings


def delete_stale_docs(dry_run: bool = True) -> int:
    import os
    import shutil
    GIT = shutil.which("git") or os.path.join(
        os.environ.get("LOCALAPPDATA", ""), "Programs", "Git", "cmd", "git.exe"
    )
    deleted = 0
    for rel_path in DELETE_THESE_DOCS:
        fpath = REPO_ROOT / rel_path
        if fpath.exists():
            if dry_run:
                print(f"  [DRY RUN] Would delete: {rel_path}")
            else:
                try:
                    subprocess.run(
                        [GIT, "rm", "-f", rel_path],
                        check=True, capture_output=True, cwd=REPO_ROOT
                    )
                    print(f"  x Deleted: {rel_path}")
                    deleted += 1
                except subprocess.CalledProcessError:
                    fpath.unlink()
                    print(f"  x Deleted (untracked): {rel_path}")
                    deleted += 1
        else:
            print(f"  + Already absent: {rel_path}")
    return deleted


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true",
                        help="Actually delete stale docs (default: dry run)")
    args = parser.parse_args()

    print("=" * 70)
    print(f"PHASE 5 — DOCUMENTATION AUDIT {'[DELETING]' if args.delete else '[DRY RUN]'}")
    print("=" * 70)
    print(f"  Repo: {REPO_ROOT}")

    # ── Step 1: Delete explicitly stale docs ─────────────────────────────
    print("\n[1] Deleting explicitly stale documentation...")
    deleted = delete_stale_docs(dry_run=not args.delete)
    print(f"    {'Deleted' if args.delete else 'Would delete'}: {deleted} docs")

    # ── Step 2: Scan surviving docs for dead references ───────────────────
    print("\n[2] Scanning surviving docs for dead references...")
    md_files = get_all_md_files()
    all_findings: list = []

    # Normalize the delete list to use the same path separators as rglob output
    delete_set = set(
        str(Path(p)).replace("\\", "/") for p in DELETE_THESE_DOCS
    )

    for f in md_files:
        try:
            rel = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
        except ValueError:
            rel = str(f).replace("\\", "/")
        # Skip docs that were/will be deleted
        if rel in delete_set:
            continue
        findings = scan_doc(f)
        all_findings.extend(findings)

    # ── Step 3: Report ────────────────────────────────────────────────────
    if all_findings:
        print(f"\n  Found {len(all_findings)} dead references in surviving docs:\n")
        by_file: dict = {}
        for item in all_findings:
            by_file.setdefault(item["file"], []).append(item)

        for fpath, items in by_file.items():
            print(f"  {fpath}")
            for i in items:
                print(f"    line {i['line']:4d}: [{i['dead_reference']}]")
                print(f"           {i['context']}")
    else:
        print("\n  + No dead references in surviving docs")

    # ── Step 4: Check canonical documentation state ───────────────────────
    print("\n[3] Checking canonical documentation state...")
    for doc in CANONICAL_DOCS:
        fpath = REPO_ROOT / doc
        if fpath.exists():
            print(f"  + {doc}")
        else:
            print(f"  ! MISSING canonical doc: {doc}")

    # ── Step 5: Write report ──────────────────────────────────────────────
    (REPO_ROOT / "reports").mkdir(exist_ok=True)
    report_path = REPO_ROOT / "reports" / "STALE_DOCS_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("# Stale Documentation Report\n\n")
        fh.write(f"Dead references found: {len(all_findings)}\n\n")
        if all_findings:
            fh.write("## Files With Dead References\n\n")
            by_file = {}
            for item in all_findings:
                by_file.setdefault(item["file"], []).append(item)
            for fpath, items in by_file.items():
                fh.write(f"### `{fpath}`\n\n")
                for i in items:
                    fh.write(
                        f"- Line {i['line']}: `{i['dead_reference']}` "
                        f"— `{i['context']}`\n"
                    )
                fh.write("\n")

    print(f"\n  Report: {report_path}")

    if not args.delete and deleted > 0:
        print(f"\n  Run with --delete to actually remove {deleted} stale docs:")
        print("  python scripts/hardening/phase5_rewrite_docs.py --delete")


if __name__ == "__main__":
    main()
