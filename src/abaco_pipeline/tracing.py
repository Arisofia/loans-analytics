"""Tracing helpers for the v2 pipeline scaffold."""

from __future__ import annotations  # noqa: E402

from opentelemetry import trace  # noqa: E402


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)
