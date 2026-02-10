#!/usr/bin/env python3
"""Workflow linter for malformed $GITHUB_OUTPUT echo blocks."""

import re
import sys
from pathlib import Path

WORKFLOWS = Path(__file__).parent.parent / ".github" / "workflows"
BAD_PATTERN = re.compile(r'echo\s+"[^"]*>>\s*\$GITHUB_OUTPUT')
GOOD_PATTERN = re.compile(r'echo\s+"[^"]*>>\s*\"\$GITHUB_OUTPUT\"')
failures = []
for wf in WORKFLOWS.glob("*.yml"):
    text = wf.read_text(encoding="utf-8")
    for m in BAD_PATTERN.finditer(text):
        # Only flag if not already quoted
        if not GOOD_PATTERN.search(m.group(0)):
            failures.append((wf.name, m.group(0)))
if failures:
    # Logging removed for production. Use logging module if needed.
    sys.exit(1)
