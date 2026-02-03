#!/usr/bin/env python3
"""
Repository Structure Validator

Validates that core expected files and folders exist in the repository.
Uses .repo-structure.json as source of truth.

Usage:
    python scripts/validate_structure.py
    python scripts/validate_structure.py --verbose
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Tuple


ROOT = Path(__file__).resolve().parents[1]
STRUCTURE_FILE = ROOT / ".repo-structure.json"


def load_expected_paths() -> List[Path]:
    """Load expected component paths from .repo-structure.json or use fallback."""
    if not STRUCTURE_FILE.exists():
        # Fallback: minimal critical components
        return [
            ROOT / "src" / "pipeline" / "orchestrator.py",
            ROOT / "config" / "pipeline.yml",
            ROOT / "scripts" / "data" / "run_data_pipeline.py",
        ]

    try:
        data = json.loads(STRUCTURE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        # If file is malformed, use fallback
        return [
            ROOT / "src" / "pipeline" / "orchestrator.py",
            ROOT / "config" / "pipeline.yml",
            ROOT / "scripts" / "data" / "run_data_pipeline.py",
        ]

    expected_files: List[Path] = []

    # Extract folders from ACTIVE_PRODUCTION_WORKFLOW
    for entry in data.get("ACTIVE_PRODUCTION_WORKFLOW", {}).get("folders", []):
        path = entry.get("path")
        if path:
            expected_files.append(ROOT / path)

    # Extract configuration files
    for entry in data.get("CONFIGURATION_FILES", {}).get("files", []):
        path = entry.get("path")
        if path:
            expected_files.append(ROOT / path)

    return expected_files


def validate_structure(verbose: bool = False) -> Tuple[int, int]:
    """Validate repo structure and return (total, missing_count)."""
    expected = load_expected_paths()
    missing: List[Path] = [p for p in expected if not p.exists()]

    if verbose:
        print("✅ Repository Structure Validation")
        print(f"Root: {ROOT}")
        print(f"Expected components: {len(expected)}")

        if missing:
            print("\n❌ Missing components:")
            for p in missing:
                print(f"  - {p.relative_to(ROOT)}")
        else:
            print("\n✅ All expected components are present.")

    total = len(expected)
    missing_count = len(missing)
    status = "IMPLEMENTED - COMPLETE" if missing_count == 0 else "INCOMPLETE"
    found_count = total - missing_count

    if verbose:
        print(
            f"\n📊 Repository Status: {status} "
            f"(Found: {found_count}/{total}, Missing: {missing_count})"
        )
    else:
        print(
            f"Repository Status: {status} "
            f"(Found: {found_count}/{total}, Missing: {missing_count})"
        )

    return total, missing_count


def main(argv: List[str] | None = None) -> int:
    """Main entry point."""
    argv = argv or sys.argv[1:]
    verbose = "--verbose" in argv
    _, missing_count = validate_structure(verbose=verbose)
    return 0 if missing_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
