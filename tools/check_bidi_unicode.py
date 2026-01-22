#!/usr/bin/env python3
"""
Pre-commit hook to detect and prevent hidden/bidirectional Unicode characters in YAML files.
This prevents supply-chain attacks and accidental parser bypass issues.
"""

import sys
from pathlib import Path

# Unicode bidirectional markers that are security risks
BIDI_MARKERS = [
    "\u202a",  # LEFT-TO-RIGHT EMBEDDING
    "\u202b",  # RIGHT-TO-LEFT EMBEDDING
    "\u202c",  # POP DIRECTIONAL FORMATTING
    "\u202d",  # LEFT-TO-RIGHT OVERRIDE
    "\u202e",  # RIGHT-TO-LEFT OVERRIDE
    "\u2066",  # LEFT-TO-RIGHT ISOLATE
    "\u2067",  # RIGHT-TO-LEFT ISOLATE
    "\u2068",  # FIRST STRONG ISOLATE
    "\u2069",  # POP DIRECTIONAL ISOLATE
    "\u061c",  # ARABIC LETTER MARK (ALM)
    "\u200e",  # LEFT-TO-RIGHT MARK
    "\u200f",  # RIGHT-TO-LEFT MARK
    "\u200d",  # ZERO WIDTH JOINER
    "\u200c",  # ZERO WIDTH NON-JOINER
]

ZERO_WIDTH_CHARS = [
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE
]


def check_file(filepath):
    """Check a file for hidden/BiDi Unicode characters."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

    issues = []

    for i, char in enumerate(content):
        if char in BIDI_MARKERS or char in ZERO_WIDTH_CHARS:
            line_num = content[:i].count("\n") + 1
            char_code = f"U+{ord(char):04X}"
            issues.append(f"  Line {line_num}: Hidden Unicode character {char_code}")

    if issues:
        print(f"\n❌ {filepath}:")
        for issue in issues:
            print(issue)
        return False

    return True


def main():
    # Check only YAML files in workflows
    workflow_dir = Path(".github/workflows")
    if not workflow_dir.exists():
        print("✅ No .github/workflows directory found")
        return 0

    yaml_files = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))

    if not yaml_files:
        print("✅ No YAML workflow files found")
        return 0

    all_ok = True
    for yaml_file in yaml_files:
        if not check_file(yaml_file):
            all_ok = False

    if all_ok:
        print("✅ All workflow YAML files are clean (no hidden/BiDi Unicode)")
        return 0
    else:
        print("\n🚨 FATAL: Hidden/BiDi Unicode characters detected in workflows!")
        print("This is a Severity 0 security issue. Remediate immediately:")
        print("  1. Recreate the files in a trusted editor (VS Code, etc.)")
        print("  2. Verify in hex dump: hexdump -C .github/workflows/file.yml")
        print("  3. Test with: python -m tools.check_bidi_unicode")
        return 2


if __name__ == "__main__":
    sys.exit(main())
