"""Tests for logging configuration utilities."""

import logging
import unittest

from backend.python.logging_config import configure_logging, get_logger


class TestLoggingConfig(unittest.TestCase):
    """Test logging configuration utilities."""

    def test_get_logger_with_name(self):
        """Test getting logger with a name."""
        logger = get_logger("test.module")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test.module")

    def test_get_logger_with_none(self):
        """Test getting root logger."""
        logger = get_logger(None)
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "root")

    def test_get_logger_default(self):
        """Test getting logger without parameters."""
        logger = get_logger()
        self.assertIsInstance(logger, logging.Logger)

    def test_configure_logging_default(self):
        """Test logging configuration with defaults."""
        # Should not raise any exceptions
        configure_logging()
        logger = get_logger("test.config")
        self.assertEqual(logger.level, 0)  # Inherits from root

    def test_configure_logging_custom_level(self):
        """Test logging configuration with custom level."""
        configure_logging(level="WARNING")
        # Verify root logger level is set
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.WARNING)

    def test_logger_singleton_behavior(self):
        """Test that multiple calls return the same logger instance."""
        logger1 = get_logger("test.singleton")
        logger2 = get_logger("test.singleton")
        self.assertIs(logger1, logger2)


if __name__ == "__main__":
    unittest.main()

