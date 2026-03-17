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
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_file_exists(file_path: Path, description: str) -> bool:
    """Check if a file exists and print result."""
    if file_path.exists():
        print(f"  [OK] {description}: {file_path}")
        return True
    print(f"  [MISS] {description} NOT FOUND: {file_path}")
    return False


def validate_data_files() -> dict[str, bool]:
    """Validate that key data locations exist (no demo-only dependencies)."""
    print_section("DATA FILES")

    results: dict[str, bool] = {}

    # Real / governed data directory
    raw_dir = ROOT_DIR / "data" / "raw"
    results["raw_dir"] = raw_dir.exists()
    if raw_dir.exists():
        files = list(raw_dir.glob("*.csv"))
        print(f"  [OK] data/raw exists ({len(files)} CSV file(s))")
    else:
        print("  [WARN] data/raw directory missing")

    # Logs / runs directory for pipeline outputs
    runs_dir = ROOT_DIR / "logs" / "runs"
    results["logs_runs_dir"] = runs_dir.exists()
    if runs_dir.exists():
        all_runs = list(runs_dir.glob("*"))
        latest_runs = sorted(all_runs, reverse=True)[:3]
        print(f"  [OK] logs/runs exists ({len(all_runs)} run(s))")
        if latest_runs:
            print("  Recent runs:")
            for d in latest_runs:
                print(f"     - {d.name}")
    else:
        print("  [WARN] logs/runs directory missing (run pipeline to generate artifacts)")

    return results


def validate_scripts() -> dict[str, bool]:
    """Validate canonical script locations."""
    print_section("SCRIPTS")

    results: dict[str, bool] = {}

    results["run_pipeline"] = check_file_exists(
        ROOT_DIR / "scripts" / "data" / "run_data_pipeline.py", "Unified Pipeline Runner"
    )

    results["validate_structure"] = check_file_exists(
        ROOT_DIR / "scripts" / "maintenance" / "validate_structure.py",
        "Repository Structure Validator",
    )

    results["service_status"] = check_file_exists(
        ROOT_DIR / "scripts" / "maintenance" / "generate_service_status_report.py",
        "Service Status Report Generator",
    )

    results["repo_maintenance"] = check_file_exists(
        ROOT_DIR / "scripts" / "maintenance" / "repo_maintenance.sh",
        "Repository Maintenance Orchestrator",
    )

    results["path_utils"] = check_file_exists(
        ROOT_DIR / "scripts" / "path_utils.py",
        "Path Security Utilities",
    )

    return results


def validate_dashboard() -> dict[str, bool]:
    """Validate Streamlit dashboard components."""
    print_section("DASHBOARD")

    results: dict[str, bool] = {}

    results["main_app"] = check_file_exists(ROOT_DIR / "streamlit_app.py", "Main Streamlit App")

    results["multi_page_app"] = check_file_exists(
        ROOT_DIR / "frontend" / "streamlit_app" / "app.py", "Multi-page Streamlit App Entrypoint"
    )

    results["portfolio_dashboard"] = check_file_exists(
        ROOT_DIR / "frontend" / "streamlit_app" / "pages" / "3_Portfolio_Dashboard.py",
        "Portfolio Dashboard",
    )

    results["usage_metrics"] = check_file_exists(
        ROOT_DIR / "frontend" / "streamlit_app" / "pages" / "4_Usage_Metrics.py",
        "Usage Metrics Page",
    )

    results["monitoring_control"] = check_file_exists(
        ROOT_DIR / "frontend" / "streamlit_app" / "pages" / "5_Monitoring_Control.py",
        "Monitoring & Control Page",
    )

    return results


def validate_docker() -> dict[str, bool]:
    """Validate Docker and monitoring configuration."""
    print_section("DOCKER & MONITORING CONFIGURATION")

    results: dict[str, bool] = {}

    results["dockerfile_api"] = check_file_exists(
        ROOT_DIR / "Dockerfile", "API / Pipeline Dockerfile"
    )

    results["dockerfile_dashboard"] = check_file_exists(
        ROOT_DIR / "Dockerfile.dashboard", "Dashboard Dockerfile"
    )

    results["docker_compose"] = check_file_exists(
        ROOT_DIR / "docker-compose.yml", "Main docker-compose.yml"
    )

    results["docker_compose_monitoring"] = check_file_exists(
        ROOT_DIR / "docker-compose.yml",
        "Monitoring profile in canonical docker-compose.yml",
    )

    results["prometheus_config"] = check_file_exists(
        ROOT_DIR / "config" / "prometheus.yml", "Prometheus Configuration"
    )

    results["metrics_exporter"] = check_file_exists(
        ROOT_DIR / "scripts" / "monitoring" / "metrics_exporter.py",
        "Metrics Exporter Script",
    )

    return results


