import re

def _sanitize_for_logging(value: str, max_length: int=200) -> str:
    if not value:
        return ''
    sanitized = value.replace('\n', '\\n').replace('\r', '\\r')
    sanitized = sanitized.replace('\t', '\\t')
    sanitized = sanitized.replace('\x00', '')
    sanitized = sanitized.replace('\x1b', '')
    sanitized = re.sub('[\\x00-\\x08\\x0B-\\x0C\\x0E-\\x1F\\x7F]', '', sanitized)
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + '...[truncated]'
    return sanitized

class TestLogInjectionPrevention:

    def test_sanitize_newlines(self):
        malicious = 'innocent.csv\n[2026-02-01] CRITICAL - System hacked'
        sanitized = _sanitize_for_logging(malicious)
        assert '\n' not in sanitized
        assert '\\n' in sanitized
        assert 'innocent.csv' in sanitized

    def test_sanitize_carriage_return(self):
        malicious = 'file.txt\r\nADMIN LOGIN SUCCEEDED'
        sanitized = _sanitize_for_logging(malicious)
        assert '\r' not in sanitized
        assert '\n' not in sanitized
        assert '\\r' in sanitized or '\\n' in sanitized

    def test_sanitize_ansi_codes(self):
        malicious = 'report.xlsx\x1b[31mCRITICAL ERROR\x1b[0m'
        sanitized = _sanitize_for_logging(malicious)
        assert '\x1b' not in sanitized
        assert 'report.xlsx' in sanitized

    def test_sanitize_null_bytes(self):
        malicious = 'file.csv\x00\nHidden log entry'
        sanitized = _sanitize_for_logging(malicious)
        assert '\x00' not in sanitized
        assert '\n' not in sanitized

    def test_sanitize_truncates_long_input(self):
        long_input = 'A' * 500
        sanitized = _sanitize_for_logging(long_input, max_length=200)
        assert len(sanitized) <= 220
        assert sanitized.endswith('[truncated]')

    def test_sanitize_empty_input(self):
        assert _sanitize_for_logging('') == ''

    def test_legitimate_paths_handled_correctly(self):
        legitimate_paths = ['reports/monthly.csv', 'data_2026-01.json', 'analytics/user-report.xlsx']
        for path in legitimate_paths:
            sanitized = _sanitize_for_logging(path)
            assert sanitized == path, f'Legitimate path {path} should not be modified'
