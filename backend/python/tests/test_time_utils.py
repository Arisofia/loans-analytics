"""Tests for time utilities."""

import unittest
from datetime import datetime, timezone

from backend.python.time_utils import (
    format_timestamp,
    get_iso_timestamp,
    get_utc_now,
    parse_iso_timestamp,
)


class TestTimeUtils(unittest.TestCase):
    """Test time utility functions."""

    def test_get_utc_now_returns_datetime(self):
        """Test that get_utc_now returns a datetime object."""
        result = get_utc_now()
        self.assertIsInstance(result, datetime)

    def test_get_utc_now_is_timezone_aware(self):
        """Test that get_utc_now returns timezone-aware datetime."""
        result = get_utc_now()
        self.assertIsNotNone(result.tzinfo)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_get_iso_timestamp_format(self):
        """Test that get_iso_timestamp returns valid ISO 8601 string."""
        result = get_iso_timestamp()
        self.assertIsInstance(result, str)
        # Should be parseable back to datetime
        parsed = datetime.fromisoformat(result)
        self.assertIsInstance(parsed, datetime)

    def test_parse_iso_timestamp_valid(self):
        """Test parsing a valid ISO timestamp."""
        timestamp_str = "2024-01-28T10:30:00+00:00"
        result = parse_iso_timestamp(timestamp_str)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 28)

    def test_parse_iso_timestamp_with_z_suffix(self):
        """Test parsing ISO timestamp with Z suffix for UTC."""
        timestamp_str = "2024-01-28T10:30:00Z"
        result = parse_iso_timestamp(timestamp_str)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 28)
        # Verify it's timezone-aware and UTC
        self.assertIsNotNone(result.tzinfo)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_parse_iso_timestamp_invalid(self):
        """Test parsing an invalid timestamp raises error."""
        with self.assertRaises(ValueError):
            parse_iso_timestamp("not-a-timestamp")

    def test_format_timestamp_default(self):
        """Test formatting timestamp with default ISO format."""
        dt = datetime(2024, 1, 28, 10, 30, 0, tzinfo=timezone.utc)
        result = format_timestamp(dt)
        self.assertIn("2024-01-28", result)
        self.assertIn("10:30:00", result)

    def test_format_timestamp_custom(self):
        """Test formatting timestamp with custom format."""
        dt = datetime(2024, 1, 28, 10, 30, 0, tzinfo=timezone.utc)
        result = format_timestamp(dt, "%Y-%m-%d")
        self.assertEqual(result, "2024-01-28")

    def test_roundtrip_timestamp(self):
        """Test that timestamp can be formatted and parsed back."""
        original = get_utc_now()
        iso_str = format_timestamp(original)
        parsed = parse_iso_timestamp(iso_str)
        # Compare with microsecond precision loss
        self.assertEqual(original.replace(microsecond=0), parsed.replace(microsecond=0))


if __name__ == "__main__":
    unittest.main()

