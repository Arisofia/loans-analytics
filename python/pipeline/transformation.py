# Compatibility shim: re-export transformation utilities from the canonical implementation in `src`.
# This keeps the `python.pipeline` package working for legacy imports while
# keeping the implementation in `src.pipeline`.

from src.pipeline.data_transformation import (TransformationResult,
                                              UnifiedTransformation)

__all__ = [
    "UnifiedTransformation",
    "TransformationResult",
]
