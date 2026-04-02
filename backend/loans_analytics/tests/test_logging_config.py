import logging
import unittest
from backend.loans_analytics.logging_config import configure_logging, get_logger

class TestLoggingConfig(unittest.TestCase):

    def test_get_logger_with_name(self):
        logger = get_logger('test.module')
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test.module')

    def test_get_logger_with_none(self):
        logger = get_logger(None)
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'root')

    def test_get_logger_default(self):
        logger = get_logger()
        self.assertIsInstance(logger, logging.Logger)

    def test_configure_logging_default(self):
        configure_logging()
        logger = get_logger('test.config')
        self.assertEqual(logger.level, 0)

    def test_configure_logging_custom_level(self):
        configure_logging(level='WARNING')
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.WARNING)

    def test_logger_singleton_behavior(self):
        logger1 = get_logger('test.singleton')
        logger2 = get_logger('test.singleton')
        self.assertIs(logger1, logger2)
if __name__ == '__main__':
    unittest.main()
