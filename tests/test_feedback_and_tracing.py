import json
import logging
from pathlib import Path

import pytest

import src.azure_tracing as azure_tracing
from src.agents.learning import FeedbackStore


def test_feedback_store_skips_malformed_files(tmp_path, caplog):
    storage = tmp_path / "feedback"
    storage.mkdir()

    # valid feedback file
    (storage / "agentA_1_feedback.json").write_text(
        json.dumps({"agent_name": "agentA", "run_id": "1", "score": 0.8})
    )

    # malformed JSON
    (storage / "agentA_2_feedback.json").write_text("{not json")

    # missing score
    (storage / "agentA_3_feedback.json").write_text(
        json.dumps({"agent_name": "agentA", "run_id": "3"})
    )

    # non-dict JSON
    (storage / "agentA_4_feedback.json").write_text(json.dumps(["a", "b"]))

    fs = FeedbackStore(storage_dir=str(storage))

    caplog.set_level(logging.WARNING)

    perf = fs.get_agent_performance("agentA")

    # Only the single valid file should be counted
    assert perf["total_feedbacks"] == 1
    assert pytest.approx(perf["average_score"], 0.001) == 0.8

    # Ensure warnings were emitted for skipped files
    assert any("Skipping" in r.message for r in caplog.records)


def test_trace_analytics_job_wraps_and_logs(monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    # 1) When tracer is not available, we should hit the TRACE-MOCK path
    monkeypatch.setattr(azure_tracing, "_tracer", None)

    @azure_tracing.trace_analytics_job("jobX", "client1", "r1")
    def f(x):
        """My docstring"""
        return x + 1

    # wraps preserved
    assert f.__name__ == "f"
    assert f.__doc__ == "My docstring"
    assert f(1) == 2

    assert any("TRACE-MOCK" in r.message for r in caplog.records)

    # 2) When tracer is present, ensure we create a span and add attributes
    class FakeSpan:
        def __init__(self, name):
            self.name = name
            self.attrs = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def add_attribute(self, k, v):
            self.attrs.append((k, v))

    class FakeTracer:
        def __init__(self):
            self.spans = []

        def span(self, name):
            s = FakeSpan(name)
            self.spans.append(s)
            return s

    fake = FakeTracer()
    monkeypatch.setattr(azure_tracing, "_tracer", fake)

    caplog.clear()

    @azure_tracing.trace_analytics_job("jobY", "client2", "r2")
    def g(x):
        return x * 2

    assert g.__name__ == "g"
    assert g(3) == 6

    assert len(fake.spans) == 1
    assert fake.spans[0].name == "jobY.r2"
    assert any(
        "TRACE] Starting job: jobY" in r.message or "TRACE-MOCK" in r.message
        for r in caplog.records
    )
