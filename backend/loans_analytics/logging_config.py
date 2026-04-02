from __future__ import annotations
import logging
import os
import sentry_sdk

def get_logger(name: str | None=None) -> logging.Logger:
    return logging.getLogger(name)

def configure_logging(level: str='INFO', format_string: str | None=None) -> None:
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    level_upper = level.upper()
    valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    if level_upper not in valid_levels:
        raise ValueError(f'Invalid logging level: {level}. Must be one of {valid_levels}')
    logging.basicConfig(level=getattr(logging, level_upper), format=format_string, datefmt='%Y-%m-%d %H:%M:%S')

def _get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default

def init_sentry(service_name: str) -> None:
    dsn = os.getenv('SENTRY_DSN')
    if not dsn:
        return
    send_default_pii = os.getenv('SENTRY_SEND_DEFAULT_PII', 'false').lower() == 'true'
    sentry_sdk.init(dsn=dsn, environment=os.getenv('ENVIRONMENT', 'local'), release=os.getenv('SENTRY_RELEASE', f'{service_name}@dev'), send_default_pii=send_default_pii, traces_sample_rate=_get_float_env('SENTRY_TRACES_SAMPLE_RATE', 0.1), profiles_sample_rate=_get_float_env('SENTRY_PROFILES_SAMPLE_RATE', 0.0))

def set_sentry_correlation(correlation_id: str) -> None:
    sentry_sdk.set_tag('correlation_id', correlation_id)
    sentry_sdk.set_context('monitoring', {'correlation_id': correlation_id})
