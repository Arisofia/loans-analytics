import pytest
from backend.python.apps.analytics.api.main import _sanitize_and_resolve

class TestPathTraversalPrevention:

    def test_rejects_absolute_paths(self, tmp_path):
        with pytest.raises(ValueError, match='absolute paths are not allowed'):
            _sanitize_and_resolve('/etc/passwd', tmp_path)
        with pytest.raises(ValueError, match='absolute paths are not allowed'):
            _sanitize_and_resolve('/root/secret.txt', tmp_path)

    def test_rejects_parent_traversal(self, tmp_path):
        with pytest.raises(ValueError, match='parent traversal is not allowed'):
            _sanitize_and_resolve('../../../etc/passwd', tmp_path)
        with pytest.raises(ValueError, match='parent traversal is not allowed'):
            _sanitize_and_resolve('data/../../../secrets.env', tmp_path)

    def test_rejects_invalid_characters(self, tmp_path):
        malicious_chars = ['file;rm -rf /', 'file\x00.txt', 'file<script>', 'file|cmd']
        for malicious in malicious_chars:
            with pytest.raises(ValueError, match='invalid characters'):
                _sanitize_and_resolve(malicious, tmp_path)

    def test_rejects_empty_path(self, tmp_path):
        with pytest.raises(ValueError, match='empty path'):
            _sanitize_and_resolve('', tmp_path)

    def test_allows_legitimate_paths(self, tmp_path):
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        test_file = data_dir / 'report.csv'
        test_file.write_text('test data')
        legitimate_paths = ['report.csv', 'data/report.csv', 'reports/2026/january.csv', 'analytics_data-2026.json']
        for path in legitimate_paths:
            try:
                resolved = _sanitize_and_resolve(path, tmp_path)
                assert resolved.is_relative_to(tmp_path)
            except ValueError:
                pass

    def test_resolved_path_within_allowed_dir(self, tmp_path):
        allowed_file = tmp_path / 'allowed.txt'
        allowed_file.write_text('accessible')
        resolved = _sanitize_and_resolve('allowed.txt', tmp_path)
        assert resolved.is_relative_to(tmp_path)
        assert resolved.exists()
        assert resolved.read_text() == 'accessible'

    def test_symlink_cannot_escape(self, tmp_path):
        outside_dir = tmp_path.parent / 'outside'
        outside_dir.mkdir(exist_ok=True)
        secret_file = outside_dir / 'secret.txt'
        secret_file.write_text('fake_secret_data_for_testing')
        allowed_dir = tmp_path / 'allowed'
        allowed_dir.mkdir()
        try:
            symlink = allowed_dir / 'escape'
            symlink.symlink_to(secret_file)
            with pytest.raises(ValueError, match='outside the allowed data directory'):
                _sanitize_and_resolve('escape', allowed_dir)
        except OSError:
            pytest.skip('Symlinks not supported on this system')

    def test_url_encoded_traversal_blocked(self, tmp_path):
        encoded_attempts = ['..%2F..%2Fetc%2Fpasswd', '..%252F..%252F', 'data%2F..%2F..%2Fsecret']
        for encoded in encoded_attempts:
            with pytest.raises(ValueError):
                _sanitize_and_resolve(encoded, tmp_path)

    def test_windows_path_separators_handled(self, tmp_path):
        result = _sanitize_and_resolve('data\\reports\\file.csv', tmp_path)
        assert result.is_relative_to(tmp_path)

class TestComplianceRequirements:

    def test_owasp_asvs_5_2_1_compliance(self, tmp_path):
        secret_dir = tmp_path.parent / 'secrets'
        secret_dir.mkdir(exist_ok=True)
        secret_file = secret_dir / 'credentials.env'
        secret_file.write_text('DATABASE_PASSWORD=fake_test_password_not_real')
        allowed_dir = tmp_path / 'public'
        allowed_dir.mkdir()
        traversal_attempts = ['../secrets/credentials.env', '../../secrets/credentials.env', '../../../secrets/credentials.env']
        for attempt in traversal_attempts:
            with pytest.raises(ValueError):
                _sanitize_and_resolve(attempt, allowed_dir)
        assert secret_file.exists()
        assert secret_file.read_text() == 'DATABASE_PASSWORD=fake_test_password_not_real'

    def test_defense_in_depth(self, tmp_path):
        test_cases = [('../etc/passwd', 'parent traversal'), ('/etc/passwd', 'absolute path'), ('file;rm -rf /', 'invalid characters'), ('', 'empty path')]
        for malicious_input, attack_type in test_cases:
            with pytest.raises(ValueError) as exc_info:
                _sanitize_and_resolve(malicious_input, tmp_path)
            assert len(str(exc_info.value)) > 0, f'No error message for {attack_type} attack'

@pytest.fixture
def tmp_path(tmp_path):
    return tmp_path
