import os
import sys

from dotenv import load_dotenv
from hubspot import HubSpot
try:
    from hubspot.auth.oauth.exceptions import ApiException
except ImportError:
    try:
        from hubspot.crm.owners.exceptions import ApiException
    except ImportError:
        ApiException = Exception


def mask_value(value: str) -> str:
    """Masks a sensitive value, showing only the first and last few characters."""
    if not isinstance(value, str) or len(value) <= 8:
        return "********"
    return f"{value[:4]}...{value[-4:]}"


def verify_hubspot_connectivity():
    """
    Checks for the HubSpot API key and verifies it by making a live,
    read-only API call to fetch account owners.
    """
    print("=" * 60)
    print("Step 1: Checking for HubSpot API Key presence...")

    hubspot_access_token = os.getenv("HUBSPOT_ACCESS_TOKEN") or os.getenv("HUBSPOT_API_KEY")
    if not hubspot_access_token:
        print("❌ HUBSPOT_ACCESS_TOKEN or HUBSPOT_API_KEY: NOT FOUND in environment.")
        print("   Please ensure HUBSPOT_ACCESS_TOKEN or HUBSPOT_API_KEY is set in your .env file.")
        sys.exit(1)

    print(f"✅ HUBSPOT_ACCESS_TOKEN: Found. (Value: {mask_value(hubspot_access_token)})")

    print("\nStep 2: Verifying HubSpot API connectivity and authentication...")
    try:
        client = HubSpot(access_token=hubspot_access_token)
        client.crm.owners.basic_api.get_page(limit=1)
        print("✅ HubSpot API Verification: SUCCESS")
        print("   Successfully authenticated and connected to the HubSpot API.")

    except ApiException as e:
        print("❌ HubSpot API Verification: FAILED")
        if hasattr(e, 'status') and e.status == 401:
            print(
                "   Reason: Authentication error. The access token is likely invalid, expired, or lacks permissions."
            )
        else:
            print(f"   Reason: An API error occurred (Status: {getattr(e, 'status', 'unknown')}): {getattr(e, 'reason', str(e))}")
        sys.exit(1)

    except Exception as e:
        print("❌ HubSpot API Verification: FAILED")
        print(f"   An unexpected error occurred: {e}")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    load_dotenv()
    verify_hubspot_connectivity()
