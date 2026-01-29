#!/usr/bin/env python3
"""Validate agent implementation checklist.

This script checks if new or modified agents meet the implementation checklist requirements.
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from scripts.path_utils import validate_path


class AgentChecklistValidator:
    """Validate agent implementation against checklist."""

    def __init__(self, file_path: str):
        """Initialize validator.

        Args:
            file_path: Path to the agent file
        """
        # Validate file path for security (CWE-22: Path Traversal)
        validated_path = validate_path(file_path, base_dir=".", must_exist=True)
        self.file_path = validated_path
        self.content = self.file_path.read_text()
        self.tree = ast.parse(self.content)
        self.results: Dict[str, bool] = {}
        self.messages: List[str] = []

    def validate_all(self) -> Tuple[bool, List[str]]:
        """Run all validation checks.

        Returns:
            Tuple of (all_passed, messages)
        """
        self.check_base_agent_extension()
        self.check_required_methods()
        self.check_docstrings()
        self.check_error_handling()
        self.check_no_hardcoded_secrets()

        all_passed = all(self.results.values())
        return all_passed, self.messages

    def check_base_agent_extension(self) -> None:
        """Check if agent extends BaseAgent or similar base class."""
        has_base = False
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                if node.bases:
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            if "Agent" in base.id or "Base" in base.id:
                                has_base = True
                                break

        self.results["base_agent"] = has_base
        if has_base:
            self.messages.append("✅ Agent extends base class")
        else:
            self.messages.append("⚠️  Agent should extend BaseAgent or similar")

    def check_required_methods(self) -> None:
        """Check for required agent methods."""
        required_methods = ["execute", "__init__"]
        found_methods = set()

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                found_methods.add(node.name)

        has_all = all(method in found_methods for method in required_methods)
        self.results["required_methods"] = has_all

        if has_all:
            self.messages.append("✅ Required methods present (execute, __init__)")
        else:
            missing = set(required_methods) - found_methods
            self.messages.append(f"⚠️  Missing required methods: {missing}")

    def check_docstrings(self) -> None:
        """Check for proper docstrings."""
        has_module_docstring = ast.get_docstring(self.tree) is not None
        class_docstrings = 0
        method_docstrings = 0
        total_classes = 0
        total_methods = 0

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                total_classes += 1
                if ast.get_docstring(node):
                    class_docstrings += 1
            elif isinstance(node, ast.FunctionDef):
                if not node.name.startswith("_") or node.name == "__init__":
                    total_methods += 1
                    if ast.get_docstring(node):
                        method_docstrings += 1

        has_good_docs = (
            has_module_docstring
            and (class_docstrings / max(total_classes, 1)) >= 0.8
            and (method_docstrings / max(total_methods, 1)) >= 0.6
        )

        self.results["docstrings"] = has_good_docs
        if has_good_docs:
            self.messages.append("✅ Adequate documentation with docstrings")
        else:
            self.messages.append(
                f"⚠️  Documentation needs improvement: "
                f"{class_docstrings}/{total_classes} classes, "
                f"{method_docstrings}/{total_methods} methods documented"
            )

    def check_error_handling(self) -> None:
        """Check for proper error handling."""
        has_try_except = False
        has_error_method = False

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Try):
                has_try_except = True
            if isinstance(node, ast.FunctionDef):
                if "error" in node.name.lower() or "handle" in node.name.lower():
                    has_error_method = True

        has_error_handling = has_try_except or has_error_method
        self.results["error_handling"] = has_error_handling

        if has_error_handling:
            self.messages.append("✅ Error handling implemented")
        else:
            self.messages.append("⚠️  No error handling found (try/except or error methods)")

    def check_no_hardcoded_secrets(self) -> None:
        """Check for hardcoded secrets or API keys."""
        secret_patterns = [
            r"api[_-]?key\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]",
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]",
        ]

        has_hardcoded = False
        for pattern in secret_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                has_hardcoded = True
                break

        # Check for os.getenv or environment variable usage (good practice)
        has_env_usage = "os.getenv" in self.content or "os.environ" in self.content

        no_secrets = not has_hardcoded
        self.results["no_secrets"] = no_secrets

        if no_secrets and has_env_usage:
            self.messages.append("✅ No hardcoded secrets, using environment variables")
        elif no_secrets:
            self.messages.append("✅ No hardcoded secrets detected")
        else:
            self.messages.append("❌ SECURITY: Hardcoded secrets detected!")


def validate_agent_files(files: List[str]) -> bool:
    """Validate multiple agent files.

    Args:
        files: List of file paths to validate

    Returns:
        True if all files pass validation
    """
    all_passed = True

    for file_path in files:
        if not Path(file_path).exists():
            print(f"\n⚠️  File not found: {file_path}")
            continue

        if not file_path.endswith(".py"):
            continue

        if "test" in file_path or "__pycache__" in file_path:
            continue

        print(f"\n📋 Validating: {file_path}")
        validator = AgentChecklistValidator(file_path)
        passed, messages = validator.validate_all()

        for message in messages:
            print(f"  {message}")

        if not passed:
            all_passed = False
            print(f"  ❌ Validation failed for {file_path}")
        else:
            print("  ✅ All checks passed")

    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate agent implementation checklist")
    parser.add_argument(
        "files",
        nargs="*",
        help="Agent files to validate (default: all in src/agents/)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any check fails",
    )
    args = parser.parse_args()

    if args.files:
        files = args.files
    else:
        # Find all Python files in src/agents/
        agents_dir = Path("src/agents")
        if agents_dir.exists():
            files = [str(f) for f in agents_dir.rglob("*.py")]
        else:
            print("❌ Error: src/agents/ directory not found")
            sys.exit(1)

    print("🔍 Agent Implementation Checklist Validation\n")
    print(f"Checking {len(files)} file(s)...")

    all_passed = validate_agent_files(files)

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All agent files passed validation!")
        sys.exit(0)
    else:
        print("⚠️  Some checks failed. Review the output above.")
        if args.strict:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
