import re
import warnings
from typing import Optional

try:
    from requests.exceptions import RequestsDependencyWarning  # noqa: E402
except ImportError:

    if "RequestsDependencyWarning" not in locals():

        class RequestsDependencyWarning(Warning):
            pass


try:
    from packaging.version import InvalidVersion, Version  # noqa: E402
except ImportError:
    Version = None


def check_cryptography_robust(cryptography_version: Optional[str]) -> None:
    """Robust cryptography version check.

    Uses packaging.Version if available to properly compare prerelease versions.
    Falls back to a numeric regex extraction.
    """
    if not cryptography_version:
        return

    if Version:
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
