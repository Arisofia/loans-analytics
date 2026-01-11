import json

import pandas as pd
import pytest
from pipeline.ingestion import UnifiedIngestion


@pytest.fixture
def base_config():
    return {"pipeline": {"phases": {"ingestion": {"validation": {"strict": False}}}}}


def test_looker_par_balances_to_loan_tape(base_config):
    ui = UnifiedIngestion(base_config)
    df = pd.DataFrame(
        {
            "reporting_date": ["2024-01-01", "2024-01-01"],
            "outstanding_balance_usd": [100.0, 50.0],
            "par_7_balance_usd": [20.0, 10.0],
            "par_30_balance_usd": [10.0, 5.0],
            "par_60_balance_usd": [5.0, 2.0],
            "par_90_balance_usd": [2.0, 1.0],
        }
    )
    cash_by_date = {"2024-01-01": 15.0}
    out = ui._looker_par_balances_to_loan_tape(df, cash_by_date)
    assert "measurement_date" in out.columns
    assert out["total_receivable_usd"].sum() == pytest.approx(150.0)
    # locate the row by the measurement date for robustness
    row = out.loc[out["measurement_date"] == "2024-01-01"].iloc[0]
    assert row["cash_available_usd"] == pytest.approx(15.0)


def test_looker_dpd_to_loan_tape(base_config):
    ui = UnifiedIngestion(base_config)
    df = pd.DataFrame(
        {"dpd": [0, 5, 10, 40, 75, 120], "outstanding_balance": [10, 10, 10, 10, 10, 10]}
    )
    out = ui._looker_dpd_to_loan_tape(df, {})
    # dpd buckets
    assert out["dpd_0_7_usd"].sum() >= 10.0
    assert out["dpd_7_30_usd"].sum() >= 10.0
    assert out["dpd_30_60_usd"].sum() >= 10.0
    assert out["dpd_60_90_usd"].sum() >= 10.0 or out["dpd_90_plus_usd"].sum() >= 10.0


class DummyResponse:
    def __init__(
        self, content: bytes, content_type: str = "application/json", encoding: str = "utf-8"
    ):
        self.content = content
        self.headers = {"Content-Type": content_type}
        self.encoding = encoding

    def raise_for_status(self):
        return None


def test_ingest_http_json_and_csv(monkeypatch, base_config):
    ui = UnifiedIngestion(base_config)

    # JSON response
    json_content = b'[{"loan_id":"l1", "total_receivable_usd": 100.0, "total_eligible_usd": 100.0, "discounted_balance_usd": 100.0}]'

    def mock_get_json(url, headers=None, timeout=None):
        return DummyResponse(json_content, content_type="application/json")

    monkeypatch.setattr("requests.get", mock_get_json)

    res = ui.ingest_http("http://example.com/data")
    assert res.df.shape[0] == 1

    # CSV response
    csv_content = b"loan_id,total_receivable_usd,total_eligible_usd,discounted_balance_usd\nl1,50.0,50.0,50.0\n"

    def mock_get_csv(url, headers=None, timeout=None):
        return DummyResponse(csv_content, content_type="text/csv")

    monkeypatch.setattr("requests.get", mock_get_csv)

    res2 = ui.ingest_http("http://example.com/data.csv")
    assert res2.df.shape[0] == 1


def test_ingest_file_xlsx_and_json_lines(tmp_path, base_config):
    ui = UnifiedIngestion(base_config)

    # XLSX
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

    # JSON lines
    lines = [json.dumps(row.to_dict()) for _, row in df.iterrows()]
    jsonl_path = tmp_path / "test.json"
    jsonl_path.write_text("\n".join(lines))

    res2 = ui.ingest_file(jsonl_path)
    assert res2.df.shape[0] == 2
