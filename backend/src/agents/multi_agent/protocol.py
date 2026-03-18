"""Compatibility wrapper for canonical src.agents.multi_agent imports."""

from importlib import import_module

_MODULE = import_module("backend.python.multi_agent.protocol")
__all__ = getattr(_MODULE, "__all__", [name for name in dir(_MODULE) if not name.startswith("_")])

globals().update({name: getattr(_MODULE, name) for name in __all__})
