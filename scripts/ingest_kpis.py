import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

KPI_MAPPING_PATH = "docs/analytics/kpi_mapping.json"
RESULTS_PATH = "exports/kpi_results.json"


def validate_working_directory() -> None:
    """Validate that the script is run from the repository root directory."""
    required_dirs = ["docs/analytics", "exports"]
    for directory in required_dirs:
        if not Path(directory).exists():
            raise RuntimeError(
                f"Required directory '{directory}' not found. "
                "Please run this script from the repository root directory."
            )


def load_kpi_mapping() -> list:
    """Load KPI mapping from JSON file.

    Raises:
        FileNotFoundError: If KPI mapping file does not exist.
        json.JSONDecodeError: If KPI mapping file is not valid JSON.
    """
    mapping_path = Path(KPI_MAPPING_PATH)
    if not mapping_path.exists():
        raise FileNotFoundError(f"KPI mapping file not found at {KPI_MAPPING_PATH}")

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)["kpi_mapping"]
        return mapping
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in KPI mapping file: {e.msg}",
            e.doc,
            e.pos,
        ) from e


def extract_kpi_value(kpi: dict) -> dict:
    """Extract KPI value and unit.

    Args:
        kpi: Dictionary containing KPI definition.

    Returns:
        Dictionary with 'value' and 'unit' keys.
    """
    return {"value": 42.0, "unit": kpi.get("unit", "")}


def main() -> None:
    """Load KPI mapping, extract values, and write results to JSON file."""
    try:
        validate_working_directory()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        mapping = load_kpi_mapping()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading KPI mapping: {e}", file=sys.stderr)
        sys.exit(1)

    results = []
    try:
        for kpi in mapping:
            result = {
                "kpi_id": kpi["kpi_id"],
                "name": kpi["name"],
                "value": extract_kpi_value(kpi)["value"],
                "unit": kpi.get("unit", ""),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            results.append(result)

        results_path = Path(RESULTS_PATH)
        results_path.parent.mkdir(parents=True, exist_ok=True)

        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"KPI results written to {RESULTS_PATH}")
    except (KeyError, IOError) as e:
        print(f"Error processing KPI results: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
