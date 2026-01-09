import logging
from typing import Optional

try:
    from stdnum import iban as iban_validator

    def is_valid_iban(iban: str) -> bool:
        return iban_validator.is_valid(iban)
except ImportError:
    # Fallback for environments where python-stdnum package is not yet installed
    def is_valid_iban(iban: str) -> bool:
        return len(iban) > 15  # Very basic check if package is missing


logger = logging.getLogger(__name__)


def validate_iban(iban: Optional[str]) -> bool:
    """
    Validate an IBAN string.
    Returns True if valid, False otherwise.
    """
    if not iban:
        return False

    clean_iban = iban.replace(" ", "").upper()
    try:
        return is_valid_iban(clean_iban)
    except Exception as e:
        # Avoid logging IBAN or any derived identifier; log only generic error information
        logger.error("Error validating IBAN", exc_info=e)
        return False
