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

    events = tracker.get_events()
    assert len(events) == 1
    assert event.feature_name == "test_feature"
    assert event.action == "test_action"
    assert event.user_id == "user_1"
    assert event.metadata == {"key": "value"}

    # Verify persistence
    storage_exists = temp_storage.exists()
    assert storage_exists
    with open(temp_storage, "r") as f:
        stored_data = json.loads(f.read())
        feature_name = stored_data["feature_name"]
        assert feature_name == "test_feature"


def test_persistence_load(temp_storage):
    """Test loading events from persistent storage."""
    # First tracker to save events
    tracker1 = UsageTracker(storage_path=temp_storage)
    tracker1.track("feature1", "action1")
    tracker1.track("feature2", "action2")

    # Second tracker to load them
    tracker2 = UsageTracker(storage_path=temp_storage)
    events = tracker2.get_events()

    events_count = len(events)
    assert events_count == 2
    feature_name_0 = events[0].feature_name
    assert feature_name_0 == "feature1"
    feature_name_1 = events[1].feature_name
    assert feature_name_1 == "feature2"


def test_export_json(temp_storage, tmp_path):
    """Test exporting to JSON."""
    tracker = UsageTracker(storage_path=temp_storage)
    tracker.track("feature", "action")

    export_path = tmp_path / "export.json"
    tracker.export(export_path, export_format="json")

    json_path_exists = export_path.exists()
    assert json_path_exists
    with open(export_path, "r") as f:
        data = json.load(f)
        data_len = len(data)
        assert data_len == 1
        feature_name_json = data[0]["feature_name"]
        assert feature_name_json == "feature"


def test_export_csv(temp_storage, tmp_path):
    """Test exporting to CSV."""
    tracker = UsageTracker(storage_path=temp_storage)
    tracker.track("feature", "action")

    export_path = tmp_path / "export.csv"
    tracker.export(export_path, export_format="csv")

    csv_path_exists = export_path.exists()
    assert csv_path_exists
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
