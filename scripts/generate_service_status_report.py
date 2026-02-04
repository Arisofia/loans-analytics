#!/usr/bin/env python3
"""Generate comprehensive service status report.

This script checks all system components and generates a markdown report
showing the current status of the abaco-loans-analytics system.
It continues checking all components even if some fail.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ServiceStatusChecker:
    """Check status of all system components."""

    def __init__(self):
        self.results: dict[str, dict[str, Any]] = {}
        self.repo_root = Path(__file__).parent.parent

    def run_command(self, cmd: list[str], timeout: int = 30) -> tuple[bool, str, str]:
        """Run a command and return success status, stdout, stderr.
        
        Args:
            cmd: Command to run as list of strings
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.repo_root,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)

    def check_git_status(self) -> dict[str, Any]:
        """Check Git repository status."""
        status = {
            "name": "Git Repository",
            "success": True,
            "details": {},
        }
        overall_success = True

        # Get current branch
        success, stdout, stderr = self.run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        )
        if success:
            status["details"]["current_branch"] = stdout.strip()
        else:
            status["details"]["current_branch"] = "unknown"
            status["details"]["current_branch_error"] = (
                stderr.strip() or "git rev-parse failed"
            )
            overall_success = False

        # Get latest commit
        success, stdout, stderr = self.run_command(
            ["git", "log", "--oneline", "-1"]
        )
        if success:
            status["details"]["latest_commit"] = stdout.strip()
        else:
            status["details"]["latest_commit"] = "unknown"
            status["details"]["latest_commit_error"] = (
                stderr.strip() or "git log failed"
            )
            overall_success = False

        # Check for uncommitted changes (exclude report files to avoid false positives)
        success, stdout, stderr = self.run_command(["git", "status", "--porcelain"])
        if success:
            # Filter out service_status_report files
            filtered_lines = [
                line for line in stdout.strip().split("\n")
                if line and not any(
                    exclude in line
                    for exclude in ["service_status_report.md", "service_status_report.json"]
                )
            ]
            has_changes = bool(filtered_lines)
            status["details"]["uncommitted_changes"] = has_changes
            status["details"]["clean_working_tree"] = not has_changes
        else:
            status["details"]["uncommitted_changes"] = "unknown"
            status["details"]["clean_working_tree"] = "unknown"
            status["details"]["working_tree_status_error"] = (
                stderr.strip() or "git status failed"
            )
            overall_success = False

        status["success"] = overall_success
        return status

    def check_python_environment(self) -> dict[str, Any]:
        """Check Python environment and dependencies."""
        status = {
            "name": "Python Environment",
            "success": True,
            "details": {},
        }
        
        # Python version
        status["details"]["python_version"] = sys.version.split()[0]
        
        # Virtual environment
        status["details"]["virtual_env_active"] = "VIRTUAL_ENV" in os.environ
        status["details"]["virtual_env_path"] = os.environ.get("VIRTUAL_ENV", "None")
        
        # Check key packages
        packages = ["pandas", "pydantic", "pytest", "opentelemetry", "asyncpg"]
        installed_packages = {}
        for package in packages:
            try:
                __import__(package.replace("-", "_"))
                installed_packages[package] = "✅ Installed"
            except ImportError:
                installed_packages[package] = "❌ Not installed"
                status["success"] = False
                
        status["details"]["packages"] = installed_packages
        
        return status

    def check_tests(self) -> dict[str, Any]:
        """Check test suite status."""
        status = {
            "name": "Test Suite",
            "success": False,
            "details": {},
        }
        
        # Check if tests directory exists (for informational purposes)
        tests_dir = self.repo_root / "tests"
        status["details"]["tests_directory_exists"] = tests_dir.exists()
        
        # Always attempt to run pytest so that pytest.ini testpaths are respected,
        # even if the legacy tests/ directory does not exist.
        
        # Try to run pytest using repository configuration
        success, stdout, stderr = self.run_command(
            [sys.executable, "-m", "pytest", "-v", "--tb=short", "--maxfail=5"],
            timeout=120
        )
        
        status["success"] = success
        
        # Parse test results
        if "passed" in stdout or "passed" in stderr:
            output = stdout + stderr
            # Extract test count
            for line in output.split("\n"):
                if "passed" in line or "failed" in line:
                    status["details"]["result_summary"] = line.strip()
                    break
        else:
            status["details"]["result_summary"] = "No test results"
            
        status["details"]["exit_code"] = "0" if success else "non-zero"
        
        return status

    def check_linting(self) -> dict[str, Any]:
        """Check code quality/linting status."""
        status = {
            "name": "Code Quality (Linting)",
            "success": True,
            "details": {},
        }
        
        # Check ruff
        success, stdout, stderr = self.run_command(
            [sys.executable, "-m", "ruff", "check", ".", "--quiet"],
            timeout=60
        )
        status["details"]["ruff"] = "✅ Pass" if success else "❌ Issues found"
        if not success:
            status["success"] = False
            
        # Check for TODO count - use Python instead of grep for portability
        try:
            todo_count = 0
            for pattern in ["src/", "python/"]:
                search_dir = self.repo_root / pattern
                if search_dir.exists():
                    for py_file in search_dir.rglob("*.py"):
                        try:
                            with open(py_file, "r", encoding="utf-8") as f:
                                todo_count += sum(1 for line in f if "TODO:" in line)
                        except Exception:
                            pass  # Skip files that can't be read
            status["details"]["active_todos"] = f"{todo_count} items"
        except Exception as e:
            status["details"]["active_todos"] = f"unknown (error: {str(e)})"
        
        return status

    def check_supabase_configuration(self) -> dict[str, Any]:
        """Check Supabase configuration.

        A successful status requires both SUPABASE_URL and a Supabase key
        (SUPABASE_ANON_KEY or SUPABASE_KEY) to be configured.
        """
        status = {
            "name": "Supabase",
            "success": False,
            "details": {},
        }

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

        status["details"]["url_configured"] = supabase_url is not None
        status["details"]["key_configured"] = supabase_key is not None

        if not supabase_url:
            status["details"]["message"] = "SUPABASE_URL not configured"
            return status

        if not supabase_key:
            status["details"]["message"] = (
                "Supabase URL configured but key missing; connectivity not available"
            )
            return status

        status["success"] = True
        status["details"]["message"] = "Configuration complete"
        return status

    def check_pipeline(self) -> dict[str, Any]:
        """Check data pipeline status."""
        status = {
            "name": "Data Pipeline",
            "success": True,
            "details": {},
        }
        
        pipeline_script = self.repo_root / "scripts" / "run_data_pipeline.py"
        status["details"]["script_exists"] = pipeline_script.exists()
        
        # Check pipeline configuration
        config_file = self.repo_root / "config" / "pipeline.yml"
        status["details"]["config_exists"] = config_file.exists()
        
        # Check if pipeline modules exist
        pipeline_dir = self.repo_root / "src" / "pipeline"
        if pipeline_dir.exists():
            modules = ["ingestion.py", "transformation.py", "calculation.py", "output.py"]
            existing_modules = [m for m in modules if (pipeline_dir / m).exists()]
            status["details"]["modules"] = f"{len(existing_modules)}/{len(modules)} present"
        else:
            status["success"] = False
            status["details"]["modules"] = "Pipeline directory not found"
            
        return status

    def check_multi_agent_system(self) -> dict[str, Any]:
        """Check multi-agent system status."""
        status = {
            "name": "Multi-Agent System",
            "success": True,
            "details": {},
        }
        
        # Check if multi-agent directory exists
        agent_dir = self.repo_root / "python" / "multi_agent"
        status["details"]["directory_exists"] = agent_dir.exists()
        
        if not agent_dir.exists():
            status["success"] = False
            status["details"]["message"] = "Multi-agent directory not found"
            return status
            
        # Check for key modules
        key_files = ["orchestrator.py", "protocol.py", "guardrails.py", "tracing.py"]
        existing_files = [f for f in key_files if (agent_dir / f).exists()]
        status["details"]["core_modules"] = f"{len(existing_files)}/{len(key_files)} present"
        
        # Check LLM provider configuration
        llm_configured = bool(
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("ANTHROPIC_API_KEY") or 
            os.getenv("GEMINI_API_KEY")
        )
        status["details"]["llm_provider_configured"] = llm_configured
        
        return status

    def check_documentation(self) -> dict[str, Any]:
        """Check documentation status."""
        status = {
            "name": "Documentation",
            "success": True,
            "details": {},
        }
        
        docs_dir = self.repo_root / "docs"
        status["details"]["docs_directory_exists"] = docs_dir.exists()
        
        if docs_dir.exists():
            # Count documentation files
            md_files = list(docs_dir.glob("*.md"))
            status["details"]["markdown_files"] = len(md_files)
            
            # Check for key documentation
            key_docs = ["README.md", "DEVELOPMENT.md", "DEPLOYMENT_OPERATIONS_GUIDE.md"]
            existing_docs = [d for d in key_docs if (docs_dir / d).exists()]
            status["details"]["key_docs"] = f"{len(existing_docs)}/{len(key_docs)} present"
        else:
            status["success"] = False
            status["details"]["message"] = "Documentation directory not found"
            
        return status

    def check_ci_cd(self) -> dict[str, Any]:
        """Check CI/CD configuration."""
        status = {
            "name": "CI/CD",
            "success": True,
            "details": {},
        }
        
        workflows_dir = self.repo_root / ".github" / "workflows"
        status["details"]["workflows_directory_exists"] = workflows_dir.exists()
        
        if workflows_dir.exists():
            # Count workflow files
            workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            status["details"]["workflow_count"] = len(workflow_files)
            
            # Check for key workflows
            key_workflows = ["unified-tests.yml", "security-scan.yml", "deployment.yml"]
            existing_workflows = [w for w in key_workflows if (workflows_dir / w).exists()]
            status["details"]["key_workflows"] = f"{len(existing_workflows)}/{len(key_workflows)} present"
        else:
            status["success"] = False
            status["details"]["message"] = "Workflows directory not found"
            
        return status

    def run_all_checks(self) -> dict[str, dict[str, Any]]:
        """Run all health checks and return results.
        
        This method continues checking all components even if some fail.
        """
        print("🔍 Running service status checks...\n")
        
        checks = [
            ("git", self.check_git_status),
            ("python", self.check_python_environment),
            ("tests", self.check_tests),
            ("linting", self.check_linting),
            ("supabase", self.check_supabase_configuration),
            ("pipeline", self.check_pipeline),
            ("agents", self.check_multi_agent_system),
            ("docs", self.check_documentation),
            ("cicd", self.check_ci_cd),
        ]
        
        for key, check_func in checks:
            try:
                print(f"  Checking {check_func.__doc__.split('.')[0].strip()}...")
                self.results[key] = check_func()
            except Exception as e:
                print(f"  ❌ Error in {key}: {e}")
                self.results[key] = {
                    "name": key.title(),
                    "success": False,
                    "details": {"error": str(e)},
                }
        
        print("\n✅ All checks completed\n")
        return self.results


