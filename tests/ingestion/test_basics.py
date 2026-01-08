import pandas as pd
import pytest
from src.pipeline.data_ingestion import UnifiedIngestion


@pytest.fixture
def base_config():
    return {"pipeline": {"phases": {"ingestion": {"validation": {"strict": False}}}}}


def test_archive_raw_and_log(tmp_path, base_config):
    ui = UnifiedIngestion(base_config)
    src = tmp_path / "data.csv"
    src.write_text("loan_id,total_receivable_usd\n1,100\n")
    archive_dir = tmp_path / "archive"

    archived = ui._archive_raw(src, archive_dir)
    assert archived is not None
    assert archived.exists()


def test_apply_deduplication_config(base_config):
    cfg = base_config.copy()
    cfg["pipeline"]["phases"]["ingestion"]["deduplication"] = {
        "enabled": True,
        "key_columns": ["loan_id"],
    }
    ui = UnifiedIngestion(cfg)
    df = pd.DataFrame({"loan_id": ["a", "a", "b"], "total_receivable_usd": [10, 10, 20]})
    deduped, removed = ui._apply_deduplication(df)
    assert removed == 1
    assert len(deduped) == 2


def test_validation_strict_raises():
    cfg = {
        "pipeline": {
            "phases": {
                "ingestion": {
                    "validation": {
                        "required_columns": ["loan_id", "total_receivable_usd"],
                        "strict": True,
                    }
                }
            }
        }
    }
    ui = UnifiedIngestion(cfg)
    df = pd.DataFrame({"loan_id": ["a"]})
    with pytest.raises(ValueError):
        ui._validate_dataframe(df)
