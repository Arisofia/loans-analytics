import pytest
import requests
from pipeline.ingestion import UnifiedIngestion


@pytest.fixture
def base_config():
    return {
        "pipeline": {"phases": {"ingestion": {"validation": {"strict": False}}}},
        "cascade": {
            "http": {
                "retry": {"max_retries": 2, "backoff_seconds": 0},
                "rate_limit": {"max_requests_per_minute": 60},
                "circuit_breaker": {"failure_threshold": 1, "reset_seconds": 60},
            }
        },
    }


class FlakyResponse:
    def __init__(self, sequence):
        self._seq = sequence

    def __call__(self, *args, **kwargs):
        result = self._seq.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class DummyResponse:
    def __init__(self, content: bytes, status_code: int = 200, headers=None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/json"}

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise requests.HTTPError(f"status: {self.status_code}")


def test_ingest_http_retries_and_success(monkeypatch, base_config):
    # First call raises Timeout, second returns JSON payload
    json_content = b'[{"loan_id":"l1", "total_receivable_usd": 100.0}]'
    seq = [requests.Timeout("timeout"), DummyResponse(json_content)]
    monkeypatch.setattr("requests.get", FlakyResponse(seq))

    ui = UnifiedIngestion(base_config)
    res = ui.ingest_http("http://example.com/data")
    assert res.df.shape[0] == 1
    # Expect an http_retry event logged
    assert any(e.get("event") == "http_retry" for e in ui.audit_log)


def test_circuit_breaker_opens_after_failure(monkeypatch, base_config):
    # requests.get always raises an error
    monkeypatch.setattr(
        "requests.get", lambda *a, **k: (_ for _ in ()).throw(requests.ConnectionError("down"))
    )

    cfg = base_config.copy()
    # Set failure threshold to 1 to open circuit quickly
    cfg["cascade"]["http"]["circuit_breaker"]["failure_threshold"] = 1
    ui = UnifiedIngestion(cfg)

    with pytest.raises(Exception):
        ui.ingest_http("http://example.com/data")

    # Now circuit breaker should prevent the next attempt
    with pytest.raises(RuntimeError):
        ui.ingest_http("http://example.com/data")


def test_rate_limiter_wait_called(monkeypatch, base_config):
    json_content = b'[{"loan_id":"l1", "total_receivable_usd": 100.0}]'
    monkeypatch.setattr("requests.get", lambda *a, **k: DummyResponse(json_content))

    ui = UnifiedIngestion(base_config)
    called = {"wait": False}

    def fake_wait():
        called["wait"] = True

    ui.rate_limiter.wait = fake_wait
    ui.ingest_http("http://example.com/data")
    assert called["wait"] is True


def test_ingest_looker_missing_columns_raises(monkeypatch, base_config, tmp_path):
    ui = UnifiedIngestion(base_config)
    # create a CSV missing PAR and DPD columns
    p = tmp_path / "loans.csv"
    p.write_text("loan_id,outstanding_balance\n1,100\n")

    with pytest.raises(ValueError):
        ui.ingest_looker(p)
