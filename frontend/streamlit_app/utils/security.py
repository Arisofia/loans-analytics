from __future__ import annotations
import ipaddress
import os
import socket
from typing import Optional
from urllib.parse import urlparse

def sanitize_api_base(base: str) -> Optional[str]:
    try:
        parsed = urlparse(base)
        if parsed.scheme not in ('http', 'https'):
            return None
        if not parsed.netloc:
            return None
        safe = f'{parsed.scheme}://{parsed.netloc}'
        host = parsed.hostname
        if host is None:
            return None
        try:
            ip = ipaddress.ip_address(host)
            if not ip.is_global:
                if os.environ.get('ALLOW_PRIVATE_API_BASE') != '1':
                    return None
        except ValueError:
            try:
                for res in socket.getaddrinfo(host, None):
                    addr = res[4][0]
                    ip = ipaddress.ip_address(addr)
                    if not ip.is_global:
                        if os.environ.get('ALLOW_PRIVATE_API_BASE') != '1':
                            return None
            except socket.gaierror:
                pass
        return safe
    except (TypeError, ValueError, AttributeError):
        return None
