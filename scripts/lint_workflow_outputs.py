#!/usr/bin/env python3
"""
Workflow Linter: Checks for unquoted $GITHUB_OUTPUT and malformed echo output blocks in .github/workflows/*.yml
"""
import re
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
    exit(1)
