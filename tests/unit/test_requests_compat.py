import warnings

import pytest

from src.utils.compat import check_cryptography_robust

# Try to import RequestsDependencyWarning, fallback to a mock if not available
try:
    from requests.exceptions import RequestsDependencyWarning
except ImportError:
    from src.utils.compat import RequestsDependencyWarning


def test_check_cryptography_prerelease_and_none():
    # prerelease lower than 1.3.4 should warn
    with pytest.warns(RequestsDependencyWarning):
        check_cryptography_robust("1.3.3rc1")

    # prerelease for 1.3.4 (rc) is still older than 1.3.4 and should warn
    with pytest.warns(RequestsDependencyWarning):
        check_cryptography_robust("1.3.4rc1")

    # release 1.3.4 should NOT warn
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        check_cryptography_robust("1.3.4")
        assert not any(isinstance(w.message, RequestsDependencyWarning) for w in rec)

    # None should be a no-op
    check_cryptography_robust(None)
