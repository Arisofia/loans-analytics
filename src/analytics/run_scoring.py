"""
CLI for running loan KPI analytics on CSV inputs
with optional Azure export.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

import pandas as pd

REPO_ROOT = tuple(Path(__file__).resolve().parents)[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analytics.azure_blob_exporter import \
    AzureBlobKPIExporter  # noqa: E402
from src.analytics.enterprise_analytics_engine import \
    LoanAnalyticsEngine  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for KPI and risk alert computation."""
    parser = argparse.ArgumentParser(
        description=("Compute loan KPIs and optional risk alerts from a CSV dataset.")
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
        "--connection-string",
        help="Azure Blob Storage connection string.",
    )
    parser.add_argument(
        "--account-url",
        help="Azure Blob Storage account URL.",
    )
    parser.add_argument(
        "--include-risk-alerts",
        dest="include_risk_alerts",
        action="store_true",
        help="Compute and include risk alerts.",
    )
    parser.add_argument(
        "--ltv-threshold",
        type=float,
        default=90.0,
        help="LTV threshold for risk alerts (default: 90.0).",
    )
    parser.add_argument(
        "--dti-threshold",
        type=float,
        default=40.0,
        help="DTI threshold for risk alerts (default: 40.0).",
    )
    return parser.parse_args()


def load_portfolio(file_path: Path) -> pd.DataFrame:
    """Load portfolio data from a CSV file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    # Expand user path just in case
    return pd.read_csv(file_path.expanduser())


def summarize_results(metrics: Dict[str, float], risk_alert_count: int) -> None:
    """Print a summary of the analysis results."""
    print("\n--- Analysis Summary ---")
    for key, value in metrics.items():
        formatted_key = key.replace("_", " ").title()
        if isinstance(value, float):
            print(f"{formatted_key}: {value:.2f}")
        else:
            print(f"{formatted_key}: {value}")
    print(f"Risk alerts flagged: {risk_alert_count}")
    print("------------------------\n")


def main() -> None:
    """Main entry point for KPI analytics CLI."""
    args = parse_args()

    try:
        df = load_portfolio(Path(args.data))
        engine = LoanAnalyticsEngine(df)
        kpi_results = engine.run_full_analysis()

        if args.output:
            with open(args.output, "w") as f:
                json.dump(kpi_results, f, indent=2, default=str)
            print(f"✅ KPI results written to {args.output}")

        risk_alert_count = 0
        if args.include_risk_alerts:
            risk_alerts = engine.risk_alerts(
                ltv_threshold=args.ltv_threshold, dti_threshold=args.dti_threshold
            )
            risk_alert_count = len(risk_alerts)
            if args.output:
                alert_path = args.output.replace(".json", "_alerts.json")
                # Convert DataFrame to dict for JSON serialization
                alerts_dict = risk_alerts.to_dict(orient="records")
                with open(alert_path, "w") as f:
                    json.dump(alerts_dict, f, indent=2, default=str)
                print(f"✅ Risk alerts written to {alert_path}")

        if args.container_name:
            exporter = AzureBlobKPIExporter(
                container_name=args.container_name,
                connection_string=args.connection_string,
                account_url=args.account_url,
            )
            blob_name = args.blob_name or "kpi_results.json"
            exporter.upload_metrics(kpi_results, blob_name)
            print(f"✅ KPI results exported to Azure Blob: {blob_name}")

        summarize_results(kpi_results, risk_alert_count)
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
