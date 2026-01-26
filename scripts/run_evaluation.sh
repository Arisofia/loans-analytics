#!/bin/bash
set -e

# Configuration (environment-aware)
REPORTS_DIR="${REPORTS_DIR:-reports}"
CONFIG_DIR="${CONFIG_DIR:-config}"

# Ensure reports directory exists
mkdir -p "$REPORTS_DIR/visualizations"

# Install dependencies
python3 -m pip install --upgrade pip

# Install from the analytics app requirements
python3 -m pip install -r apps/analytics/requirements.txt

# Run evaluation scripts
python3 scripts/evaluation/check_thresholds.py \
    --metrics-file "$REPORTS_DIR/evaluation-metrics.json" \
    --config "$CONFIG_DIR/evaluation-thresholds.yml" \
    --output threshold-results.json

python3 scripts/evaluation/generate_visualizations.py \
    --metrics-file "$REPORTS_DIR/evaluation-metrics.json" \
    --output-dir "$REPORTS_DIR/visualizations/"
