"""
Security tests for log injection prevention (CodeQL Alert #137).

Verifies that user-controlled input cannot forge log entries.
"""

import logging
import pytest
from python.apps.analytics.api.main import _sanitize_for_logging


class TestLogInjectionPrevention:
    """Test suite for log injection vulnerability fixes."""
    
    def test_sanitize_newlines(self):
        """Verify newlines are escaped to prevent log entry forging."""
        malicious = "innocent.csv\n[2026-02-01] CRITICAL - System hacked"
        sanitized = _sanitize_for_logging(malicious)
        
        # Newlines should be escaped, not literal
        assert '\n' not in sanitized
        assert '\\n' in sanitized
        assert 'innocent.csv' in sanitized
        
    def test_sanitize_carriage_return(self):
        """Verify carriage returns are escaped."""
        malicious = "file.txt\r\nADMIN LOGIN SUCCEEDED"
        sanitized = _sanitize_for_logging(malicious)
        
        assert '\r' not in sanitized
        assert '\n' not in sanitized
        assert '\\r' in sanitized or '\\n' in sanitized
        
    def test_sanitize_ansi_codes(self):
        """Verify ANSI escape codes are removed."""
        malicious = "report.xlsx\x1b[31mCRITICAL ERROR\x1b[0m"
        sanitized = _sanitize_for_logging(malicious)
        
        # ANSI escape character should be removed
        assert '\x1b' not in sanitized
        assert 'report.xlsx' in sanitized
        
    def test_sanitize_null_bytes(self):
        """Verify null bytes are removed."""
        malicious = "file.csv\x00\nHidden log entry"
        sanitized = _sanitize_for_logging(malicious)
        
        assert '\x00' not in sanitized
        assert '\n' not in sanitized
        
    def test_sanitize_truncates_long_input(self):
        """Verify excessive input is truncated to prevent log flooding."""
        long_input = "A" * 500
        sanitized = _sanitize_for_logging(long_input, max_length=200)
        
        assert len(sanitized) <= 220  # 200 + "...[truncated]"
        assert sanitized.endswith("[truncated]")
        
    def test_sanitize_empty_input(self):
        """Verify empty input is handled safely."""
        assert _sanitize_for_logging("") == ""
        
    def test_legitimate_paths_handled_correctly(self):
        """Verify legitimate paths are still handled correctly."""
        legitimate_paths = [
            "reports/monthly.csv",
            "data_2026-01.json",
            "analytics/user-report.xlsx"
        ]
        
        for path in legitimate_paths:
            sanitized = _sanitize_for_logging(path)
            assert sanitized == path, f"Legitimate path {path} should not be modified"