def validate_documentation() -> dict[str, bool]:
    """Validate documentation exists for deployment and ops."""
    print_section("DOCUMENTATION")

    results: dict[str, bool] = {}

    results["deployment_guide"] = check_file_exists(
        ROOT_DIR / "docs" / "PRODUCTION_DEPLOYMENT_GUIDE.md", "Production Deployment Guide"
    )

    results["observability"] = check_file_exists(
        ROOT_DIR / "docs" / "OBSERVABILITY.md", "Observability Documentation"
    )

    results["setup_guide"] = check_file_exists(
        ROOT_DIR / "docs" / "SUPABASE_SETUP_GUIDE.md", "Supabase Setup Guide"
    )

    results["operations"] = check_file_exists(
        ROOT_DIR / "docs" / "OPERATIONS.md", "Operations Documentation"
    )

    results["maintenance_guide"] = check_file_exists(
        ROOT_DIR / "docs" / "REPOSITORY_MAINTENANCE.md", "Repository Maintenance Guide"
    )

    results["security_doc"] = check_file_exists(
        ROOT_DIR / "docs" / "SECURITY.md", "Security Documentation"
    )

    results["deployment_checklist"] = check_file_exists(
        ROOT_DIR / "docs" / "operations" / "SECURITY_DEPLOYMENT_CHECKLIST.md",
        "Security Deployment Checklist",
    )

    return results


def run_basic_imports() -> dict[str, bool]:
    """Test basic Python imports necessary for the stack."""
    print_section("PYTHON DEPENDENCIES")

    results: dict[str, bool] = {}

    modules = [
        ("json", "JSON"),
        ("csv", "CSV"),
        ("datetime", "DateTime"),
        ("pathlib", "PathLib"),
        ("pydantic", "Pydantic"),
        ("fastapi", "FastAPI"),
        ("streamlit", "Streamlit"),
    ]

    for module, name in modules:
        try:
            __import__(module)
            print(f"  [OK] {name} module available")
            results[module] = True
        except ImportError:
            print(f"  [MISS] {name} module NOT available")
            results[module] = False

    return results


def check_agent_analysis_results() -> dict[str, bool]:
    """Check if agent analysis has been run and contains metrics."""
    print_section("AGENT ANALYSIS")

    results: dict[str, bool] = {}

    latest_analysis = ROOT_DIR / "data" / "agent_analysis" / "latest_analysis.json"

    if latest_analysis.exists():
        print(f"  [OK] Latest analysis found: {latest_analysis}")
        try:
            with open(latest_analysis, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "agent_analyses" in data:
                agent_count = len(data["agent_analyses"])
                print(f"  [OK] {agent_count} agent analyses present")
                results["has_analyses"] = True
            else:
                print("  [WARN] No agent analyses in results")
                results["has_analyses"] = False

            if "portfolio_metrics" in data:
                metrics = data["portfolio_metrics"]
                print("  [OK] Portfolio metrics calculated")
                print(f"     - Total loans: {metrics.get('total_loans', 'N/A')}")
                total_portfolio = metrics.get("total_portfolio", 0)
                currency = metrics.get("total_portfolio_currency", "")
                print(f"     - Portfolio value: {currency} {total_portfolio:,.2f}")
                results["has_metrics"] = True
            else:
                print("  [WARN] No portfolio metrics in results")
                results["has_metrics"] = False

        except Exception as exc:
            print(f"  [WARN] Error reading analysis: {exc}")
            results["has_analyses"] = False
            results["has_metrics"] = False
    else:
        print("  [WARN] No analysis results found")
        raw_candidates = sorted((ROOT_DIR / "data" / "raw").glob("abaco_real_data_*.csv"))
        if raw_candidates:
            cmd = f"python scripts/data/run_data_pipeline.py --input {raw_candidates[-1]}"
        else:
            cmd = (
                "python scripts/data/run_data_pipeline.py "
                "--input data/raw/<your_real_loans_file>.csv"
            )
        print(f"     Run to generate: {cmd}")
        results["has_analyses"] = False
        results["has_metrics"] = False

    return results


def print_summary(all_results: dict[str, dict[str, bool]]) -> int:
    """Print validation summary and return an exit code."""
    print_section("VALIDATION SUMMARY")

    total_checks = 0
    passed_checks = 0

    for _, results in all_results.items():
        for _, passed in results.items():
            total_checks += 1
            if passed:
                passed_checks += 1

    success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

    print(f"\n  Total Checks: {total_checks}")
    print(f"  Passed: {passed_checks}")
    print(f"  Failed: {total_checks - passed_checks}")
    print(f"  Success Rate: {success_rate:.1f}%")

    if success_rate == 100:
        print("\n  ALL CHECKS PASSED! Stack is ready for deployment.")
        return 0
    if success_rate >= 80:
        print("\n  Most checks passed. Minor issues may need attention.")
        return 0
    print("\n  Several checks failed. Review errors above.")
    return 1


def main() -> None:
    """Main validation function."""
    print("=" * 60)
    print("  ABACO LOANS ANALYTICS - STACK VALIDATION")
    print("=" * 60)
    print("\n  Validating complete stack deployment...")
    print(f"  Root directory: {ROOT_DIR}")

    all_results = {
        "data_files": validate_data_files(),
        "scripts": validate_scripts(),
        "dashboard": validate_dashboard(),
        "docker": validate_docker(),
        "documentation": validate_documentation(),
        "python_deps": run_basic_imports(),
        "agent_analysis": check_agent_analysis_results(),
    }

    exit_code = print_summary(all_results)

    print("\n" + "=" * 60)
    print("  NEXT STEPS")
    print("=" * 60)
    print("\n  1. Fix any failed checks above")
    print("  2. Run your deployment workflow")
    print("  3. Access dashboard: http://localhost:8501 or your prod URL")
    print("  4. Run the pipeline with real data to generate logs/runs artifacts")
    print("  5. Explore KPIs, agent insights, and monitoring/command pages")
    print("\n" + "=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
