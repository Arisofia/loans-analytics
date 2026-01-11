"""Compatibility shim for historical `src.abaco_pipeline` package.

This package provides a minimal `__version__` attribute used by tests and
legacy imports. It intentionally keeps a tiny surface area to avoid
reintroducing historical application logic here.
"""

__all__ = ["__version__"]

# Historical package version used in coverage artifacts and tests
__version__ = "0.1.0"
