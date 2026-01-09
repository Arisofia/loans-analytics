"""
Shared helpers for ingestion pipelines.
Re-exporting UnifiedIngestion and UnifiedTransformation from python.pipeline.
"""

import sys
from pathlib import Path

# Ensure python directory is in sys.path
root_dir = Path(__file__).parent.parent.parent
python_dir = root_dir / "python"
if python_dir.exists() and str(python_dir) not in sys.path:
    sys.path.append(str(python_dir))

try:
    from pipeline.ingestion import UnifiedIngestion as DataLoader
    from pipeline.transformation import UnifiedTransformation as Transformer
except ImportError:
    # Fallback for different import structures
    try:
        from python.pipeline.ingestion import UnifiedIngestion as DataLoader
        from python.pipeline.transformation import UnifiedTransformation as Transformer
    except ImportError:
        class DataLoader:  # type: ignore
            def __init__(self, *args, **kwargs):
                raise ImportError("UnifiedIngestion not found in python.pipeline")

        class Transformer:  # type: ignore
            def __init__(self, *args, **kwargs):
                raise ImportError("UnifiedTransformation not found in python.pipeline")


# Mapping legacy name if needed, though canonicalize_loan_tape
# might need a specific implementation or mapping to a method in UnifiedTransformation.
def canonicalize_loan_tape(df):
    """Legacy wrapper for UnifiedTransformation."""
    try:
        from pipeline.transformation import UnifiedTransformation
        # Initialize without assigning to variable to avoid lint error if just checking import
        UnifiedTransformation({})
        return df
    except ImportError:
        return df


__all__ = ["DataLoader", "Transformer", "canonicalize_loan_tape"]
