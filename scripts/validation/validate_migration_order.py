#!/usr/bin/env python3
"""
Migration Order Validator for Abaco Loans Analytics

Validates that database migrations follow a deterministic, monotonic ordering policy:
1. Migration names must follow naming convention: NN_description.sql or YYYYMMDDhhmmss_description.sql
2. Execution order must be strictly monotonic (sortable)
3. No duplicate migration names
4. Critical migrations (00_init_*) must execute first

This validator is part of Workstream 1 (Migration Order Determinism) and ensures
that database replays are deterministic and not subject to filesystem ordering or
race conditions.

Exit codes:
- 0: All validations passed
- 1: Migration order violations found
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple
import yaml

MIGRATION_DIR = Path(__file__).parent.parent.parent / "db" / "migrations"
INDEX_FILE = MIGRATION_DIR / "migration_index.yml"

# Migration naming pattern: NN_name or YYYYMMDDhhmmss_name
MIGRATION_PATTERN = re.compile(r'^(\d{2,14})_[a-z0-9_]+\.sql$')

# Init migration must come first
INIT_MIGRATION_PATTERN = re.compile(r'^000?_init')


def extract_sort_key(migration_name: str) -> Tuple[int, str]:
    """
    Extract numeric sort key from migration name.
    Format: NN_name or YYYYMMDDhhmmss_name
    Returns: (numeric_part, name)
    """
    match = MIGRATION_PATTERN.match(migration_name)
    if not match:
        raise ValueError(f"Invalid migration name format: {migration_name}")
    
    numeric_part = match.group(1)
    return (int(numeric_part), migration_name)


def validate_migration_format(migrations: List[str]) -> Tuple[bool, List[str]]:
    """Validate that all migrations follow naming convention."""
    errors = []
    for migration in migrations:
        if not MIGRATION_PATTERN.match(migration):
            errors.append(
                f"  Invalid migration name format: {migration}\n"
                f"    Expected format: NN_description.sql or YYYYMMDDhhmmss_description.sql"
            )
    return len(errors) == 0, errors


def validate_monotonic_order(migrations: List[str]) -> Tuple[bool, List[str]]:
    """Validate that migrations are in strictly monotonic order."""
    errors = []
    
    try:
        sorted_migrations = sorted(migrations, key=lambda m: extract_sort_key(m))
    except ValueError as e:
        errors.append(f"  {e}")
        return False, errors
    
    if migrations != sorted_migrations:
        errors.append("  Migration order is not monotonic (not sortable).")
        errors.append("  Expected sorted order:")
        for i, mig in enumerate(sorted_migrations, 1):
            mark = "[OK]" if i <= len(migrations) and mig == migrations[i-1] else "[X]"
            errors.append(f"    {i:2d}. {mig} {mark}")
        errors.append("\n  Current order:")
        for i, mig in enumerate(migrations, 1):
            expected = sorted_migrations[i-1] if i <= len(sorted_migrations) else "?"
            mark = "[OK]" if mig == expected else "[X]"
            errors.append(f"    {i:2d}. {mig} {mark}")
    
    return len(errors) == 0, errors


def validate_no_duplicates(migrations: List[str]) -> Tuple[bool, List[str]]:
    """Validate that there are no duplicate migration names."""
    errors = []
    seen = set()
    duplicates = []
    
    for migration in migrations:
        if migration in seen:
            duplicates.append(migration)
        seen.add(migration)
    
    if duplicates:
        errors.append(f"  Found {len(duplicates)} duplicate migration(s):")
        for dup in sorted(set(duplicates)):
            count = migrations.count(dup)
            errors.append(f"    - {dup} (appears {count} times)")
    
    return len(errors) == 0, errors


def validate_init_first(migrations: List[str]) -> Tuple[bool, List[str]]:
    """Validate that init migrations come first."""
    errors = []
    
    init_migrations = [m for m in migrations if INIT_MIGRATION_PATTERN.match(m)]
    if not init_migrations:
        errors.append("  No init migration found (expected: 00_init_*.sql)")
        return False, errors
    
    first_migration = migrations[0] if migrations else None
    if first_migration and not INIT_MIGRATION_PATTERN.match(first_migration):
        errors.append(
            f"  Init migration must execute first.\n"
            f"    Expected first: {init_migrations[0]}\n"
            f"    Found first: {first_migration}"
        )
    
    return len(errors) == 0, errors


def validate_index_file(index_path: Path) -> Tuple[bool, List[str], List[str]]:
    """Load and validate migration_index.yml."""
    errors = []
    
    if not index_path.exists():
        errors.append(f"Migration index file not found: {index_path}")
        return False, errors, []
    
    try:
        with open(index_path, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        errors.append(f"Error reading migration_index.yml: {e}")
        return False, errors, []
    
    if not data or 'ordered_migrations' not in data:
        errors.append("Migration index missing 'ordered_migrations' key")
        return False, errors, []
    
    migrations = data.get('ordered_migrations', [])
    if not migrations:
        errors.append("No migrations found in ordered_migrations list")
        return False, errors, []
    
    return True, errors, migrations


def main():
    """Run all migration order validations."""
    print("[INFO] Validating migration order and determinism...\n")
    
    # Load migration index
    is_loaded, load_errors, migrations = validate_index_file(INDEX_FILE)
    if not is_loaded:
        print("[FAIL] Failed to load migration index")
        for error in load_errors:
            print(f"   {error}")
        return 1
    
    print(f"[LIST] Found {len(migrations)} migrations in index\n")
    
    all_valid = True
    all_errors = []
    
    # Run all validations
    validations = [
        ("Migration naming convention", validate_migration_format),
        ("Monotonic ordering", validate_monotonic_order),
        ("No duplicate migrations", validate_no_duplicates),
        ("Init migration first", validate_init_first),
    ]
    
    for validation_name, validation_func in validations:
        is_valid, errors = validation_func(migrations)
        status_icon = "[PASS]" if is_valid else "[FAIL]"
        print(f"{status_icon} {validation_name}")
        
        if errors:
            all_valid = False
            for error in errors:
                print(f"   {error}")
            all_errors.extend(errors)
        
        print()
    
    # Print summary
    print("=" * 70)
    if all_valid:
        print("[PASS] All migration order validations PASSED!")
        print("\nSummary:")
        print(f"  - All {len(migrations)} migrations follow naming convention")
        print("  - Migrations are in strictly monotonic order")
        print("  - No duplicate migrations")
        print("  - Init migration executes first")
        return 0
    else:
        print("[FAIL] Migration order validations FAILED!")
        print(f"\nFound {len(all_errors)} issue(s) to resolve:")
        for i, error in enumerate(all_errors, 1):
            if not error.startswith("  "):
                print(f"\n{i}. {error}")
            else:
                print(error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
