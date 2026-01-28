#!/usr/bin/env python3
"""Store performance metrics for trend analysis."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def store_metrics(metrics_file: str, storage_dir: str = "metrics/history") -> None:
    """Store metrics with timestamp for historical tracking.

    Args:
        metrics_file: Path to metrics JSON file
        storage_dir: Directory to store historical metrics
    """
    if not Path(metrics_file).exists():
        print(f"❌ Error: Metrics file not found: {metrics_file}")
        sys.exit(1)

    with open(metrics_file) as f:
        metrics = json.load(f)

    # Create storage directory
    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = storage_path / f"metrics_{timestamp}.json"

    # Add storage metadata
    metrics["stored_at"] = datetime.utcnow().isoformat()
    metrics["source_file"] = metrics_file

    # Save metrics
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Metrics stored to {output_file}")

    # Also update the latest metrics file
    latest_file = storage_path / "latest.json"
    with open(latest_file, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Updated latest metrics: {latest_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Store performance metrics")
    parser.add_argument(
        "metrics_file",
        help="Performance metrics JSON file",
    )
    parser.add_argument(
        "--storage-dir",
        default="metrics/history",
        help="Directory to store historical metrics",
    )
    args = parser.parse_args()

    store_metrics(args.metrics_file, args.storage_dir)


if __name__ == "__main__":
    main()
