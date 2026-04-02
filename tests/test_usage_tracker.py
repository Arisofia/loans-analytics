import json
import pandas as pd
import pytest
from backend.loans_analytics.utils.usage_tracker import UsageTracker

@pytest.fixture
def temp_storage(tmp_path):
    return tmp_path / 'usage_events.jsonl'

def test_track_event(temp_storage):
    tracker = UsageTracker(storage_path=temp_storage)
    event = tracker.track('test_feature', 'test_action', user_id='user_1', key='value')
    events = tracker.get_events()
    assert len(events) == 1
    assert event.feature_name == 'test_feature'
    assert event.action == 'test_action'
    assert event.user_id == 'user_1'
    assert event.metadata == {'key': 'value'}
    storage_exists = temp_storage.exists()
    assert storage_exists
    with open(temp_storage, 'r') as f:
        stored_data = json.loads(f.read())
        feature_name = stored_data['feature_name']
        assert feature_name == 'test_feature'

def test_persistence_load(temp_storage):
    tracker1 = UsageTracker(storage_path=temp_storage)
    tracker1.track('feature1', 'action1')
    tracker1.track('feature2', 'action2')
    tracker2 = UsageTracker(storage_path=temp_storage)
    events = tracker2.get_events()
    events_count = len(events)
    assert events_count == 2
    feature_name_0 = events[0].feature_name
    assert feature_name_0 == 'feature1'
    feature_name_1 = events[1].feature_name
    assert feature_name_1 == 'feature2'

def test_export_json(temp_storage, tmp_path):
    tracker = UsageTracker(storage_path=temp_storage)
    tracker.track('feature', 'action')
    export_path = tmp_path / 'export.json'
    tracker.export(export_path, export_format='json')
    json_path_exists = export_path.exists()
    assert json_path_exists
    with open(export_path, 'r') as f:
        data = json.load(f)
        data_len = len(data)
        assert data_len == 1
        feature_name_json = data[0]['feature_name']
        assert feature_name_json == 'feature'

def test_export_csv(temp_storage, tmp_path):
    tracker = UsageTracker(storage_path=temp_storage)
    tracker.track('feature', 'action')
    export_path = tmp_path / 'export.csv'
    tracker.export(export_path, export_format='csv')
    csv_path_exists = export_path.exists()
    assert csv_path_exists
    df = pd.read_csv(export_path)
    df_len = len(df)
    assert df_len == 1
    feature_name_csv = df.iloc[0]['feature_name']
    assert feature_name_csv == 'feature'

def test_export_parquet(temp_storage, tmp_path):
    tracker = UsageTracker(storage_path=temp_storage)
    tracker.track('feature', 'action')
    export_path = tmp_path / 'export.parquet'
    tracker.export(export_path, export_format='parquet')
    parquet_path_exists = export_path.exists()
    assert parquet_path_exists
    df = pd.read_parquet(export_path)
    df_len = len(df)
    assert df_len == 1
    feature_name_parquet = df.iloc[0]['feature_name']
    assert feature_name_parquet == 'feature'
