"""Bootstrap module to ensure repo imports resolve in Streamlit."""

import sys
from pathlib import Path

# Standard monorepo root detection
ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def bootstrap_repo_root():
    """Ensure the project root is in sys.path."""
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
