#!/usr/bin/env python3
"""ABACO infrastructure validator and canonicalization utility.

Task flow implemented by this script:
1. Identify legacy scripts duplicated outside canonical locations.
2. Apply structural alignment by syncing ``.repo-structure.json`` with current paths.
3. Remove duplicate scripts and keep one canonical path per task.
4. Run a validation checklist and emit a machine-readable report.
5. Optionally perform branching operations (stage + commit).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from importlib import metadata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / ".repo-structure.json"
SCRIPTS_DIR = REPO_ROOT / "scripts"
REPORT_PATH = REPO_ROOT / "reports" / "abaco_infra_validator_report.json"

TASK_LABELS = {
    "task_1": "Identify legacy scripts",
    "task_2": "Structural alignment (.repo-structure.json)",
    "task_3": "Script consolidation",
    "task_4": "Validation checklist",
    "task_5": "Branching operations (git commit)",
}

CANONICAL_SCRIPT_TARGETS = {
    SCRIPTS_DIR / "data" / "run_data_pipeline.py": "Pipeline entrypoint",
    SCRIPTS_DIR / "data" / "analyze_real_data.py": "Real data analyzer",
    SCRIPTS_DIR / "data" / "generate_sample_data.py": "Synthetic data generator",
    SCRIPTS_DIR / "data" / "load_sample_kpis_supabase.py": "Synthetic KPI loader",
    SCRIPTS_DIR / "data" / "seed_spanish_loans.py": "Spanish ID seeding",
    SCRIPTS_DIR / "maintenance" / "validate_structure.py": "Structure validator",
    SCRIPTS_DIR
    / "maintenance"
    / "generate_service_status_report.py": "Service status report generator",
    SCRIPTS_DIR / "path_utils.py": "Path security utilities",
    SCRIPTS_DIR / "maintenance" / "repo_maintenance.sh": "Maintenance orchestration",
    SCRIPTS_DIR / "maintenance" / "repo-doctor.sh": "Repo doctor",
}

LEGACY_DUPLICATE_SEARCH_DIRS = (REPO_ROOT, SCRIPTS_DIR)
SCRIPT_EXTENSIONS = {".py", ".sh"}


@dataclass
class LegacyCandidate:
    """Represents one duplicate script that should be removed."""

    path: Path
    canonical_target: Path
    reason: str


@dataclass
class ChecklistItem:
    """One validation checklist row."""

    label: str
    passed: bool
    detail: str


class AbacoInfraValidator:
    """Implements Task 1-5 in one command-line workflow."""

    def __init__(self, *, apply: bool, commit: bool, commit_message: str, verbose: bool) -> None:
        self.apply = apply
        self.commit = commit
        self.commit_message = commit_message
        self.verbose = verbose

        self.legacy_candidates: list[LegacyCandidate] = []
        self.manifest_changes: list[str] = []
        self.consolidation_changes: list[str] = []
        self.changed_paths: set[Path] = set()
        self.commit_hash: str | None = None

    def run(self) -> int:
        """Run Task 1-5 and return process exit code."""
        self.legacy_candidates = self.identify_legacy_scripts()
        self.sync_repo_structure()
        self.apply_script_consolidation()

        checklist = self.build_validation_checklist()
        checklist.append(self.handle_branching_operations())

        self.print_summary(checklist)
        self.write_report(checklist)

        return 0 if all(item.passed for item in checklist) else 1

    def identify_legacy_scripts(self) -> list[LegacyCandidate]:
        """Task 1: Identify duplicated script paths to remove."""
        candidates = self._discover_duplicate_script_paths()

        if self.verbose:
            for candidate in candidates:
                rel = candidate.path.relative_to(REPO_ROOT)
                canonical = candidate.canonical_target.relative_to(REPO_ROOT)
                print(f"[legacy] {rel} -> {canonical} ({candidate.reason})")

        return candidates

    def sync_repo_structure(self) -> None:
        """Task 2: Align ``.repo-structure.json`` with current repository layout."""
        manifest = self._load_manifest()
        updated_manifest = deepcopy(manifest)

        def set_if_changed(container: dict[str, Any], key: str, value: Any, detail: str) -> None:
            if container.get(key) != value:
                container[key] = value
                self.manifest_changes.append(detail)

        set_if_changed(
            updated_manifest,
            "last_updated",
            date.today().isoformat(),
            "Updated last_updated to current date",
        )

        legacy = updated_manifest.setdefault("LEGACY_ARCHIVED_CONTENT", {})
        set_if_changed(
            legacy,
            "location",
            "none",
            "Aligned legacy location to none",
        )
        set_if_changed(
            legacy,
            "note",
            "Legacy maintenance artifacts were removed from the repository",
            "Normalized legacy note to current cleanup policy",
        )

        desired_legacy_folders: list[dict[str, Any]] = []
        set_if_changed(
            legacy,
            "folders",
            desired_legacy_folders,
            "Aligned LEGACY_ARCHIVED_CONTENT folders to empty legacy layout",
        )

        phases = updated_manifest.setdefault("PROCESS_PHASES", {})
        orchestration = phases.setdefault("ORCHESTRATION", {})
        set_if_changed(
            orchestration,
            "trigger",
            "scripts/data/run_data_pipeline.py (entry point)",
            "Aligned ORCHESTRATION trigger path",
        )

        workflow = updated_manifest.setdefault("ACTIVE_PRODUCTION_WORKFLOW", {})
        folders = workflow.get("folders", [])
        for folder in folders:
            if folder.get("path") != "docs/":
                continue
            active_docs = [
                "README.md - Documentation index",
                "OPERATIONS.md - Deployment and runbooks",
                "OBSERVABILITY.md - Monitoring setup",
                "REPOSITORY_MAINTENANCE.md - Repo hygiene and consolidation",
                "operations/SCRIPT_CANONICAL_MAP.md - Canonical script command map",
            ]
            if folder.get("active_docs") != active_docs:
                folder["active_docs"] = active_docs
                self.manifest_changes.append("Aligned docs/active_docs to canonical command docs")
            break

        if self.apply and self.manifest_changes:
            self._write_json(MANIFEST_PATH, updated_manifest)
            self.changed_paths.add(MANIFEST_PATH)

        if self.verbose:
            if self.manifest_changes:
                for item in self.manifest_changes:
                    print(f"[manifest] {item}")
            else:
                print("[manifest] No structural changes required")

    def apply_script_consolidation(self) -> None:
        """Task 3: Delete duplicate paths and enforce canonical script layout."""
        for candidate in self.legacy_candidates:
            rel = candidate.path.relative_to(REPO_ROOT)
            canonical = candidate.canonical_target.relative_to(REPO_ROOT)

            if not self.apply:
                self.consolidation_changes.append(
                    f"Planned duplicate removal {rel} (canonical: {canonical})"
                )
                continue

            if candidate.path.exists():
                candidate.path.unlink()
                self.consolidation_changes.append(
                    f"Removed duplicate {rel} (canonical: {canonical})"
                )
                self.changed_paths.add(candidate.path)

        if self.verbose:
            if self.consolidation_changes:
                for item in self.consolidation_changes:
                    print(f"[consolidate] {item}")
            else:
                print("[consolidate] No duplicate script paths detected")

    def build_validation_checklist(self) -> list[ChecklistItem]:
        """Task 4: Build and execute validation checklist."""
        checklist: list[ChecklistItem] = []

        checklist.append(
            ChecklistItem(
                label=TASK_LABELS["task_1"],
                passed=True,
                detail=f"{len(self.legacy_candidates)} duplicate candidate(s) identified",
            )
        )

        manifest = self._load_manifest()
        legacy_location_ok = (
            manifest.get("LEGACY_ARCHIVED_CONTENT", {}).get("location") == "none"
        )
        orchestration_trigger = (
            manifest.get("PROCESS_PHASES", {}).get("ORCHESTRATION", {}).get("trigger", "")
        )
        trigger_ok = "scripts/data/run_data_pipeline.py" in orchestration_trigger
        checklist.append(
            ChecklistItem(
                label=TASK_LABELS["task_2"],
                passed=legacy_location_ok and trigger_ok,
                detail=f"legacy_location_ok={legacy_location_ok}, trigger_ok={trigger_ok}",
            )
        )

        canonical_ok = all(path.exists() for path in CANONICAL_SCRIPT_TARGETS)
        duplicates_removed = len(self._discover_duplicate_script_paths()) == 0
        checklist.append(
            ChecklistItem(
                label=TASK_LABELS["task_3"],
                passed=canonical_ok and duplicates_removed,
                detail=(
                    f"canonical_ok={canonical_ok}, duplicates_removed={duplicates_removed}"
                ),
            )
        )

        structure_check = self._run_command(
            [sys.executable, "scripts/maintenance/validate_structure.py"],
            check=False,
        )
        checklist.append(
            ChecklistItem(
                label=TASK_LABELS["task_4"],
                passed=structure_check.returncode == 0,
                detail=f"validate_structure.py exit code: {structure_check.returncode}",
            )
        )

        dep_ok, dep_detail = self._check_runtime_dependencies()
        checklist.append(
            ChecklistItem(
                label="Dependency upgrade verification (polars, pydantic-settings)",
                passed=dep_ok,
                detail=dep_detail,
            )
        )

        return checklist

    def handle_branching_operations(self) -> ChecklistItem:
        """Task 5: Stage and commit changes if requested."""
        if not self.commit:
            return ChecklistItem(
                label=TASK_LABELS["task_5"],
                passed=True,
                detail="Commit step skipped (run with --commit to enable)",
            )

        if not self.apply:
            return ChecklistItem(
                label=TASK_LABELS["task_5"],
                passed=False,
                detail="Cannot commit without --apply",
            )

        tracked_candidates = sorted(
            {
                str(path.relative_to(REPO_ROOT))
                for path in self.changed_paths
                if path.exists() or not path.exists()
            }
            | {
                ".repo-structure.json",
                "requirements.txt",
                "requirements.lock.txt",
                "scripts/path_utils.py",
                "scripts/data/analyze_real_data.py",
                "scripts/data/generate_sample_data.py",
                "scripts/data/load_sample_kpis_supabase.py",
                "scripts/data/seed_spanish_loans.py",
                "scripts/maintenance/generate_service_status_report.py",
                "scripts/maintenance/abaco_infra_validator.py",
                "docs/operations/SCRIPT_CANONICAL_MAP.md",
            }
        )

        existing_paths = [path for path in tracked_candidates if (REPO_ROOT / path).exists()]
        self._run_command(["git", "add", "--", *existing_paths], check=True)

        # Stage deletions too (files removed from disk)
        deleted_paths = [path for path in tracked_candidates if not (REPO_ROOT / path).exists()]
        if deleted_paths:
            self._run_command(["git", "add", "--", *deleted_paths], check=True)

        staged = self._run_command(["git", "diff", "--cached", "--name-only"], check=True)
        staged_files = [line for line in staged.stdout.splitlines() if line.strip()]
        if not staged_files:
            return ChecklistItem(
                label=TASK_LABELS["task_5"],
                passed=True,
                detail="No staged changes to commit",
            )

        self._run_command(["git", "commit", "-m", self.commit_message], check=True)
        self.commit_hash = self._run_command(["git", "rev-parse", "--short", "HEAD"], check=True).stdout.strip()

        return ChecklistItem(
            label=TASK_LABELS["task_5"],
            passed=True,
            detail=f"Committed {len(staged_files)} file(s) on {self.current_branch()} at {self.commit_hash}",
        )

    def print_summary(self, checklist: list[ChecklistItem]) -> None:
        """Print concise task summary."""
        print("\nABACO Infra Validator Summary")
        print("=" * 36)

        for item in checklist:
            marker = "[x]" if item.passed else "[ ]"
            print(f"{marker} {item.label}: {item.detail}")

        if self.manifest_changes:
            print("\nManifest updates:")
            for item in self.manifest_changes:
                print(f"- {item}")

        if self.consolidation_changes:
            print("\nConsolidation updates:")
            for item in self.consolidation_changes:
                print(f"- {item}")

        if self.commit_hash:
            print(f"\nCommit: {self.commit_hash}")

    def write_report(self, checklist: list[ChecklistItem]) -> None:
        """Persist JSON report for manual/CI review."""
        payload = {
            "date": date.today().isoformat(),
            "apply_mode": self.apply,
            "commit_mode": self.commit,
            "legacy_candidates": [
                {
                    "path": str(candidate.path.relative_to(REPO_ROOT)),
                    "canonical_target": str(candidate.canonical_target.relative_to(REPO_ROOT)),
                    "reason": candidate.reason,
                }
                for candidate in self.legacy_candidates
            ],
            "manifest_changes": self.manifest_changes,
            "consolidation_changes": self.consolidation_changes,
            "checklist": [
                {
                    "label": item.label,
                    "passed": item.passed,
                    "detail": item.detail,
                }
                for item in checklist
            ],
            "commit_hash": self.commit_hash,
        }

        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _check_runtime_dependencies(self) -> tuple[bool, str]:
        """Check installed versions for required upgraded dependencies."""
        package_names = ("polars", "pydantic-settings")
        versions: list[str] = []

        for package in package_names:
            try:
                versions.append(f"{package}=={metadata.version(package)}")
            except metadata.PackageNotFoundError:
                return False, f"{package} not installed in active environment"

        return True, ", ".join(versions)

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _canonical_targets_by_filename() -> dict[str, Path]:
        targets: dict[str, Path] = {}
        for path in CANONICAL_SCRIPT_TARGETS:
            targets[path.name] = path
        return targets

    def _discover_duplicate_script_paths(self) -> list[LegacyCandidate]:
        """Find duplicate scripts by filename outside canonical paths."""
        candidates: list[LegacyCandidate] = []
        canonical_by_name = self._canonical_targets_by_filename()

        for directory in LEGACY_DUPLICATE_SEARCH_DIRS:
            if not directory.exists() or not directory.is_dir():
                continue

            for candidate_path in sorted(directory.iterdir()):
                if not candidate_path.is_file():
                    continue
                if candidate_path.suffix not in SCRIPT_EXTENSIONS:
                    continue

                canonical_target = canonical_by_name.get(candidate_path.name)
                if canonical_target is None or candidate_path == canonical_target:
                    continue

                reason = "Duplicate script filename found outside canonical location"
                candidates.append(
                    LegacyCandidate(
                        path=candidate_path,
                        canonical_target=canonical_target,
                        reason=reason,
                    )
                )

        return candidates

    @staticmethod
    def _load_manifest() -> dict[str, Any]:
        if not MANIFEST_PATH.exists():
            raise FileNotFoundError(f"Missing manifest: {MANIFEST_PATH}")
        with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _run_command(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=check,
        )

    @staticmethod
    def current_branch() -> str:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="ABACO infra validator (Task 1-5)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply structural/script updates (otherwise report only)",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Stage + commit managed files after --apply",
    )
    parser.add_argument(
        "--commit-message",
        default="chore(maintenance): canonicalize scripts and commands",
        help="Commit message to use with --commit",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed logs")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    validator = AbacoInfraValidator(
        apply=args.apply,
        commit=args.commit,
        commit_message=args.commit_message,
        verbose=args.verbose,
    )
    return validator.run()


if __name__ == "__main__":
    raise SystemExit(main())
