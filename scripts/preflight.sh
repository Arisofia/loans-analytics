#!/usr/bin/env bash
set -euo pipefail

echo "== Python =="
which python
python --version

echo "== Pip =="
which pip
pip --version

echo "== Key packages =="
python - <<'PY'
import pandas, numpy
print("pandas", pandas.__version__)
print("numpy", numpy.__version__)
PY

echo "== Repo sanity =="
test -f requirements.txt
test -f streamlit_app.py
test -d tests

echo "== Sample data presence =="
test -f data_samples/abaco_portfolio_sample.csv

echo "== Pytest dry run =="
pytest -q --disable-warnings --maxfail=1
