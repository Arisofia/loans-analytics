#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-${WEBSITES_PORT:-8501}}"

exec python -m streamlit run streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port "${PORT}" \
  --server.headless true \
  --browser.gatherUsageStats false
