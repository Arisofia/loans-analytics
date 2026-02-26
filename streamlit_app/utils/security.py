"""Security-related helper utilities for streamlit pages.

Contains helper to sanitize API base URL and break taint propagation for SSRF.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from typing import Optional
from urllib.parse import urlparse


def sanitize_api_base(base: str) -> Optional[str]:
    """Validate and normalize the API base URL.

    Returns a normalized base like 'https://example.com' or None when invalid.
    This removes any path/query/fragment that could be attacker-controlled.
    """
    try:
        parsed = urlparse(base)
        if parsed.scheme not in ("http", "https"):
            return None
        if not parsed.netloc:
            return None
        # Normalize to scheme://netloc (strip path/query/fragment)
        safe = f"{parsed.scheme}://{parsed.netloc}"

        # Optional extra validation: reject IPs in known private ranges unless explicitly allowed
        host = parsed.hostname
        try:
            for res in socket.getaddrinfo(host, None):
                addr = res[4][0]
                ip = ipaddress.ip_address(addr)
                # If the IP is private/non-global and not localhost, consider rejecting
                if ip.is_private and not ip.is_loopback:
                    # Allow private addresses only if explicitly configured via env var
                    if os.environ.get("ALLOW_PRIVATE_API_BASE") != "1":
                        return None
        except Exception:
            # DNS issues: fail closed
            return None

        return safe
    except Exception:
        return None
