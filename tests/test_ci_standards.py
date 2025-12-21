"""
Test suite for CI/CD standards validation.

Ensures configuration files, workflow files, and project structure
comply with Abaco Loans Analytics standards.
"""

import json
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


class TestVercelConfiguration:
    """Validate vercel.json configuration meets standards."""

    def test_vercel_json_exists(self):
        """Vercel config file must exist at root."""
        vercel_path = PROJECT_ROOT / "vercel.json"
        assert vercel_path.exists(), "vercel.json not found in project root"

    def test_vercel_config_valid_json(self):
        """Config must be valid JSON."""
        vercel_path = PROJECT_ROOT / "vercel.json"
        with open(vercel_path) as f:
            config = json.load(f)
        assert isinstance(config, dict), "vercel.json must contain a JSON object"

    def test_vercel_has_required_fields(self):
        """Config must have required modern fields."""
        vercel_path = PROJECT_ROOT / "vercel.json"
        with open(vercel_path) as f:
            config = json.load(f)

        required_fields = {"framework", "buildCommand", "outputDirectory"}
        missing = required_fields - set(config.keys())
        assert not missing, f"Missing required fields: {missing}"

    def test_vercel_no_deprecated_version_2(self):
        """Config must not use deprecated v2 schema."""
        vercel_path = PROJECT_ROOT / "vercel.json"
        with open(vercel_path) as f:
            config = json.load(f)

        assert config.get("version") != 2, (
            "vercel.json uses deprecated version 2. "
            "Use version 3 or omit the version field."
        )
        assert "builds" not in config, (
            "vercel.json uses deprecated 'builds' field. "
            "Use modern 'buildCommand' instead."
        )
        assert "routes" not in config, (
            "vercel.json uses deprecated 'routes' field. "
            "Modern config handles routing automatically."
        )

    def test_vercel_framework_is_nextjs(self):
        """Config must specify Next.js framework."""
        vercel_path = PROJECT_ROOT / "vercel.json"
        with open(vercel_path) as f:
            config = json.load(f)

        assert (
            config.get("framework") == "nextjs"
        ), "framework must be 'nextjs'"

    def test_vercel_build_command_valid(self):
        """Build command must reference apps/web."""
        vercel_path = PROJECT_ROOT / "vercel.json"
        with open(vercel_path) as f:
            config = json.load(f)

        build_cmd = config.get("buildCommand", "")
        assert "apps/web" in build_cmd or "build" in build_cmd, (
            "buildCommand must reference apps/web or 'build' task"
        )

    def test_vercel_output_directory_valid(self):
        """Output directory must be apps/web/.next."""
        vercel_path = PROJECT_ROOT / "vercel.json"
        with open(vercel_path) as f:
            config = json.load(f)

        output_dir = config.get("outputDirectory", "")
        assert (
            "apps/web" in output_dir and ".next" in output_dir
        ), "outputDirectory must reference 'apps/web/.next'"


class TestGitHubWorkflows:
    """Validate GitHub Actions workflow files."""

    def test_ci_main_workflow_exists(self):
        """Main CI workflow must exist."""
        workflow_path = (
            PROJECT_ROOT / ".github" / "workflows" / "ci-main.yml"
        )
        assert workflow_path.exists(), (
            ".github/workflows/ci-main.yml not found"
        )

    def test_ci_main_no_raw_javascript_in_shell(self):
        """Shell steps must not contain raw JavaScript code."""
        workflow_path = (
            PROJECT_ROOT / ".github" / "workflows" / "ci-main.yml"
        )
        with open(workflow_path) as f:
            content = f.read()

        # Look for JavaScript patterns in shell run commands
        # Match patterns like: run: | const foo = ...
        js_in_shell = re.search(
            r"run:\s*\|\s*\n\s+(const|let|var|function|async|await)\s+",
            content,
        )

        assert not js_in_shell, (
            "Workflow contains JavaScript code in shell step. "
            "Use 'actions/github-script@v7' action or script file instead."
        )

    def test_lint_validation_workflow_exists(self):
        """Lint validation workflow must exist for PR checks."""
        workflow_path = (
            PROJECT_ROOT / ".github" / "workflows" / "ci-lint-validation.yml"
        )
        assert workflow_path.exists(), (
            "Lint validation workflow not found. "
            "Create .github/workflows/ci-lint-validation.yml"
        )

    def test_lint_validation_has_vercel_check(self):
        """Lint workflow must validate Vercel config."""
        workflow_path = (
            PROJECT_ROOT / ".github" / "workflows" / "ci-lint-validation.yml"
        )
        with open(workflow_path) as f:
            content = f.read()

        assert (
            "vercel-config-validation" in content
        ), "Workflow must include vercel-config-validation job"


