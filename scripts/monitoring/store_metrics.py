#!/usr/bin/env python3
"""Store performance metrics for trend analysis."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.path_utils import validate_path


def store_metrics(metrics_file: str, storage_dir: str = "metrics/history") -> None:
    """Store metrics with timestamp for historical tracking.

    Args:
        metrics_file: Path to metrics JSON file
        storage_dir: Directory to store historical metrics
    """
    # Validate input paths for security (CWE-22: Path Traversal)
    # nosemgrep: python.lang.security.injection.path-traversal
    validated_metrics_file = validate_path(metrics_file, base_dir="metrics", must_exist=True)
    # nosemgrep: python.lang.security.injection.path-traversal
    validated_storage_dir = validate_path(storage_dir, base_dir="metrics", allow_write=True)

    with open(str(validated_metrics_file)) as f:  # snyk:skip=f6be9097-832a-4935-8f4b-0567b21a7239
        metrics = json.load(f)

    # Create storage directory
    validated_storage_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_filename = f"metrics_{timestamp}.json"
    output_file = validated_storage_dir / output_filename

    # Validate output file path
    # nosemgrep: python.lang.security.injection.path-traversal
    validated_output = validate_path(str(output_file), base_dir="metrics", allow_write=True)

    # Add storage metadata
    metrics["stored_at"] = datetime.utcnow().isoformat()
    metrics["source_file"] = str(validated_metrics_file)

    # Save metrics
    with open(str(validated_output), "w") as f:
        json.dump(metrics, f, indent=2)  # snyk:skip=f1572f76-d7bf-4f4c-bd0b-2473222e8af5

    print(f"✅ Metrics stored to {validated_output}")

    # Also update the latest metrics file
    latest_filename = "latest.json"
    latest_file = validated_storage_dir / latest_filename

    # Validate latest file path
    # nosemgrep: python.lang.security.injection.path-traversal
    validated_latest = validate_path(str(latest_file), base_dir="metrics", allow_write=True)
    with open(str(validated_latest), "w") as f:  # snyk:skip=1c5826a5-deb8-4f04-9cc0-2df7fcc280d4
        json.dump(metrics, f, indent=2)

    print(f"✅ Updated latest metrics: {validated_latest}")


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
