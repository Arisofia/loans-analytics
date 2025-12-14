"""
CLI for running loan KPI analytics on CSV inputs
with optional Azure export.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.analytics.src.azure_blob_exporter import AzureBlobKPIExporter  # noqa: E402
from apps.analytics.src.enterprise_analytics_engine import LoanAnalyticsEngine  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for KPI and risk alert computation."""
    parser = argparse.ArgumentParser(
        description=(
            "Compute loan KPIs and optional risk alerts from a CSV dataset."
        )
    )
    parser.add_argument(
        "--data",
        required=True,
        help=(
            "Path to a CSV containing loan_amount, appraised_value, "
            "borrower_income, monthly_debt, loan_status, interest_rate, "
            "principal_balance."
        ),
    )
    parser.add_argument(
        "--output",
        help="Optional path to write KPI results as JSON.",
    )
    parser.add_argument(
        "--export-blob",
        dest="container_name",
        help="Optional Azure Blob container name for uploading KPIs.",
    )
    parser.add_argument(
        "--blob-name",
        help="Optional Azure Blob name for the exported KPI JSON.",
    )
    parser.add_argument(
        "--include-risk-alerts",
        dest="include_risk_alerts",
        action="store_true",
        help="Compute and include risk alerts.",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for KPI analytics CLI."""
    args = parse_args()

    try:
        engine = LoanAnalyticsEngine(args.data)
        kpi_results = engine.compute_kpis()

        if args.output:
            with open(args.output, "w") as f:
                json.dump(kpi_results, f, indent=2, default=str)
            print(f"✅ KPI results written to {args.output}")

        if args.include_risk_alerts:
            risk_alerts = engine.compute_risk_alerts()
            if args.output:
                alert_path = args.output.replace(".json", "_alerts.json")
                with open(alert_path, "w") as f:
                    json.dump(risk_alerts, f, indent=2, default=str)
                print(f"✅ Risk alerts written to {alert_path}")

        if args.container_name:
            exporter = AzureBlobKPIExporter(args.container_name)
            blob_name = args.blob_name or "kpi_results.json"
            exporter.upload_kpi_results(kpi_results, blob_name)
            print(f"✅ KPI results exported to Azure Blob: {blob_name}")

        print("\n📊 KPI Analytics Complete")

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
