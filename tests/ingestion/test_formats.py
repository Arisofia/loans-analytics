import pandas as pd
import pytest
from src.pipeline.data_ingestion import UnifiedIngestion


@pytest.fixture
def base_config():
    return {"pipeline": {"phases": {"ingestion": {"validation": {"strict": False}}}}}


def test_ingest_file_xlsx(tmp_path, base_config):
    ui = UnifiedIngestion(base_config)
    df = pd.DataFrame(
        {
            "loan_id": ["a1", "a2"],
            "total_receivable_usd": [10.0, 20.0],
            "total_eligible_usd": [10.0, 20.0],
            "discounted_balance_usd": [10.0, 20.0],
        }
    )
    xlsx_path = tmp_path / "test.xlsx"
    df.to_excel(xlsx_path, index=False)

    res = ui.ingest_file(xlsx_path)
    assert res.df.shape[0] == 2


def test_ingest_file_json(tmp_path, base_config):
    ui = UnifiedIngestion(base_config)
    df = pd.DataFrame(
        {
            "loan_id": ["a1", "a2"],
            "total_receivable_usd": [10.0, 20.0],
            "total_eligible_usd": [10.0, 20.0],
            "discounted_balance_usd": [10.0, 20.0],
        }
    )
    json_path = tmp_path / "test.json"
    df.to_json(json_path)

    res = ui.ingest_file(json_path)
    assert res.df.shape[0] == 2


def test_ingest_file_strict_raises(tmp_path):
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
    p = tmp_path / "data.csv"
    p.write_text("loan_id\n1\n")

    with pytest.raises(ValueError):
        ui.ingest_file(p)