def generate_markdown_report(results: dict[str, dict[str, Any]]) -> str:
    """Generate markdown report from check results."""
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Count overall status
    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r.get("success", False))
    
    lines = [
        "# Service Status Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Status:** {passed_checks}/{total_checks} checks passed",
        "",
        "## Executive Summary",
        "",
    ]
    
    # Overall status
    if passed_checks == total_checks:
        lines.append("✅ **All systems operational** - All health checks passed successfully.")
    elif passed_checks >= total_checks * 0.7:
        lines.append(f"⚠️ **Degraded** - {total_checks - passed_checks} component(s) need attention.")
    else:
        lines.append(f"❌ **Critical** - Multiple systems require immediate attention.")
    
    lines.extend(["", "---", "", "## Component Status", ""])
    
    # Generate detailed status for each component
    for key, result in results.items():
        name = result.get("name", key.title())
        success = result.get("success", False)
        details = result.get("details", {})
        
        # Header
        status_icon = "✅" if success else "❌"
        lines.append(f"### {status_icon} {name}")
        lines.append("")
        
        # Status
        status_text = "Operational" if success else "Issues Detected"
        lines.append(f"**Status:** {status_text}")
        lines.append("")
        
        # Details
        if details:
            lines.append("**Details:**")
            lines.append("")
            for detail_key, detail_value in details.items():
                # Format key nicely
                formatted_key = detail_key.replace("_", " ").title()
                
                # Handle different value types
                if isinstance(detail_value, dict):
                    lines.append(f"- **{formatted_key}:**")
                    for sub_key, sub_value in detail_value.items():
                        lines.append(f"  - {sub_key}: {sub_value}")
                elif isinstance(detail_value, bool):
                    bool_text = "Yes" if detail_value else "No"
                    lines.append(f"- **{formatted_key}:** {bool_text}")
                else:
                    lines.append(f"- **{formatted_key}:** {detail_value}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Footer
    lines.extend([
        "## Actions Required",
        "",
    ])
    
    # List failed checks
    failed_checks = [r["name"] for r in results.values() if not r.get("success", False)]
    if failed_checks:
        lines.append("The following components require attention:")
        lines.append("")
        for check in failed_checks:
            lines.append(f"- {check}")
        lines.append("")
    else:
        lines.append("✅ No actions required - all systems operational")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## About This Report",
        "",
        "This report is automatically generated by `scripts/generate_service_status_report.py`.",
        "It performs comprehensive health checks across all system components and continues",
        "checking even if individual components fail, ensuring complete visibility into",
        "system status.",
        "",
        "To regenerate this report:",
        "```bash",
        "python scripts/generate_service_status_report.py",
        "```",
        "",
        f"*Last updated: {timestamp}*",
    ])
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    print("=" * 70)
    print("Service Status Report Generator")
    print("=" * 70)
    print()
    
    # Run all checks
    checker = ServiceStatusChecker()
    results = checker.run_all_checks()
    
    # Generate markdown report
    print("📝 Generating markdown report...")
    report = generate_markdown_report(results)
    
    # Write to file
    output_file = Path(__file__).parent.parent / "service_status_report.md"
    output_file.write_text(report, encoding="utf-8")
    
    print(f"✅ Report written to: {output_file}")
    print()
    
    # Also output JSON for programmatic use
    json_file = Path(__file__).parent.parent / "service_status_report.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"✅ JSON data written to: {json_file}")
    print()
    
    # Print summary
    total = len(results)
    passed = sum(1 for r in results.values() if r.get("success", False))
    
    print("=" * 70)
    print(f"Summary: {passed}/{total} checks passed")
    print("=" * 70)
    
    # Always exit 0 - script is non-blocking and should not fail CI/CD
    sys.exit(0)


if __name__ == "__main__":
    main()
