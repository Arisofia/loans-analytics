#!/usr/bin/env python3
"""
Port Consistency Validator for Abaco Loans Analytics

Validates that the canonical dashboard and API ports are consistent across
startup scripts, Docker configurations, and documentation.

Canonical Port Policy:
- Dashboard: 8000 (via STREAMLIT_SERVER_PORT env var or default)
- API: 8000 (via API_PORT env var or default)
- Both services default to port 8000 for alignment with Azure Web App

Exit codes:
- 0: All validations passed
- 1: Port consistency violations found
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

CANONICAL_PORT = 8000
DASHBOARD_PORT_VAR = "STREAMLIT_SERVER_PORT"
API_PORT_VAR = "API_PORT"

# Files to validate and their expected port patterns
VALIDATION_RULES = {
    "startup.sh": {
        "description": "Startup script for Azure Web App",
        "patterns": [
            (r"CANONICAL_PORT=\$\{STREAMLIT_SERVER_PORT:-8000\}", "Canonical port via env override with 8000 default"),
            (r"--server\.port=\$\{CANONICAL_PORT\}", "Streamlit invocation with CANONICAL_PORT variable"),
            (r"Default: 8000 \(Azure Web Apps standard", "Documentation comment referencing 8000 as default"),
        ],
        "must_not_contain": [
            (r"--server\.port=8501", "Hardcoded old port 8501"),
        ],
    },
    "Dockerfile.dashboard": {
        "description": "Dashboard Docker image",
        "patterns": [
            (r'PORT=8000', "Port environment variable set to 8000"),
            (r'STREAMLIT_SERVER_PORT=8000', "Streamlit server port set to 8000"),
            (r"EXPOSE 8000", "Docker EXPOSE directive set to 8000"),
            (r'--server\.port=\$\{PORT:-8000\}', "Port flag uses PORT env var with 8000 default"),
        ],
        "must_not_contain": [
            (r"PORT=8501", "Old hardcoded port 8501"),
            (r"EXPOSE 8501", "Old exposed port 8501"),
        ],
    },
    "backend/python/OPERATIONS.md": {
        "description": "Operations documentation",
        "patterns": [
            (r"localhost:8000", "Local port 8000 documented"),
            (r"canonical port", "Canonical port policy mentioned (case-insensitive)"),
        ],
        "must_not_contain": [
            (r"localhost:8501", "Old documented port 8501"),
        ],
    },
}


def validate_file(file_path: Path, rules: dict) -> Tuple[bool, List[str]]:
    """
    Validate a single file against the given rules.
    
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"Error reading file {file_path}: {e}")
        return False, errors
    
    # Check required patterns
    if "patterns" in rules:
        for pattern, description in rules["patterns"]:
            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                errors.append(
                    f"  Missing required pattern in {file_path.name}:\n"
                    f"    Pattern: {pattern}\n"
                    f"    Expected: {description}"
                )
    
    # Check patterns that must NOT be present
    if "must_not_contain" in rules:
        for pattern, description in rules["must_not_contain"]:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                errors.append(
                    f"  Found forbidden pattern in {file_path.name}:\n"
                    f"    Pattern: {pattern}\n"
                    f"    Message: {description}"
                )
    
    return len(errors) == 0, errors


def main():
    """
    Run all port consistency validations.
    """
    repo_root = Path(__file__).parent.parent.parent
    all_valid = True
    all_errors = []
    
    print("🔍 Validating port consistency across Abaco Loans Analytics...\n")
    print("📋 Canonical Port Policy:")
    print(f"   - Dashboard: {CANONICAL_PORT} (via {DASHBOARD_PORT_VAR} env var)")
    print(f"   - API: {CANONICAL_PORT} (via {API_PORT_VAR} env var)")
    print()
    
    for file_name, rules in VALIDATION_RULES.items():
        file_path = repo_root / file_name
        is_valid, errors = validate_file(file_path, rules)
        
        status_icon = "✅" if is_valid else "❌"
        print(f"{status_icon} {rules['description']}: {file_name}")
        
        if errors:
            all_valid = False
            for error in errors:
                print(f"   {error}")
            all_errors.extend(errors)
        
        print()
    
    # Print summary
    print("=" * 70)
    if all_valid:
        print("✅ All port consistency validations PASSED!")
        print("\nSummary:")
        print(f"  - Canonical port {CANONICAL_PORT} consistently referenced")
        print("  - Environment variable overrides properly configured")
        print("  - Documentation reflects updated port policy")
        return 0
    else:
        print("❌ Port consistency validations FAILED!")
        print(f"\nFound {len(all_errors)} issue(s) to resolve:")
        for i, error in enumerate(all_errors, 1):
            print(f"\n  {i}. {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
