"""Standard root conftest.py for Abaco Monorepo.

Ensures the project root is in sys.path for absolute imports using
backend.* and frontend.* prefixes.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
