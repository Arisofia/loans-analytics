import pytest
import pandas as pd
from src.ingest import DataLoader, Transformer, canonicalize_loan_tape

def test_dataloader_import():
    assert DataLoader is not None

def test_transformer_import():
    assert Transformer is not None

def test_canonicalize_loan_tape():
    df = pd.DataFrame({"test": [1, 2, 3]})
    result = canonicalize_loan_tape(df)
    assert result.equals(df)
