import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.path_utils import validate_path

def store_metrics(metrics_file: str, storage_dir: str='metrics/history') -> None:
    validated_metrics_file = validate_path(metrics_file, base_dir='metrics', must_exist=True)
    validated_storage_dir = validate_path(storage_dir, base_dir='metrics', allow_write=True)
    with open(str(validated_metrics_file)) as f:
        metrics = json.load(f)
    validated_storage_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    output_filename = f'metrics_{timestamp}.json'
    output_file = validated_storage_dir / output_filename
    validated_output = validate_path(str(output_file), base_dir='metrics', allow_write=True)
    metrics['stored_at'] = datetime.utcnow().isoformat()
    metrics['source_file'] = str(validated_metrics_file)
    with open(str(validated_output), 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f'✅ Metrics stored to {validated_output}')
    latest_filename = 'latest.json'
    latest_file = validated_storage_dir / latest_filename
    validated_latest = validate_path(str(latest_file), base_dir='metrics', allow_write=True)
    with open(str(validated_latest), 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f'✅ Updated latest metrics: {validated_latest}')

def main():
    parser = argparse.ArgumentParser(description='Store performance metrics')
    parser.add_argument('metrics_file', help='Performance metrics JSON file')
    parser.add_argument('--storage-dir', default='metrics/history', help='Directory to store historical metrics')
    args = parser.parse_args()
    store_metrics(args.metrics_file, args.storage_dir)
if __name__ == '__main__':
    main()
