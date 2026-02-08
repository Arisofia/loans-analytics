#!/usr/bin/env python3
"""
Complete Stack Validation Script

Validates that all components of the Abaco Loans Analytics stack are working correctly.
Runs checks on:
- Data files
- Scripts
- Dashboard components
- Agent analysis
- Docker configuration

Usage:
    python scripts/validate_complete_stack.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_file_exists(file_path: Path, description: str) -> bool:
    """Check if a file exists."""
    if file_path.exists():
        print(f"  ✅ {description}: {file_path.name}")
        return True
    else:
        print(f"  ❌ {description} NOT FOUND: {file_path}")
        return False


def validate_data_files() -> dict[str, bool]:
    """Validate that all required data files exist."""
    print_section("📊 DATA FILES")

    results = {}

    # Seed data
    results["seed_data"] = check_file_exists(
        ROOT_DIR / "data" / "raw" / "spanish_loans_seed.csv",
        "Spanish Loans Seed Data (850 records)",
    )

    results["sample_data"] = check_file_exists(
        ROOT_DIR / "data" / "raw" / "spanish_loans_sample.csv", "Sample Data (50 records)"
    )

    # Check if seed data has correct format
    if results["seed_data"]:
        try:
            import csv

            seed_file = ROOT_DIR / "data" / "raw" / "spanish_loans_seed.csv"
            with open(seed_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                required = [
                    "loan_id",
                    "borrower_name",
                    "borrower_email",
                    "borrower_id_number",
                    "principal_amount",
                    "interest_rate",
                    "term_months",
                    "origination_date",
                    "current_status",
                    "payment_history_json",
                    "risk_score",
                    "region",
                ]
                missing = [col for col in required if col not in headers]
                if missing:
                    print(f"  ⚠️  Missing columns: {', '.join(missing)}")
                    results["seed_data_valid"] = False
                else:
                    print(f"  ✅ All required columns present ({len(required)} columns)")
                    results["seed_data_valid"] = True
        except Exception as e:
            print(f"  ⚠️  Error reading seed data: {str(e)}")
            results["seed_data_valid"] = False

    return results


def validate_scripts() -> dict[str, bool]:
    """Validate that all required scripts exist."""
    print_section("🔧 SCRIPTS")

    results = {}

    results["seed_script"] = check_file_exists(
        ROOT_DIR / "scripts" / "seed_spanish_loans.py", "Seed Data Generator"
    )

    results["analysis_script"] = check_file_exists(
        ROOT_DIR / "scripts" / "run_daily_agent_analysis.py", "Daily Agent Analysis"
    )

    results["deploy_script"] = check_file_exists(
        ROOT_DIR / "scripts" / "deploy_stack.sh", "Stack Deployment Script"
    )

    # Check if scripts are executable
    deploy_script = ROOT_DIR / "scripts" / "deploy_stack.sh"
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
        ROOT_DIR / "DEPLOYMENT_GUIDE.md", "Deployment Guide"
    )

    results["operations_guide"] = check_file_exists(
        ROOT_DIR / "docs" / "USER_OPERATIONS_GUIDE.md", "User Operations Guide"
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
                results["has_analyses"] = False

            if "portfolio_metrics" in data:
                metrics = data["portfolio_metrics"]
                print("  ✅ Portfolio metrics calculated")
                print(f"     - Total loans: {metrics.get('total_loans', 'N/A')}")
                print(f"     - Portfolio value: €{metrics.get('total_portfolio', 0):,.2f}")
                results["has_metrics"] = True
            else:
                print("  ⚠️  No portfolio metrics in results")
                results["has_metrics"] = False

        except Exception as e:
            print(f"  ⚠️  Error reading analysis: {str(e)}")
            results["has_analyses"] = False
            results["has_metrics"] = False
    else:
        print("  ⚠️  No analysis results found")
        cmd = (
            "python scripts/run_daily_agent_analysis.py" " --input data/raw/spanish_loans_seed.csv"
        )
        print(f"     Run: {cmd}")
        results["has_analyses"] = False
        results["has_metrics"] = False

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
    print("  2. Run: bash scripts/deploy_stack.sh")
    print("  3. Access dashboard: http://localhost:8501")
    print("  4. Load sample data from sidebar")
    print("  5. Explore visualizations and metrics")
    print("\n" + "=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
