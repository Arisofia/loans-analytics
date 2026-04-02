from datetime import datetime, timezone
from typing import Optional

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

def get_iso_timestamp() -> str:
    return get_utc_now().isoformat()

def parse_iso_timestamp(timestamp_str: str) -> datetime:
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1] + '+00:00'
    return datetime.fromisoformat(timestamp_str)

def format_timestamp(dt: datetime, fmt: Optional[str]=None) -> str:
    if fmt is None:
        return dt.isoformat()
    return dt.strftime(fmt)
