#!/usr/bin/env python3
"""Utility to fix extracted run scripts produced by the workflow extractor.
Adds a canonical shebang + strict mode and replaces 'cat file | cmd' with 'cmd < file'.
"""
import sys
import re
from pathlib import Path
p = Path('.github/workflows/extracted_runs')
if not p.exists():
    print('No extracted runs dir found; aborting')
    sys.exit(0)
files = sorted([f for f in p.iterdir() if f.is_file() and f.suffix == '.sh'])
if not files:
    print('No .sh files found; aborting')
    sys.exit(0)
fixed_files = []
for f in files:
    s = f.read_text()
    orig = s
    # Add shebang and strict mode if missing
    if not s.startswith('#!'):
        s = '#!/usr/bin/env bash\nset -euo pipefail\n\n' + s
    # Replace 'cat file | cmd' with 'cmd < file'
    s = re.sub(r"cat\s+([^\s|;]+)\s*\|\s*([^\n]+)", r"\2 < \1", s)
    # Write back if changed
    if s != orig:
        f.write_text(s)
        f.chmod(0o755)
        fixed_files.append(str(f))
print('Fixed files count:', len(fixed_files))
for fn in fixed_files[:50]:
    print('-', fn)
print('Done')
