"""Test script for UsageTracker."""

from pathlib import Path

from python.utils.usage_tracker import UsageTracker


def test_usage_tracker():
    tracker = UsageTracker("data/usage_metrics/test_usage.jsonl")

    # Track some events
    tracker.track("dashboard", "view", user_id="user_123")
    tracker.track("kpi_pipeline", "run", user_id="admin", status="success")
    tracker.track("report", "export", user_id="user_123", format="pdf")

    print(f"Tracked {len(tracker.get_events())} events.")

    # Export to different formats
    exports_dir = Path("data/usage_metrics/exports")
    tracker.export(exports_dir / "usage.json", export_format="json")
    tracker.export(exports_dir / "usage.csv", export_format="csv")
    tracker.export(exports_dir / "usage.parquet", export_format="parquet")

    print(f"Exported to {exports_dir}")

    # Check if files exist
    if not (exports_dir / "usage.json").exists():
        raise RuntimeError("Expected usage.json export file does not exist")
    if not (exports_dir / "usage.csv").exists():
        raise RuntimeError("Expected usage.csv export file does not exist")
    if not (exports_dir / "usage.parquet").exists():
        raise RuntimeError("Expected usage.parquet export file does not exist")

    print("Test passed!")


if __name__ == "__main__":
    test_usage_tracker()
