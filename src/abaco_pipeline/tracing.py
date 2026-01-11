"""Tracing helpers for the v2 pipeline scaffold."""

from __future__ import annotations

from opentelemetry import trace


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)
