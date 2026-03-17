"""Root conftest.py — keeps pre-restructure import paths working.

After the Clean Architecture directory moves (Phase 1), the packages
``src``, ``python``, and ``streamlit_app`` now live under ``backend/``
and ``frontend/`` respectively.  Adding those two directories to
``sys.path`` lets every existing import statement continue to resolve
without touching individual source files.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(_ROOT / "frontend"))
