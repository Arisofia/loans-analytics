import sys
import os
from pathlib import Path

# Ensure repository modules can be imported when tests run from the repo root.
ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "apps"):
    sys.path.insert(0, str(path))

# Change working directory to repository root so relative file paths work
os.chdir(ROOT)
