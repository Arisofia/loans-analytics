from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import pandas as pd
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from backend.python.models.default_risk_model import DefaultRiskModel

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train default-risk model (XGBoost)')
    parser.add_argument('--input', type=Path, default=Path('data/samples/abaco_sample_data_20260202.csv'), help='CSV with training rows and status/current_status column')
    parser.add_argument('--output-dir', type=Path, default=Path('models/risk'), help='Directory where model and metadata are written')
    parser.add_argument('--exclude-days-past-due', action='store_true', help='Exclude days_past_due feature for origination-only scoring')
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f'Input dataset not found: {args.input}')
    df = pd.read_csv(args.input, low_memory=False)
    if df.empty:
        raise ValueError('Training dataset is empty')
    model = DefaultRiskModel()
    exclude_features = ['days_past_due'] if args.exclude_days_past_due else None
    metrics = model.train(df, exclude_features=exclude_features)
    model_path = model.save(str(args.output_dir))
    print('Model training complete')
    print(f'model_path: {model_path}')
    print('metrics:')
    print(json.dumps(metrics, indent=2))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
