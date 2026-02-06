"""Tests for UsageTracker utility."""

import json

import pandas as pd
import pytest

from python.utils.usage_tracker import UsageTracker


@pytest.fixture
def temp_storage(tmp_path):
    """Fixture for temporary storage path."""
    return tmp_path / "usage_events.jsonl"


def test_track_event(temp_storage):
    """Test tracking a single event."""
    tracker = UsageTracker(storage_path=temp_storage)
    event = tracker.track("test_feature", "test_action", user_id="user_1", key="value")

    assert len(tracker.get_events()) == 1
    assert event.feature_name == "test_feature"
    assert event.action == "test_action"
    assert event.user_id == "user_1"
    assert event.metadata == {"key": "value"}

    # Verify persistence
    assert temp_storage.exists()
    with open(temp_storage, "r") as f:
        stored_data = json.loads(f.read())
        assert stored_data["feature_name"] == "test_feature"


def test_persistence_load(temp_storage):
    """Test loading events from persistent storage."""
    # First tracker to save events
    tracker1 = UsageTracker(storage_path=temp_storage)
    tracker1.track("feature1", "action1")
    tracker1.track("feature2", "action2")

    # Second tracker to load them
    tracker2 = UsageTracker(storage_path=temp_storage)
    events = tracker2.get_events()

    assert len(events) == 2
    assert events[0].feature_name == "feature1"
    assert events[1].feature_name == "feature2"


def test_export_json(temp_storage, tmp_path):
    """Test exporting to JSON."""
    tracker = UsageTracker(storage_path=temp_storage)
    tracker.track("feature", "action")

    export_path = tmp_path / "export.json"
    tracker.export(export_path, export_format="json")

    assert export_path.exists()
    with open(export_path, "r") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["feature_name"] == "feature"


def test_export_csv(temp_storage, tmp_path):
    """Test exporting to CSV."""
    tracker = UsageTracker(storage_path=temp_storage)
    tracker.track("feature", "action")

    export_path = tmp_path / "export.csv"
    tracker.export(export_path, export_format="csv")

    assert export_path.exists()
    df = pd.read_csv(export_path)
    assert len(df) == 1
    assert df.iloc[0]["feature_name"] == "feature"


def test_export_parquet(temp_storage, tmp_path):
    """Test exporting to Parquet."""
    tracker = UsageTracker(storage_path=temp_storage)
    tracker.track("feature", "action")

    export_path = tmp_path / "export.parquet"
    tracker.export(export_path, export_format="parquet")

    assert export_path.exists()
    df = pd.read_parquet(export_path)
    assert len(df) == 1
    assert df.iloc[0]["feature_name"] == "feature"
