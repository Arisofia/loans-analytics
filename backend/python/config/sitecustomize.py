# Ensure repository root is on sys.path as early as possible
import sys
from pathlib import Path

# Repo root is 3 levels up from backend/python/config/sitecustomize.py
ROOT = Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
