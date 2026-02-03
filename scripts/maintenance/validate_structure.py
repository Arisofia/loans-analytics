#!/usr/bin/env python3
"""
Repository Structure Validator

Validates that all expected files and folders from .repo-structure.json
exist in the repository. Reports missing components and verifies completeness.

Usage:
    python scripts/validate_structure.py
    python scripts/validate_structure.py --verbose
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"
    BOLD = "\033[1m"


def load_structure_definition() -> Dict:
    """Load .repo-structure.json"""
    repo_root = Path(__file__).parent.parent.parent  # 3 levels up to repo root
    structure_file = repo_root / ".repo-structure.json"

    if not structure_file.exists():
        print(f"{Colors.RED}❌ .repo-structure.json not found{Colors.END}")
        sys.exit(1)

    with open(structure_file, "r") as f:
        return json.load(f)


def check_path(path: Path, item_type: str = "file") -> bool:
    """Check if path exists"""
    if item_type == "file":
        return path.is_file()
    elif item_type == "folder":
        return path.is_dir()
    else:
        return path.exists()


def _validate_file(path_str: str, path: Path, purpose: str, verbose: bool) -> Tuple[bool, tuple]:
    """Validate a single file and return (exists, result_tuple)."""
    if check_path(path, "file"):
        print(f"{Colors.GREEN}✅{Colors.END} {path_str}")
        if verbose:
            print(f"   Purpose: {purpose}")
        return True, (path_str, "file", purpose)
    else:
        print(f"{Colors.RED}❌{Colors.END} {path_str} (MISSING)")
        return False, (path_str, "file", purpose)


def _validate_expected_files(path: Path, expected_files: list, verbose: bool) -> None:
    """Validate expected files within a directory."""
    if not (expected_files and verbose):
        return

    for file_name in expected_files:
        file_path = path / file_name
        if file_path.exists():
            print(f"   {Colors.GREEN}✓{Colors.END} {file_name}")
        else:
            print(f"   {Colors.YELLOW}⚠{Colors.END} {file_name} (missing)")


def _validate_directory(
    path_str: str, path: Path, folder_def: dict, purpose: str, verbose: bool
) -> Tuple[bool, tuple]:
    """Validate a directory and return (exists, result_tuple)."""
    if check_path(path, "folder"):
        print(f"{Colors.GREEN}✅{Colors.END} {path_str}/")
        if verbose:
            print(f"   Purpose: {purpose}")

        expected_files = folder_def.get("files", [])
        _validate_expected_files(path, expected_files, verbose)
        return True, (path_str, "folder", purpose)
    else:
        print(f"{Colors.RED}❌{Colors.END} {path_str}/ (MISSING)")
        return False, (path_str, "folder", purpose)


def _process_folder_item(
    folder_def: dict, repo_root: Path, verbose: bool
) -> Tuple[tuple | None, tuple | None]:
    """Process a single folder definition and return (found_tuple, missing_tuple)."""
    path_str = folder_def.get("path", "")
    purpose = folder_def.get("purpose", "N/A")

    if not path_str:
        return None, None

    path = repo_root / path_str

    if path_str.endswith(".py"):
        exists, result = _validate_file(path_str, path, purpose, verbose)
    else:
        exists, result = _validate_directory(path_str, path, folder_def, purpose, verbose)

    return (result, None) if exists else (None, result)


def validate_active_folders(
    structure: Dict, repo_root: Path, verbose: bool = False
) -> Tuple[List, List]:
    """Validate all active production folders"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Validating ACTIVE PRODUCTION WORKFLOW{Colors.END}")
    print("=" * 80)

    folders = structure.get("ACTIVE_PRODUCTION_WORKFLOW", {}).get("folders", [])

    found = []
    missing = []

    for folder_def in folders:
        found_item, missing_item = _process_folder_item(folder_def, repo_root, verbose)
        if found_item:
            found.append(found_item)
        if missing_item:
            missing.append(missing_item)

    return found, missing


