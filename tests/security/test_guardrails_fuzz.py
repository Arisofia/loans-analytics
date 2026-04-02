from __future__ import annotations
from hypothesis import given, settings
from hypothesis import strategies as st
from backend.loans_analytics.multi_agent.guardrails import Guardrails

@settings(max_examples=150, deadline=None)
@given(user_input=st.text(min_size=0, max_size=2000))
def test_sanitize_for_logging_neutralizes_control_chars(user_input: str) -> None:
    sanitized = Guardrails.sanitize_for_logging(user_input, max_length=256)
    assert '\n' not in sanitized
    assert '\r' not in sanitized
    assert '\x00' not in sanitized
    assert '\x1b' not in sanitized
    assert len(sanitized) <= 270

@settings(max_examples=100, deadline=None)
@given(local=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1), domain=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1))
def test_redact_pii_replaces_emails(local: str, domain: str) -> None:
    payload = f'Contact: {local}@{domain}.com'
    redacted = Guardrails.redact_pii(payload)
    assert '@{}.'.format(domain) not in redacted
    assert '[REDACTED]' in redacted
