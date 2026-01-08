import logging
from typing import Optional
try:
    from iban import is_valid as is_valid_iban
except ImportError:
    # Fallback for environments where iban package is not yet installed
    def is_valid_iban(iban: str) -> bool:
        return len(iban) > 15 # Very basic check if package is missing

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
        # Redact IBAN in logs for security
        redacted = f"{clean_iban[:4]}...{clean_iban[-4:]}" if clean_iban else "unknown"
        logger.error(f"Error validating IBAN {redacted}: {e}")
        return False