def validate_config_files(repo_root: Path, verbose: bool = False) -> Tuple[List, List]:
    """Validate configuration files"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Validating CONFIGURATION FILES{Colors.END}")
    print("=" * 80)

    config_files = [
        "config/pipeline.yml",
        "config/business_rules.yaml",
        "config/kpis/kpi_definitions.yaml",
    ]

    found = []
    missing = []

    for config_file in config_files:
        path = repo_root / config_file

        if check_path(path, "file"):
            found.append((config_file, "file", "Configuration"))
            print(f"{Colors.GREEN}✅{Colors.END} {config_file}")

            if verbose:
                size = path.stat().st_size
                print(f"   Size: {size:,} bytes")
        else:
            missing.append((config_file, "file", "Configuration"))
            print(f"{Colors.RED}❌{Colors.END} {config_file} (MISSING)")

    return found, missing


def validate_archive_structure(structure: Dict, repo_root: Path) -> Tuple[List, List]:
    """Validate archive_legacy structure"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Validating ARCHIVE STRUCTURE{Colors.END}")
    print("=" * 80)

    archive_root = repo_root / "archive_legacy"

    found = []
    missing = []

    if not archive_root.exists():
        print(f"{Colors.RED}❌{Colors.END} archive_legacy/ (MISSING)")
        missing.append(("archive_legacy/", "folder", "Archive"))
        return found, missing

    found.append(("archive_legacy/", "folder", "Archive"))
    print(f"{Colors.GREEN}✅{Colors.END} archive_legacy/")

    # Check for README
    readme = archive_root / "README.md"
    if readme.exists():
        found.append(("archive_legacy/README.md", "file", "Documentation"))
        print(f"{Colors.GREEN}✅{Colors.END} archive_legacy/README.md")
    else:
        missing.append(("archive_legacy/README.md", "file", "Documentation"))
        print(f"{Colors.YELLOW}⚠{Colors.END} archive_legacy/README.md (recommended)")

    return found, missing


def generate_report(found: List, missing: List, structure: Dict):
    """Generate final validation report"""
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}VALIDATION REPORT{Colors.END}")
    print("=" * 80)

    total = len(found) + len(missing)
    found_count = len(found)
    missing_count = len(missing)

    completion_rate = (found_count / total * 100) if total > 0 else 0

    print(f"\nTotal Expected: {total}")
    print(f"{Colors.GREEN}Found: {found_count}{Colors.END}")
    print(f"{Colors.RED}Missing: {missing_count}{Colors.END}")
    print(f"\nCompletion: {completion_rate:.1f}%")

    # Status badge
    status = structure.get("status", "UNKNOWN")
    if completion_rate == 100:
        print(f"\n{Colors.GREEN}✅ Repository Status: {status} - COMPLETE{Colors.END}")
    elif completion_rate >= 80:
        print(f"\n{Colors.YELLOW}⚠️ Repository Status: {status} - MOSTLY COMPLETE{Colors.END}")
    else:
        print(f"\n{Colors.RED}❌ Repository Status: {status} - INCOMPLETE{Colors.END}")

    if missing:
        print(f"\n{Colors.BOLD}Missing Components:{Colors.END}")
        for path, item_type, purpose in missing:
            print(f"  - {path} ({item_type})")
            if purpose != "N/A":
                print(f"    Purpose: {purpose}")

    print("\n" + "=" * 80)

    return completion_rate == 100


def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate repository structure")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.parent  # 3 levels up to repo root

    print(f"{Colors.BOLD}{Colors.BLUE}REPOSITORY STRUCTURE VALIDATION{Colors.END}")
    print(f"Repository: {repo_root.name}")
    print(f"Path: {repo_root}")

    # Load structure definition
    structure = load_structure_definition()

    # Validate components
    all_found = []
    all_missing = []

    # Active folders
    found, missing = validate_active_folders(structure, repo_root, args.verbose)
    all_found.extend(found)
    all_missing.extend(missing)

    # Configuration files
    found, missing = validate_config_files(repo_root, args.verbose)
    all_found.extend(found)
    all_missing.extend(missing)

    # Archive structure
    found, missing = validate_archive_structure(structure, repo_root)
    all_found.extend(found)
    all_missing.extend(missing)

    # Generate report
    is_complete = generate_report(all_found, all_missing, structure)

    # Exit code
    sys.exit(0 if is_complete else 1)


if __name__ == "__main__":
    main()
