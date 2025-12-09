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

from apps.analytics.src.azure_blob_exporter import AzureBlobKPIExporter
from apps.analytics.src.enterprise_analytics_engine import LoanAnalyticsEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute loan KPIs and optional risk alerts from a CSV dataset."
    )
    parser.add_argument(
        "--data",
        required=True,
        help=(
            "Path to a CSV containing loan_amount, appraised_value, borrower_income, "
            "monthly_debt, loan_status, interest_rate, principal_balance."
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
        dest="blob_name",
        help="Optional blob name for Azure export (default uses a timestamp).",
    )
    parser.add_argument(
        "--connection-string",
        dest="connection_string",
        default=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
        help="Azure Storage connection string (falls back to AZURE_STORAGE_CONNECTION_STRING).",
    )
    parser.add_argument(
        "--account-url",
        dest="account_url",
        default=os.getenv("AZURE_STORAGE_ACCOUNT_URL"),
        help="Azure Storage account URL (falls back to AZURE_STORAGE_ACCOUNT_URL).",
    )
    parser.add_argument(
        "--ltv-threshold",
        type=float,
        default=90.0,
        help="LTV threshold for flagging risk alerts (default: 90).",
    )
    parser.add_argument(
        "--dti-threshold",
        type=float,
        default=40.0,
        help="DTI threshold for flagging risk alerts (default: 40).",
    )
    return parser.parse_args()


def load_portfolio(path: Path) -> pd.DataFrame:
    """
    Load a loan portfolio from a CSV file into a pandas DataFrame.

    Args:
        path (Path): The file path to the CSV data file.

    Returns:
        pd.DataFrame: DataFrame containing the portfolio data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)


def summarize_results(metrics: Dict[str, Any], alerts_rows: int) -> None:
    """
    Display a summary of loan portfolio KPIs and risk alerts in a professional, human-readable format.

    Args:
        metrics (Dict[str, Any]): Dictionary of KPI metric names and their values. Numeric values are formatted to two decimal places; string values are displayed as-is.
        alerts_rows (int): The number of risk alerts flagged in the portfolio analysis.

    Returns:
        None. Prints the KPI summary and risk alert count to standard output.
    """
    print("--- Loan Portfolio KPI Summary ---")
    for key, value in metrics.items():
        label = key.replace("_", " ").title()
        print(f"{label}: {value:.2f}" if isinstance(value, (int, float)) else f"{label}: {value}")
    print(f"Risk alerts flagged: {alerts_rows}")
    print("----------------------------------")


def main() -> None:
    args = parse_args()
    data_path = Path(args.data).expanduser().resolve()

    portfolio = load_portfolio(data_path)
    engine = LoanAnalyticsEngine(portfolio)

    metrics = engine.run_full_analysis()
    alerts = engine.risk_alerts(ltv_threshold=args.ltv_threshold, dti_threshold=args.dti_threshold)

    output_payload: Dict[str, Any] = {
        "data_file": str(data_path),
        "metrics": metrics,
        "risk_alert_count": int(len(alerts)),
        "sample_alerts": alerts.head(5).to_dict(orient="records"),
    }

    summarize_results(metrics, len(alerts))

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.write_text(json.dumps(output_payload, indent=2))
        print(f"Saved KPI payload to {output_path}")

    if args.container_name:
        if not args.connection_string and not args.account_url:
            raise SystemExit(
                "Azure export requested but no connection string or account URL was provided. "
                "Pass --connection-string/--account-url or set AZURE_STORAGE_CONNECTION_STRING / AZURE_STORAGE_ACCOUNT_URL."
            )
        exporter = AzureBlobKPIExporter(
            container_name=args.container_name,
            connection_string=args.connection_string,
            account_url=args.account_url,
        )
        blob_path = engine.export_kpis_to_blob(exporter, blob_name=args.blob_name)
        print(f"Uploaded KPI payload to blob: {blob_path}")


if __name__ == "__main__":
    main()
