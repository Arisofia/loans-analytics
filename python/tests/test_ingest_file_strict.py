import pytest
from pipeline.ingestion import UnifiedIngestion


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
    # missing total_receivable_usd to trigger validation
    p.write_text("loan_id\n1\n")

    with pytest.raises(ValueError):
        ui.ingest_file(p)
