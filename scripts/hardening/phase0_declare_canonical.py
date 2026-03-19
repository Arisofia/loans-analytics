#!/usr/bin/env python3
"""
phase0_declare_canonical.py
Declares the ONE canonical production path and produces a complete
file-by-file inventory with KEEP_ACTIVE / KEEP_TEST_ONLY / REFACTOR_ACTIVE /
DELETE_NOW / QUARANTINE_TEMP classification.

Run from repo root:
    python3 scripts/hardening/phase0_declare_canonical.py [--json]

Output: reports/PRODUCTION_INVENTORY.md  +  reports/PRODUCTION_INVENTORY.json
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal


CANONICAL = {
    "ingestion": "backend/src/pipeline/ingestion.py",
    "transformation": "backend/src/pipeline/transformation.py",
    "calculation": "backend/python/kpis/formula/",
    "kpi_engine": "backend/python/kpis/engine.py",
    "orchestration": "backend/src/pipeline/orchestrator.py",
    "output": "backend/src/pipeline/output.py",
    "deployment": "Dockerfile + docker-compose.yml",
    "observability": "backend/src/agents/monitoring/",
    "api": "backend/python/apps/analytics/api/main.py",
    "frontend": "frontend/streamlit_app/app.py",
    "tests": "backend/python/tests/",
    "config": "pyproject.toml + config/pipeline.yml",
    "database": "db/migrations/ (timestamp-prefixed only)",
    "dpd_canonical": "backend/python/kpis/dpd_calculator.py",
    "fuzzy_canonical": "backend/src/zero_cost/fuzzy_matcher.py",
    "agents": "backend/python/multi_agent/",
}

Status = Literal[
    "KEEP_ACTIVE",
    "KEEP_TEST_ONLY",
    "REFACTOR_ACTIVE",
    "DELETE_NOW",
    "QUARANTINE_TEMP",
]


RULES: list[tuple[str, Status, str, str | None]] = [
    ("credentials/google-service-account.json", "DELETE_NOW", "Secret committed to VCS - CRITICAL", "Rotate & use env var"),
    (".env.local", "DELETE_NOW", "Live credentials in VCS", "GitHub Secret / .env.example"),
    ("*.log", "DELETE_NOW", "Runtime log output", None),
    (".mypy_full.out", "DELETE_NOW", "Runtime linter output", None),
    ("htmlcov/**", "DELETE_NOW", "Coverage build artefact", None),
    ("htmlcov", "DELETE_NOW", "Coverage build artefact", None),
    ("exports/strategic_report_*.json", "DELETE_NOW", "Runtime artefact committed", "Artifact store"),
    ("exports/strategic_report_*.md", "DELETE_NOW", "Runtime artefact committed", "Artifact store"),
    ("exports/complete_kpi_dashboard.json", "DELETE_NOW", "Runtime artefact", "Artifact store"),
    ("full_test_run.log", "DELETE_NOW", "Runtime output", None),
    ("pytest_full.log", "DELETE_NOW", "Runtime output", None),
    ("pytest_check.log", "DELETE_NOW", "Runtime output", None),
    ("pytest_results.log", "DELETE_NOW", "Runtime output", None),
    ("mypy_check.log", "DELETE_NOW", "Runtime output", None),
    ("ruff_check.log", "DELETE_NOW", "Runtime output", None),
    ("target_test.log", "DELETE_NOW", "Runtime output", None),
    ("reports/INSTITUTIONAL_AUDIT_ATTESTATION_*.md", "DELETE_NOW", "Self-signed certification - not an audit", None),
    ("READY_TO_DEPLOY.md", "DELETE_NOW", "Self-certification contradicted by committed secrets", None),
    ("MERGE_CONFLICT_RESOLUTION.md", "DELETE_NOW", "Applied conflict residue - no runtime value", None),
    ("SETUP_STATUS.md", "DELETE_NOW", "Transient operational state, not documentation", None),
    ("docs/process-output-2026-02-26.md", "DELETE_NOW", "Process residue document", None),
    ("reports/check1_*", "DELETE_NOW", "Internal audit parity artefact", None),
    ("reports/check2_*", "DELETE_NOW", "Internal audit parity artefact", None),
    ("reports/check3_*", "DELETE_NOW", "Internal audit parity artefact", None),
    ("reports/check4_*", "DELETE_NOW", "Internal audit parity artefact", None),
    ("reports/scope_*", "DELETE_NOW", "Internal audit parity artefact", None),
    ("reports/manifest_*", "DELETE_NOW", "Internal audit parity artefact", None),
    ("reports/full_file_read_*", "DELETE_NOW", "Internal audit artefact", None),
    ("reports/WORKSTREAM_*.md", "DELETE_NOW", "Internal audit artefact", None),
    ("reports/REMEDIATION_EXECUTION_PLAN_*.md", "DELETE_NOW", "Internal audit artefact", None),
    ("reports/build_manifest_v2.py", "DELETE_NOW", "Audit helper script, no production role", None),
    ("backend/src/agents/multi_agent/cli.py", "DELETE_NOW", "Duplicate of backend/python/multi_agent/cli.py", "backend/python/multi_agent/cli.py"),
    ("backend/src/agents/multi_agent/config_historical.py", "DELETE_NOW", "Duplicate of backend/python/multi_agent/config_historical.py", "backend/python/multi_agent/config_historical.py"),
    ("backend/src/agents/multi_agent/guardrails.py", "DELETE_NOW", "Duplicate of backend/python/multi_agent/guardrails.py", "backend/python/multi_agent/guardrails.py"),
    ("backend/src/agents/multi_agent/orchestrator.py", "DELETE_NOW", "Duplicate of backend/python/multi_agent/orchestrator.py", "backend/python/multi_agent/orchestrator.py"),
    ("backend/src/agents/multi_agent/protocol.py", "DELETE_NOW", "Duplicate of backend/python/multi_agent/protocol.py", "backend/python/multi_agent/protocol.py"),
    ("backend/src/zero_cost/dpd_calculator.py", "DELETE_NOW", "Duplicate DPD - canonical is backend/python/kpis/dpd_calculator.py", "backend/python/kpis/dpd_calculator.py"),
    ("frontend/streamlit_app/fuzzy_table_mapping.py", "DELETE_NOW", "Frontend shadow of backend fuzzy matcher - shadow risk engine", "backend/src/zero_cost/fuzzy_matcher.py"),
    ("backend/python/kpis/formula_engine.py", "QUARANTINE_TEMP", "Incomplete refactor: formula/ sub-package supersedes this. Verify all callers use formula/ then delete.", "backend/python/kpis/formula/"),
    ("data/abaco/collateral.csv", "DELETE_NOW", "Duplicate of data/raw/collateral.csv", "data/raw/collateral.csv"),
    ("data/abaco/customer_data.csv", "DELETE_NOW", "Duplicate of data/raw/customer_data.csv", "data/raw/customer_data.csv"),
    ("data/abaco/loan_data.csv", "DELETE_NOW", "Duplicate of data/raw/loan_data.csv", "data/raw/loan_data.csv"),
    ("data/abaco/payment_schedule.csv", "DELETE_NOW", "Duplicate of data/raw/payment_schedule.csv", "data/raw/payment_schedule.csv"),
    ("data/abaco/real_payment.csv", "DELETE_NOW", "Duplicate of data/raw/real_payment.csv", "data/raw/real_payment.csv"),
    ("backend/data-processor/processor.py", "QUARANTINE_TEMP", "Fifth ETL path - not proven to be in active production pipeline", "backend/src/pipeline/"),
    ("backend/python/ingest", "DELETE_NOW", "Empty directory - no implementation", None),
    ("tests", "DELETE_NOW", "Empty root test directory", "backend/python/tests/"),
    ("infra", "DELETE_NOW", "Empty directory - no content", None),
    ("tools", "DELETE_NOW", "Empty directory - no content", None),
    ("db/sql", "DELETE_NOW", "Empty directory - no content", None),
    ("frontend/data/agent_outputs", "DELETE_NOW", "Empty runtime output directory", None),
    (".zencoder", "DELETE_NOW", "Orphaned tool config, empty", None),
    (".zenflow", "DELETE_NOW", "Orphaned tool config, empty", None),
    ("backend/python/testing", "DELETE_NOW", "Empty testing stub - only __init__.py", None),
    ("host.json", "QUARANTINE_TEMP", "Azure Functions config - no function.json found. Delete if Azure not active.", "Supabase / Docker deployment"),
    ("azure.yaml", "QUARANTINE_TEMP", "Azure deployment config - no function.json found.", "Supabase / Docker deployment"),
    ("GRAFANA_DATA_SETUP.md", "DELETE_NOW", "Duplicate of docs/GRAFANA_SETUP_GUIDE.md", "docs/GRAFANA_SETUP_GUIDE.md"),
    ("GRAFANA_LIVE.md", "DELETE_NOW", "Duplicate of docs/GRAFANA_SETUP_GUIDE.md", "docs/GRAFANA_SETUP_GUIDE.md"),
    ("backend/python/OPERATIONS.md", "DELETE_NOW", "Duplicate of docs/OPERATIONS.md", "docs/OPERATIONS.md"),
    ("backend/python/MIGRATION.md", "DELETE_NOW", "Duplicate of docs/migration.md", "docs/migration.md"),
    ("backend/python/multi_agent/DATABASE_DESIGNER_USAGE.md", "DELETE_NOW", "Usage guide for agent, not production doc", None),
    ("docs/runbook.md", "DELETE_NOW", "Superseded by docs/runbooks/ directory", "docs/runbooks/"),
    (".github/PULL_REQUEST_TEMPLATE/fix-frontend-eslint-warnings.md", "DELETE_NOW", "Single-issue PR template, not canonical", None),
    (".github/pull_request_template.md", "QUARANTINE_TEMP", "Two PR templates exist - verify which is canonical", ".github/PULL_REQUEST_TEMPLATE/pull_request_template.md"),
    (".github/workflows/.workflow-management.md", "DELETE_NOW", "Internal meta-doc, not a workflow", None),
    (".github/agents/MICROSERVICE_DESIGNER_USAGE.md", "DELETE_NOW", "Usage guide, no production role", None),
    (".github/agents/TESTCRAFTPRO_QUICKSTART.md", "DELETE_NOW", "Usage guide, no production role", None),
    (".github/agents/TESTCRAFTPRO_USAGE.md", "DELETE_NOW", "Usage guide, no production role", None),
    (".github/agents/USAGE_EXAMPLES.md", "DELETE_NOW", "Usage examples, no production role", None),
    ("backend/python/multi_agent/test_*.py", "REFACTOR_ACTIVE", "Tests co-located in source module - must move to backend/python/tests/", "backend/python/tests/"),
    ("backend/python/patches/", "QUARANTINE_TEMP", "Applied patches - if already merged into codebase, delete; else move to docs/", "docs/patches/ or delete if applied"),
    ("data/raw/client_manual_overrides.csv", "QUARANTINE_TEMP", "Manual overrides belong in DB with audit trail, not flat CSV in source", "Database override table"),
    ("pytest.ini", "DELETE_NOW", "Duplicate pytest config - merge into pyproject.toml [tool.pytest.ini_options]", "pyproject.toml"),
    ("**/__pycache__", "DELETE_NOW", "Compiled Python cache", None),
    (".pytest_cache", "DELETE_NOW", "Test runner cache", None),
    (".mypy_cache", "DELETE_NOW", "Type checker cache", None),
    (".ruff_cache", "DELETE_NOW", "Linter cache", None),
    (".hypothesis", "DELETE_NOW", "Property test database", None),
    ("htmlcov", "DELETE_NOW", "Coverage HTML output", None),
    ("data/samples/", "QUARANTINE_TEMP", "Sample CSV in production data path - move to tests/fixtures/ or delete", "backend/python/tests/fixtures/"),
    ("backend/python/apps/analytics/api/main.py", "KEEP_ACTIVE", "FastAPI entry point", None),
    ("backend/python/apps/analytics/api/service.py", "KEEP_ACTIVE", "API service layer", None),
    ("backend/python/apps/analytics/api/models.py", "KEEP_ACTIVE", "API request/response models", None),
    ("backend/python/apps/analytics/api/monitoring_models.py", "KEEP_ACTIVE", "Monitoring models", None),
    ("backend/python/apps/analytics/api/monitoring_service.py", "KEEP_ACTIVE", "Monitoring service", None),
    ("backend/python/kpis/engine.py", "KEEP_ACTIVE", "Canonical KPI engine", None),
    ("backend/python/kpis/formula/", "KEEP_ACTIVE", "Canonical formula sub-package", None),
    ("backend/python/kpis/dpd_calculator.py", "KEEP_ACTIVE", "Canonical DPD - single source", None),
    ("backend/python/kpis/ssot_asset_quality.py", "KEEP_ACTIVE", "SSOT asset quality", None),
    ("backend/python/kpis/collection_rate.py", "KEEP_ACTIVE", "Collection rate KPI", None),
    ("backend/python/kpis/health_score.py", "KEEP_ACTIVE", "Portfolio health score", None),
    ("backend/python/kpis/ltv.py", "KEEP_ACTIVE", "LTV calculation", None),
    ("backend/python/kpis/lending_kpis.py", "KEEP_ACTIVE", "Lending KPIs", None),
    ("backend/python/kpis/portfolio_analytics.py", "KEEP_ACTIVE", "Portfolio analytics", None),
    ("backend/python/kpis/advanced_risk.py", "KEEP_ACTIVE", "Advanced risk metrics", None),
    ("backend/python/kpis/unit_economics.py", "KEEP_ACTIVE", "Unit economics", None),
    ("backend/python/kpis/graph_analytics.py", "KEEP_ACTIVE", "Graph analytics", None),
    ("backend/python/kpis/strategic_modules.py", "KEEP_ACTIVE", "Strategic KPI modules", None),
    ("backend/python/kpis/strategic_reporting.py", "KEEP_ACTIVE", "Strategic reporting", None),
    ("backend/python/kpis/catalog_processor.py", "KEEP_ACTIVE", "KPI catalog processing", None),
    ("backend/python/multi_agent/orchestrator.py", "KEEP_ACTIVE", "Canonical agent orchestrator", None),
    ("backend/python/multi_agent/agents.py", "KEEP_ACTIVE", "Agent definitions", None),
    ("backend/python/multi_agent/base_agent.py", "KEEP_ACTIVE", "Base agent", None),
    ("backend/python/multi_agent/agent_factory.py", "KEEP_ACTIVE", "Agent factory", None),
    ("backend/python/multi_agent/specialized_agents.py", "KEEP_ACTIVE", "Specialized agents", None),
    ("backend/python/multi_agent/guardrails.py", "KEEP_ACTIVE", "Agent guardrails", None),
    ("backend/python/multi_agent/protocol.py", "KEEP_ACTIVE", "Agent protocol", None),
    ("backend/python/multi_agent/kpi_integration.py", "KEEP_ACTIVE", "KPI-agent integration", None),
    ("backend/python/multi_agent/historical_context.py", "KEEP_ACTIVE", "Historical context", None),
    ("backend/python/multi_agent/historical_backend_supabase.py", "KEEP_ACTIVE", "Supabase backend for history", None),
    ("backend/python/multi_agent/config.py", "KEEP_ACTIVE", "Agent config", None),
    ("backend/python/multi_agent/config_historical.py", "KEEP_ACTIVE", "Historical config", None),
    ("backend/python/multi_agent/tracing.py", "KEEP_ACTIVE", "Agent tracing", None),
    ("backend/python/models/default_risk_model.py", "KEEP_ACTIVE", "Risk model", None),
    ("backend/python/models/kpi_models.py", "KEEP_ACTIVE", "KPI Pydantic models", None),
    ("backend/python/financial_precision.py", "KEEP_ACTIVE", "Decimal precision utils", None),
    ("backend/python/validation.py", "KEEP_ACTIVE", "Input validation", None),
    ("backend/python/schemas.py", "KEEP_ACTIVE", "Shared schemas", None),
    ("backend/python/supabase_pool.py", "KEEP_ACTIVE", "DB connection pool", None),
    ("backend/python/logging_config.py", "KEEP_ACTIVE", "Logging setup", None),
    ("backend/python/time_utils.py", "KEEP_ACTIVE", "Time utilities", None),
    ("backend/src/pipeline/ingestion.py", "KEEP_ACTIVE", "Canonical ingestion", None),
    ("backend/src/pipeline/transformation.py", "KEEP_ACTIVE", "Canonical transformation", None),
    ("backend/src/pipeline/calculation.py", "KEEP_ACTIVE", "Canonical calculation", None),
    ("backend/src/pipeline/output.py", "KEEP_ACTIVE", "Canonical output", None),
    ("backend/src/pipeline/orchestrator.py", "KEEP_ACTIVE", "Pipeline orchestrator", None),
    ("backend/src/pipeline/config.py", "KEEP_ACTIVE", "Pipeline config", None),
    ("backend/src/pipeline/utils.py", "KEEP_ACTIVE", "Pipeline utilities", None),
    ("backend/src/zero_cost/fuzzy_matcher.py", "KEEP_ACTIVE", "Canonical fuzzy matcher", None),
    ("backend/src/zero_cost/xirr.py", "KEEP_ACTIVE", "XIRR calculation", None),
    ("backend/src/zero_cost/loan_tape_loader.py", "KEEP_ACTIVE", "Loan tape loader", None),
    ("backend/src/zero_cost/storage.py", "KEEP_ACTIVE", "Storage abstraction", None),
    ("backend/src/zero_cost/exporter.py", "KEEP_ACTIVE", "Data exporter", None),
    ("backend/src/zero_cost/crosswalk.py", "KEEP_ACTIVE", "Field crosswalk", None),
    ("backend/src/zero_cost/lend_id_mapper.py", "KEEP_ACTIVE", "Loan ID mapper", None),
    ("backend/src/zero_cost/monthly_snapshot.py", "KEEP_ACTIVE", "Monthly snapshot", None),
    ("backend/src/zero_cost/pipeline_router.py", "KEEP_ACTIVE", "Pipeline router", None),
    ("backend/src/zero_cost/control_mora_adapter.py", "KEEP_ACTIVE", "Mora control adapter", None),
    ("backend/src/zero_cost/local_migration_etl.py", "KEEP_ACTIVE", "Local migration ETL", None),
    ("backend/src/agents/monitoring/cost_tracker.py", "KEEP_ACTIVE", "Cost tracking", None),
    ("backend/src/agents/monitoring/performance_tracker.py", "KEEP_ACTIVE", "Performance tracking", None),
    ("backend/src/agents/llm_provider.py", "KEEP_ACTIVE", "LLM provider abstraction", None),
    ("backend/src/infrastructure/google_sheets_adapter.py", "KEEP_ACTIVE", "Sheets connector", None),
    ("backend/src/utils/config_loader.py", "KEEP_ACTIVE", "Config loader", None),
    ("frontend/streamlit_app/app.py", "KEEP_ACTIVE", "Frontend entry point", None),
    ("frontend/streamlit_app/bootstrap.py", "KEEP_ACTIVE", "App bootstrap", None),
    ("frontend/streamlit_app/components/", "KEEP_ACTIVE", "UI components", None),
    ("frontend/streamlit_app/pages/", "KEEP_ACTIVE", "Streamlit pages", None),
    ("frontend/streamlit_app/utils/security.py", "KEEP_ACTIVE", "Frontend security", None),
    ("config/pipeline.yml", "KEEP_ACTIVE", "Pipeline configuration", None),
    ("config/business_parameters.yml", "KEEP_ACTIVE", "Business parameters", None),
    ("config/business_rules.yaml", "KEEP_ACTIVE", "Business rules", None),
    ("config/evaluation-thresholds.yml", "KEEP_ACTIVE", "Evaluation thresholds", None),
    ("config/prometheus.yml", "KEEP_ACTIVE", "Prometheus config", None),
    ("config/alertmanager.yml.template", "KEEP_ACTIVE", "Alertmanager template", None),
    ("db/migrations/", "KEEP_ACTIVE", "Database migrations", None),
    ("Dockerfile", "KEEP_ACTIVE", "Primary container build", None),
    ("Dockerfile.dashboard", "KEEP_ACTIVE", "Dashboard container", None),
    ("Dockerfile.pipeline", "KEEP_ACTIVE", "Pipeline container", None),
    ("docker-compose.yml", "KEEP_ACTIVE", "Primary compose", None),
    ("pyproject.toml", "KEEP_ACTIVE", "Project config (single source)", None),
    ("requirements.txt", "KEEP_ACTIVE", "Dependencies", None),
    ("requirements.lock.txt", "KEEP_ACTIVE", "Locked dependencies", None),
    ("requirements.prod.lock.txt", "KEEP_ACTIVE", "Prod locked dependencies", None),
    (".github/workflows/tests.yml", "KEEP_ACTIVE", "CI test runner", None),
    (".github/workflows/security-scan.yml", "KEEP_ACTIVE", "Security scanning", None),
    (".github/workflows/pr-checks.yml", "KEEP_ACTIVE", "PR quality gates", None),
    (".github/workflows/deploy-free-tier.yml", "KEEP_ACTIVE", "Deployment", None),
    (".github/dependabot.yml", "KEEP_ACTIVE", "Dependency updates", None),
    (".github/codeql-config.yml", "KEEP_ACTIVE", "SAST config", None),
    (".github/CODEOWNERS", "KEEP_ACTIVE", "Code ownership", None),
    ("backend/python/tests/", "KEEP_TEST_ONLY", "Canonical test suite", None),
    ("data/raw/", "KEEP_TEST_ONLY", "Canonical raw data (test fixtures)", None),
]


def classify_path(rel_path: str) -> tuple[Status, str, str | None]:
    import fnmatch

    for pattern, status, reason, replacement in RULES:
        has_glob = any(char in pattern for char in "*?[")
        if fnmatch.fnmatch(rel_path, pattern):
            return status, reason, replacement
        if pattern.endswith("/**") and rel_path.startswith(pattern[:-3]):
            return status, reason, replacement
        if pattern.endswith("/") and rel_path.startswith(pattern):
            return status, reason, replacement
        if not has_glob and rel_path == pattern:
            return status, reason, replacement
    return "KEEP_ACTIVE", "No rule matched - assumed active", None



def _resolve_git_executable() -> str:
    git_in_path = shutil.which("git")
    if git_in_path:
        return git_in_path

    windows_candidate = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Git" / "cmd" / "git.exe"
    if windows_candidate.exists():
        return str(windows_candidate)

    raise FileNotFoundError("Unable to locate git executable. Ensure git is installed or available on PATH.")


def get_all_tracked_files() -> list[str]:
    result = subprocess.run(
        [_resolve_git_executable(), "ls-files"],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        check=True,
    )
    tracked_files = result.stdout.strip().splitlines()
    return [file_path for file_path in tracked_files if Path(file_path).exists()]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    _ = parser.parse_args()

    files = get_all_tracked_files()
    inventory: list[dict[str, str | None]] = []

    counts: dict[Status, int] = {
        "KEEP_ACTIVE": 0,
        "KEEP_TEST_ONLY": 0,
        "REFACTOR_ACTIVE": 0,
        "DELETE_NOW": 0,
        "QUARANTINE_TEMP": 0,
    }

    for file_path in files:
        status, reason, replacement = classify_path(file_path)
        counts[status] += 1
        inventory.append(
            {
                "path": file_path,
                "status": status,
                "reason": reason,
                "replacement": replacement,
            }
        )

    Path("reports").mkdir(exist_ok=True)
    with Path("reports/PRODUCTION_INVENTORY.json").open("w", encoding="utf-8") as file_handle:
        json.dump({"canonical": CANONICAL, "inventory": inventory}, file_handle, indent=2)

    with Path("reports/PRODUCTION_INVENTORY.md").open("w", encoding="utf-8") as file_handle:
        file_handle.write("# Production Inventory Report\n\n")
        file_handle.write("## Canonical System\n\n")
        for key, value in CANONICAL.items():
            file_handle.write(f"- **{key}**: `{value}`\n")
        file_handle.write("\n## Summary\n\n")
        for status, count in counts.items():
            file_handle.write(f"- {status}: **{count}**\n")
        file_handle.write(f"\n**Total tracked files:** {len(files)}\n\n")

        for status in ("DELETE_NOW", "QUARANTINE_TEMP", "REFACTOR_ACTIVE", "KEEP_TEST_ONLY", "KEEP_ACTIVE"):
            items = [item for item in inventory if item["status"] == status]
            if not items:
                continue
            file_handle.write(f"\n## {status} ({len(items)} files)\n\n")
            for item in items:
                replacement = f" -> `{item['replacement']}`" if item["replacement"] else ""
                file_handle.write(f"- `{item['path']}` - {item['reason']}{replacement}\n")

    print("=" * 70)
    print("CANONICAL SYSTEM DECLARED")
    print("=" * 70)
    for key, value in CANONICAL.items():
        print(f"  {key:20s} -> {value}")
    print()
    print("INVENTORY SUMMARY")
    print("-" * 40)
    for status, count in counts.items():
        print(f"  {status:<20s}: {count}")
    print(f"  {'TOTAL':<20s}: {len(files)}")
    print()
    print("DELETE_NOW files:")
    for item in inventory:
        if item["status"] == "DELETE_NOW":
            print(f"  x  {item['path']}")
    print()
    print("Reports written to:")
    print("  reports/PRODUCTION_INVENTORY.md")
    print("  reports/PRODUCTION_INVENTORY.json")


if __name__ == "__main__":
    main()