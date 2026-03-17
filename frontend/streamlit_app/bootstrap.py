"""Bootstrap module to ensure repo imports resolve in Streamlit."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
for _p in (ROOT_DIR / "backend", ROOT_DIR / "frontend", ROOT_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
