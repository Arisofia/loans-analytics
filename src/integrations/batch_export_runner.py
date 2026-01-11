"""
Batch export runner for scheduled exports to all platforms.

Orchestrates the complete export pipeline:
1. Load KPI metrics and analytics data
2. Generate summaries and reports
3. Export to all configured platforms
4. Log results and handle errors
"""

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.integrations.unified_output_manager import UnifiedOutputManager

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class BatchExportRunner:
    """Run complete batch exports to all output platforms."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir or "data/exports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.manager = UnifiedOutputManager()
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def load_latest_metrics(self) -> Dict[str, Any]:
        """Load latest KPI metrics from local storage or database.

        Performs runtime validation to ensure the metrics file contains a
        JSON object; malformed or unexpected types are logged and ignored.
        """
        metrics_file = Path("data/metrics") / "latest_metrics.json"

        if metrics_file.exists():
            try:
                with metrics_file.open() as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    logger.error(
                        "Expected dict in %s, got %s; ignoring metrics file",
                        metrics_file,
                        type(data).__name__,
                    )
                    return {}
                return data
            except json.JSONDecodeError as e:
                logger.error("Failed to parse metrics file %s: %s", metrics_file, e)
                return {}
            except OSError as e:
                logger.error("Failed to read metrics file %s: %s", metrics_file, e)
                return {}

        logger.warning("No metrics file found. Using empty metrics.")
        return {}

    def load_raw_data(self) -> Optional[pd.DataFrame]:
        """Load raw analytics data from local storage or database."""
        data_file = Path("data/metrics") / "latest_data.parquet"

        if data_file.exists():
            return pd.read_parquet(data_file)

        logger.warning("No raw data file found.")
        return None

    def generate_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report from metrics."""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metric_count": len(metrics),
            "metrics_overview": {
                name: {
                    "value": data.get("current_value"),
                    "status": data.get("status", "neutral"),
                }
                for name, data in metrics.items()
            },
        }

    def generate_findings(self, metrics: Dict[str, Any]) -> list:
        """Generate key findings from metrics."""
        findings = []

        for kpi_name, metric_data in metrics.items():
            status = metric_data.get("status", "neutral")
            if status == "critical":
                findings.append(f"{kpi_name} is at critical level")
            elif status == "warning":
                findings.append(f"{kpi_name} shows concerning trend")

        if not findings:
            findings.append("All KPIs within acceptable ranges")

        return findings

    def export_kpi_only(self, export_type: str = "kpi-only") -> Dict[str, Any]:
        """Export only KPI metrics."""
        logger.info("Running KPI-only export...")

        metrics = self.load_latest_metrics()

        results = self.manager.export_kpi_metrics_only(
            metrics,
            self.run_id,
            enabled_outputs=["figma", "azure", "supabase", "meta", "notion"],
        )

        self._save_results(results, "kpi_only")
        return results

    def export_dashboard(self, export_type: str = "dashboard") -> Dict[str, Any]:
        """Export dashboard summary data."""
        logger.info("Running dashboard export...")

        metrics = self.load_latest_metrics()
        summary = self.generate_summary(metrics)

        results = self.manager.export_dashboard_data(
            metrics,
            summary,
            self.run_id,
            enabled_outputs=["figma", "azure", "supabase", "meta", "notion"],
        )

        self._save_results(results, "dashboard")
        return results

    def export_full(self, export_type: str = "full") -> Dict[str, Any]:
        """Export complete analytics report."""
        logger.info("Running full export...")

        metrics = self.load_latest_metrics()
        df = self.load_raw_data()
        summary = self.generate_summary(metrics)
        findings = self.generate_findings(metrics)

        if df is None:
            logger.warning("No raw data available for full export. Continuing with metrics only.")
            df = pd.DataFrame()

        results = self.manager.export_complete_report(
            df,
            metrics,
            summary,
            findings,
            self.run_id,
            enabled_outputs=["figma", "azure", "supabase", "meta", "notion"],
        )

        self._save_results(results, "full")
        return results

    def _save_results(self, results: Dict[str, Any], export_type: str) -> None:
        """Save export results to file."""
        results_file = self.output_dir / f"export_results_{export_type}_{self.run_id}.json"

        with results_file.open("w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Export results saved to {results_file}")

    def run(self, export_type: str = "full") -> Dict[str, Any]:
        """Run batch export based on type."""
        logger.info(f"Starting batch export: {export_type}")
        logger.info(f"Run ID: {self.run_id}")

        try:
            if export_type == "kpi-only":
                return self.export_kpi_only()
            elif export_type == "dashboard":
                return self.export_dashboard()
            else:
                return self.export_full()

        except Exception as e:
            logger.error(f"Batch export failed: {e}", exc_info=True)
            return {
                "run_id": self.run_id,
                "success": False,
                "error": str(e),
            }


def main():
    parser = argparse.ArgumentParser(description="Run batch exports to all platforms")
    parser.add_argument(
        "--type",
        choices=["kpi-only", "dashboard", "full"],
        default="full",
        help="Type of export to run",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/exports",
        help="Output directory for export results",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    runner = BatchExportRunner(output_dir=args.output_dir)
    results = runner.run(export_type=args.type)

    print(json.dumps(results, indent=2, default=str))

    return 0 if results.get("success", False) else 1


if __name__ == "__main__":
    exit(main())