class TestPackageJsonScripts:
    """Validate package.json lint scripts."""

    def test_web_package_json_exists(self):
        """Web package.json must exist."""
        pkg_path = PROJECT_ROOT / "apps" / "web" / "package.json"
        assert pkg_path.exists(), "apps/web/package.json not found"

    def test_web_has_lint_script(self):
        """Web package.json must have lint script."""
        pkg_path = PROJECT_ROOT / "apps" / "web" / "package.json"
        with open(pkg_path) as f:
            pkg = json.load(f)

        assert "lint" in pkg.get("scripts", {}), (
            "apps/web/package.json missing 'lint' script"
        )

    def test_web_lint_script_uses_eslint(self):
        """Lint script must use ESLint, not 'next lint'."""
        pkg_path = PROJECT_ROOT / "apps" / "web" / "package.json"
        with open(pkg_path) as f:
            pkg = json.load(f)

        lint_script = pkg.get("scripts", {}).get("lint", "")
        assert (
            "eslint" in lint_script
        ), "lint script must use 'eslint' command"
        assert (
            "next lint" not in lint_script
        ), "lint script must not use deprecated 'next lint'"

    def test_web_has_type_check_script(self):
        """Web package.json must have type-check script."""
        pkg_path = PROJECT_ROOT / "apps" / "web" / "package.json"
        with open(pkg_path) as f:
            pkg = json.load(f)

        assert "type-check" in pkg.get("scripts", {}), (
            "apps/web/package.json missing 'type-check' script"
        )

    def test_web_has_build_script(self):
        """Web package.json must have build script."""
        pkg_path = PROJECT_ROOT / "apps" / "web" / "package.json"
        with open(pkg_path) as f:
            pkg = json.load(f)

        assert "build" in pkg.get("scripts", {}), (
            "apps/web/package.json missing 'build' script"
        )


class TestESLintConfiguration:
    """Validate ESLint configuration files."""

    def test_eslint_config_exists(self):
        """ESLint config must exist."""
        eslint_path = PROJECT_ROOT / "apps" / "web" / "eslint.config.mjs"
        assert eslint_path.exists(), (
            "apps/web/eslint.config.mjs not found"
        )

    def test_eslintrc_exists(self):
        """.eslintrc.json must exist."""
        eslintrc_path = (
            PROJECT_ROOT / "apps" / "web" / ".eslintrc.json"
        )
        assert eslintrc_path.exists(), (
            "apps/web/.eslintrc.json not found"
        )

    def test_eslintrc_extends_next(self):
        """ESLint config must extend next/core-web-vitals."""
        eslintrc_path = (
            PROJECT_ROOT / "apps" / "web" / ".eslintrc.json"
        )
        with open(eslintrc_path) as f:
            config = json.load(f)

        extends = config.get("extends", [])
        if isinstance(extends, str):
            extends = [extends]

        assert any(
            "next" in ext for ext in extends
        ), "ESLint config must extend next/core-web-vitals"


class TestDocumentation:
    """Validate documentation exists."""

    def test_linting_standards_doc_exists(self):
        """Linting standards documentation must exist."""
        doc_path = PROJECT_ROOT / "docs" / "LINTING_STANDARDS.md"
        assert doc_path.exists(), (
            "docs/LINTING_STANDARDS.md not found. "
            "Document linting rules and standards."
        )

    def test_linting_standards_doc_not_empty(self):
        """Documentation must have content."""
        doc_path = PROJECT_ROOT / "docs" / "LINTING_STANDARDS.md"
        with open(doc_path) as f:
            content = f.read()

        assert len(content) > 100, (
            "docs/LINTING_STANDARDS.md is too short. "
            "Add comprehensive documentation."
        )

    def test_linting_standards_doc_has_sections(self):
        """Documentation must have required sections."""
        doc_path = PROJECT_ROOT / "docs" / "LINTING_STANDARDS.md"
        with open(doc_path) as f:
            content = f.read()

        required_sections = [
            "ESLint",
            "TypeScript",
            "Vercel",
            "Troubleshooting",
        ]
        for section in required_sections:
            assert section in content, (
                f"Documentation missing '{section}' section"
            )
