import os

import sentry_sdk


def init_sentry(service_name: str) -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    send_default_pii = os.getenv("SENTRY_SEND_DEFAULT_PII", "false").lower() == "true"

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("ENVIRONMENT", "local"),
        release=os.getenv("SENTRY_RELEASE", f"{service_name}@dev"),
        send_default_pii=send_default_pii,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
    )
