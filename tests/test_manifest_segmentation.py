import pandas as pd

from src.kpis.segmentation_summary import calculate_segmentation_summary
from src.pipeline.output import UnifiedOutput


def test_manifest_contains_segmentation_data(tmp_path):
    # Prepare sample data and calculate segmentation KPI
    data = {
        'Customer ID': [1, 2, 3, 4],
        'Client Segment': ['A', 'A', 'B', 'B'],
        'Outstanding Amount': [1000, 2000, 1500, 2500],
        'Approved Amount': [1100, 2100, 1600, 2600],
        'Origination Date': ['2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01'],
    }
    df = pd.DataFrame(data)

    value, ctx = calculate_segmentation_summary(df)

    metrics = {
        'SegmentationSummary': {
            'current_value': value,
            'status': 'ok',
            **ctx,
        }
    }

    metadata = {'calculation': {'note': 'test'}}
    run_ids = {'pipeline': 'seg_test_run_1'}

    # Pipeline outputs config with local dirs under tmp_path
    outputs_cfg = {
        'storage': {'local_dir': str(tmp_path / 'metrics'), 'manifest_dir': str(tmp_path / 'runs')},
        'formats': ['json'],
        'azure': {'enabled': False},
    }

    config = {'pipeline': {'phases': {'outputs': outputs_cfg}}}

    uo = UnifiedOutput(config, run_id=run_ids['pipeline'])

    result = uo.persist(df, metrics, metadata, run_ids)

    manifest = result.manifest

    assert 'metrics' in manifest
    assert 'SegmentationSummary' in manifest['metrics']
    assert 'segmentation_data' in manifest['metrics']['SegmentationSummary']
    # segmentation_data should be a list of dicts (summary records)
    assert isinstance(manifest['metrics']['SegmentationSummary']['segmentation_data'], list)
    assert len(manifest['metrics']['SegmentationSummary']['segmentation_data']) >= 1
