"""Multi-agent package — first live slice + legacy compatibility."""

from .orchestrator import DecisionOrchestrator

try:
    from .orchestrator import MultiAgentOrchestrator  # legacy re-export
except ImportError:
    pass

__all__ = ["DecisionOrchestrator", "MultiAgentOrchestrator"]
