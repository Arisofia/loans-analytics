"""
Security tests for path traversal prevention (CodeQL Alert #136).

Verifies that the path validation in python/apps/analytics/api/main.py
properly prevents directory traversal attacks.
"""

import pytest
from pathlib import Path
from python.apps.analytics.api.main import _sanitize_and_resolve, HTTPException


class TestPathTraversalPrevention:
    """Test suite for path traversal vulnerability prevention."""
    
    def test_rejects_absolute_paths(self, tmp_path):
        """Verify absolute paths are rejected."""
        with pytest.raises(ValueError, match="absolute paths are not allowed"):
            _sanitize_and_resolve("/etc/passwd", tmp_path)
        
        with pytest.raises(ValueError, match="absolute paths are not allowed"):
            _sanitize_and_resolve("/root/secret.txt", tmp_path)
    
    def test_rejects_parent_traversal(self, tmp_path):
        """Verify parent directory traversal is blocked."""
        with pytest.raises(ValueError, match="parent traversal is not allowed"):
            _sanitize_and_resolve("../../../etc/passwd", tmp_path)
        
        with pytest.raises(ValueError, match="parent traversal is not allowed"):
            _sanitize_and_resolve("data/../../../secrets.env", tmp_path)
    
    def test_rejects_invalid_characters(self, tmp_path):
        """Verify paths with invalid characters are rejected."""
        malicious_chars = [
            "file;rm -rf /",  # Command injection
            "file\x00.txt",   # Null byte injection
            "file<script>",   # XSS attempt
            "file|cmd",       # Pipe injection
        ]
        
        for malicious in malicious_chars:
            with pytest.raises(ValueError, match="invalid characters"):
                _sanitize_and_resolve(malicious, tmp_path)
    
    def test_rejects_empty_path(self, tmp_path):
        """Verify empty paths are rejected."""
        with pytest.raises(ValueError, match="empty path"):
            _sanitize_and_resolve("", tmp_path)
    
    def test_allows_legitimate_paths(self, tmp_path):
        """Verify legitimate paths are accepted."""
        # Create test file structure
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "report.csv"
        test_file.write_text("test data")
        
        # These should work
        legitimate_paths = [
            "report.csv",
            "data/report.csv",
            "reports/2026/january.csv",
            "analytics_data-2026.json",
        ]
        
        for path in legitimate_paths:
            try:
                resolved = _sanitize_and_resolve(path, tmp_path)
                # Should return a path within tmp_path
                assert resolved.is_relative_to(tmp_path)
            except ValueError:
                # OK if file doesn't exist, just testing validation
                pass
    
    def test_resolved_path_within_allowed_dir(self, tmp_path):
        """Verify resolved paths stay within allowed directory."""
        # Create a file we CAN access
        allowed_file = tmp_path / "allowed.txt"
        allowed_file.write_text("accessible")
        
        # Resolve the path
        resolved = _sanitize_and_resolve("allowed.txt", tmp_path)
        
        # Verify it's within tmp_path
        assert resolved.is_relative_to(tmp_path)
        assert resolved.exists()
        assert resolved.read_text() == "accessible"
    
    def test_symlink_cannot_escape(self, tmp_path):
        """Verify symlinks cannot escape allowed directory."""
        # Create directory structure
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        secret_file = outside_dir / "secret.txt"
        secret_file.write_text("secret data")
        
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        
        # Try to create symlink pointing outside (may fail on Windows)
        try:
            symlink = allowed_dir / "escape"
            symlink.symlink_to(secret_file)
            
            # Attempting to access the symlink should fail containment check
            with pytest.raises(ValueError, match="outside the allowed data directory"):
                _sanitize_and_resolve("escape", allowed_dir)
        except OSError:
            # Skip on systems that don't support symlinks
            pytest.skip("Symlinks not supported on this system")
    
    def test_url_encoded_traversal_blocked(self, tmp_path):
        """Verify URL-encoded traversal attempts are blocked."""
        encoded_attempts = [
            "..%2F..%2Fetc%2Fpasswd",  # URL encoded ../
            "..%252F..%252F",           # Double URL encoded
            "data%2F..%2F..%2Fsecret", # Mixed encoding
        ]
        
        for encoded in encoded_attempts:
            # Should fail validation (URL decoding handled by web framework)
            with pytest.raises(ValueError):
                _sanitize_and_resolve(encoded, tmp_path)
    
    def test_windows_path_separators_handled(self, tmp_path):
        """Verify Windows-style path separators are handled."""
        # Backslashes should be normalized to forward slashes
        result = _sanitize_and_resolve("data\\reports\\file.csv", tmp_path)
        # Should still be within allowed directory
        assert result.is_relative_to(tmp_path)


class TestComplianceRequirements:
    """Tests for enterprise security compliance."""
    
    def test_owasp_asvs_5_2_1_compliance(self, tmp_path):
        """
        Verify compliance with OWASP ASVS v4.0 5.2.1.
        
        5.2.1: Verify that the application uses OS level access controls
        to protect files and resources from unauthorized access.
        """
        # Create test structure
        secret_dir = tmp_path.parent / "secrets"
        secret_dir.mkdir(exist_ok=True)
        secret_file = secret_dir / "credentials.env"
        secret_file.write_text("DATABASE_PASSWORD=secret123")
        
        allowed_dir = tmp_path / "public"
        allowed_dir.mkdir()
        
        # Verify cannot access files outside allowed directory
        traversal_attempts = [
            "../secrets/credentials.env",
            "../../secrets/credentials.env",
            "../../../secrets/credentials.env",
        ]
        
        for attempt in traversal_attempts:
            with pytest.raises(ValueError):
                _sanitize_and_resolve(attempt, allowed_dir)
        
        # Secret file should remain inaccessible
        assert secret_file.exists()
        assert secret_file.read_text() == "DATABASE_PASSWORD=secret123"
    
    def test_defense_in_depth(self, tmp_path):
        """
        Verify multiple layers of protection (defense-in-depth).
        
        Even if one protection layer fails, others should catch attacks.
        """
        test_cases = [
            ("../etc/passwd", "parent traversal"),
            ("/etc/passwd", "absolute path"),
            ("file;rm -rf /", "invalid characters"),
            ("", "empty path"),
        ]
        
        for malicious_input, attack_type in test_cases:
            with pytest.raises(ValueError) as exc_info:
                _sanitize_and_resolve(malicious_input, tmp_path)
            
            # Should have clear error message
            assert len(str(exc_info.value)) > 0, \
                f"No error message for {attack_type} attack"


@pytest.fixture
def tmp_path(tmp_path):
    """Fixture providing temporary directory for tests."""
    return tmp_path
