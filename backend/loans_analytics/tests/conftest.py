import sys
from decimal import ROUND_HALF_UP, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# Ensure SSOT rounding guard is satisfied before importing API/KPI modules in tests.
getcontext().rounding = ROUND_HALF_UP
