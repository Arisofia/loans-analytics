import re
from datetime import datetime
from typing import Any

ISO8601_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$")


def is_valid_iso8601(val: Any) -> bool:
    """Check if value is a valid ISO 8601 date string."""
    if not isinstance(val, str):
        return False
    # Accept YYYY-MM-DD or full ISO 8601
    iso8601_regex = r"^\d{4}-\d{2}-\d{2}([T\s][\d:.+-Z]*)?$"
    try:
        if re.match(iso8601_regex, val):
            # Try parsing to ensure it's a valid date
            datetime.fromisoformat(val.replace("Z", "+00:00").replace(" ", "T"))
            return True
    except ValueError:
        return False
    return False
