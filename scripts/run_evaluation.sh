#!/bin/bash
set -e

# Install dependencies
python3 -m pip install --upgrade pip

# Install from the analytics app requirements
python3 -m pip install -r apps/analytics/requirements.txt

# Run evaluation scripts
python scripts/evaluation/check_thresholds.py --metrics-file reports/evaluation-metrics.json --config config/evaluation-thresholds.yml --output threshold-results.json

python scripts/evaluation/generate_visualizations.py --metrics-file reports/evaluation-metrics.json --output-dir reports/visualizations/
