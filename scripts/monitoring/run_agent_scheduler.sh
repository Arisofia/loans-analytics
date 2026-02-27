#!/usr/bin/env sh
set -eu

while true; do
  echo "Running daily agent analysis..."

  if [ -z "${DAILY_AGENT_INPUT_PATH:-}" ]; then
    echo "DAILY_AGENT_INPUT_PATH is not set. Skipping run to avoid seed/demo data in runtime."
    sleep 86400
    continue
  fi

  if [ ! -f "${DAILY_AGENT_INPUT_PATH}" ]; then
    echo "Input file not found: ${DAILY_AGENT_INPUT_PATH}. Skipping run."
    sleep 86400
    continue
  fi

  python /app/scripts/data/run_data_pipeline.py --input "${DAILY_AGENT_INPUT_PATH}"
  echo "Analysis complete. Sleeping for 24 hours..."
  sleep 86400
done
