import re
import warnings
from typing import Any, Optional, Type

try:
    from requests.exceptions import RequestsDependencyWarning
except ImportError:

    class RequestsDependencyWarning(Warning):  # type: ignore[no-redef]
        pass


Version: Any
InvalidVersion: Type[Exception]

try:
    from packaging.version import InvalidVersion, Version

    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False
    Version = None
    InvalidVersion = Exception


def check_cryptography_robust(cryptography_version: Optional[str]) -> None:
    """Robust cryptography version check.

    Uses packaging.Version if available to properly compare prerelease versions.
    Falls back to a numeric regex extraction.
    """
    if not cryptography_version:
        return

    if HAS_PACKAGING and Version:
        try:
            ver = Version(cryptography_version)
        except InvalidVersion:
            return
        try:
            if ver < Version("1.3.4"):
                warnings.warn(
                    f"Old version of cryptography ({cryptography_version}) may cause slowdown.",
                    RequestsDependencyWarning,
                )
        except Exception:
            # Be conservative and don't fail if comparison errors
            return
        return

    m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(cryptography_version))
    if not m:
        return
    parts = [int(p) if p is not None else 0 for p in m.groups()]
    while len(parts) < 3:
        parts.append(0)
    if parts < [1, 3, 4]:
        warnings.warn(
            f"Old version of cryptography ({cryptography_version}) may cause slowdown.",
            RequestsDependencyWarning,
        )
