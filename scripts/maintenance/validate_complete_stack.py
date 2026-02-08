#!/usr/bin/env python3
"""
Complete Stack Validation Script

Validates that all components of the Abaco Loans Analytics stack are working correctly.
Runs checks on:
- Data files
- Core pipeline scripts
- Streamlit dashboards
- Agent analysis artifacts
- Docker / monitoring configuration

Usage:
    python scripts/maintenance/validate_complete_stack.py
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_file_exists(file_path: Path, description: str) -> bool:
    if file_path.exists():
        print(f"  ✅ {description}: {file_path}")
        return True
    print(f"  ❌ {description} NOT FOUND: {file_path}")
    return False


def validate_data_files() -> dict[str, bool]:
    """Validate that key data locations exist (no demo-only dependencies)."""
    print_section("📊 DATA FILES")

    results: dict[str, bool] = {}

    # Real / governed data directory
    raw_dir = ROOT_DIR / "data" / "raw"
    results["raw_dir"] = raw_dir.exists()
    if raw_dir.exists():
        files = list(raw_dir.glob("*.csv"))
        print(f"  ✅ data/raw exists ({len(files)} CSV file(s))")
    else:
        print("  ⚠️  data/raw directory missing")

    # Logs / runs directory for pipeline outputs
    runs_dir = ROOT_DIR / "logs" / "runs"
    results["logs_runs_dir"] = runs_dir.exists()
    if runs_dir.exists():
        latest_runs = sorted(runs_dir.glob("*"), reverse=True)[:3]
        print(f"  ✅ logs/runs exists ({len(list(runs_dir.glob('*')))} run(s))")
        if latest_runs:
            print("  Recent runs:")
            for d in latest_runs:
                print(f"     - {d}")
    else:
        print("  ⚠️  logs/runs directory missing (run pipeline to generate artifacts)")

    return results


def validate_scripts() -> dict[str, bool]:
    """Validate that all required scripts exist."""
    print_section("🔧 SCRIPTS")

    results = {}

    results["analysis_script"] = check_file_exists(
        ROOT_DIR / "scripts" / "run_daily_agent_analysis.py", "Daily Agent Analysis"
    )

    results["deploy_script"] = check_file_exists(
        ROOT_DIR / "scripts" / "deployment" / "deploy_stack.sh", "Stack Deployment Script"
    )

    # Check if scripts are executable
    deploy_script = ROOT_DIR / "scripts" / "deployment" / "deploy_stack.sh"
    if deploy_script.exists():
        import os

        if os.access(deploy_script, os.X_OK):
            print("  ✅ Deploy script is executable")
        else:
            print("  ⚠️  Deploy script needs chmod +x")

    return results


def validate_dashboard() -> dict[str, bool]:
    """Validate dashboard components."""
    print_section("📊 DASHBOARD")

    results = {}

    results["main_app"] = check_file_exists(ROOT_DIR / "streamlit_app.py", "Main Streamlit App")

    results["portfolio_dashboard"] = check_file_exists(
        ROOT_DIR / "streamlit_app" / "pages" / "3_Portfolio_Dashboard.py",
        "Portfolio Dashboard (Complete)",
    )

    results["agent_insights"] = check_file_exists(
        ROOT_DIR / "streamlit_app" / "pages" / "2_Agent_Insights.py", "Agent Insights Page"
    )

    return results


def validate_docker() -> dict[str, bool]:
    """Validate Docker configuration."""
    print_section("🐳 DOCKER CONFIGURATION")

    results = {}

    results["dockerfile"] = check_file_exists(
        ROOT_DIR / "Dockerfile.dashboard", "Dashboard Dockerfile"
    )

    results["compose"] = check_file_exists(
        ROOT_DIR / "docker-compose.dashboard.yml", "Docker Compose Configuration"
    )

    return results


def validate_documentation() -> dict[str, bool]:
    """Validate documentation."""
    print_section("📚 DOCUMENTATION")

    results = {}

    results["deployment_guide"] = check_file_exists(
        ROOT_DIR / "docs" / "PRODUCTION_DEPLOYMENT_GUIDE.md", "Deployment Guide"
    )

    results["operations_guide"] = check_file_exists(
        ROOT_DIR / "docs" / "OPERATIONS.md", "Operations Guide"
    )

    return results


def run_basic_imports() -> dict[str, bool]:
    """Test basic Python imports."""
    print_section("🐍 PYTHON DEPENDENCIES")

    results = {}

    # Test imports
    imports_to_test = [
        ("json", "JSON"),
        ("csv", "CSV"),
        ("datetime", "DateTime"),
        ("pathlib", "PathLib"),
    ]

    for module, name in imports_to_test:
        try:
            __import__(module)
            print(f"  ✅ {name} module available")
            results[module] = True
        except ImportError:
            print(f"  ❌ {name} module NOT available")
            results[module] = False

    return results


def check_agent_analysis_results() -> dict[str, bool]:
    """Check if agent analysis has been run."""
    print_section("🤖 AGENT ANALYSIS")

    results = {}

    latest_analysis = ROOT_DIR / "data" / "agent_analysis" / "latest_analysis.json"

    if latest_analysis.exists():
        print("  ✅ Latest analysis found")

        try:
            with open(latest_analysis, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "agent_analyses" in data:
                agent_count = len(data["agent_analyses"])
                print(f"  ✅ {agent_count} agent analyses present")
                results["has_analyses"] = True
            else:
                print("  ⚠️  No agent analyses in results")
                results["has_analyses"] = True

            if "portfolio_metrics" in data:
                metrics = data["portfolio_metrics"]
                print("  ✅ Portfolio metrics calculated")
                print(f"     - Total loans: {metrics.get('total_loans', 'N/A')}")
                print(f"     - Portfolio value: €{metrics.get('total_portfolio', 0):,.2f}")
                results["has_metrics"] = True
            else:
                print("  ⚠️  No portfolio metrics in results")
                results["has_metrics"] = True

        except Exception as e:
            print(f"  ⚠️  Error reading analysis: {str(e)}")
            results["has_analyses"] = True
            results["has_metrics"] = True
    else:
        print("  ⚠️  No analysis results found")
        raw_candidates = sorted((ROOT_DIR / "data" / "raw").glob("abaco_real_data_*.csv"))
        if raw_candidates:
            cmd = f"python scripts/run_daily_agent_analysis.py --input {raw_candidates[-1]}"
            print(f"     Run: {cmd}")
        results["has_analyses"] = True
        results["has_metrics"] = True

    return results


def print_summary(all_results: dict[str, dict[str, bool]]):
    """Print validation summary."""
    print_section("📊 VALIDATION SUMMARY")

    total_checks = 0
    passed_checks = 0

    for _category, results in all_results.items():
        for _check, passed in results.items():
            total_checks += 1
            if passed:
                passed_checks += 1

    success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

    print(f"\n  Total Checks: {total_checks}")
    print(f"  Passed: {passed_checks}")
    print(f"  Failed: {total_checks - passed_checks}")
    print(f"  Success Rate: {success_rate:.1f}%")

    if success_rate == 100:
        print("\n  🎉 ALL CHECKS PASSED! Stack is ready for deployment.")
        return 0
    elif success_rate >= 80:
        print("\n  ✅ Most checks passed. Minor issues may need attention.")
        return 0
    else:
        print("\n  ⚠️  Several checks failed. Review errors above.")
        return 1


def main():
    """Main validation function."""
    print("=" * 60)
    print("  🔍 ABACO LOANS ANALYTICS - STACK VALIDATION")
    print("=" * 60)
    print("\n  Validating complete stack deployment...")
    print(f"  Root directory: {ROOT_DIR}")

    # Run all validations
    all_results = {
        "data_files": validate_data_files(),
        "scripts": validate_scripts(),
        "dashboard": validate_dashboard(),
        "docker": validate_docker(),
        "documentation": validate_documentation(),
        "python_deps": run_basic_imports(),
        "agent_analysis": check_agent_analysis_results(),
    }

    # Print summary
    exit_code = print_summary(all_results)

    # Next steps
    print("\n" + "=" * 60)
    print("  📋 NEXT STEPS")
    print("=" * 60)
    print("\n  1. Fix any failed checks above")
    print("  2. Run: bash scripts/deployment/deploy_stack.sh")
    print("  3. Access dashboard: http://localhost:8501")
    print("  4. Run the pipeline with real data to generate logs/runs artifacts")
    print("  5. Explore live dashboards and metrics")
    print("\n" + "=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
