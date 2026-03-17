"""Canonical multi-agent namespace under src/agents.

Current implementation re-exports the production modules from
`python.multi_agent` to maintain backward compatibility while
standardizing import paths.
"""

from python.multi_agent import *  # noqa: F401,F403
