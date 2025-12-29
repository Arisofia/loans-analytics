import os
import sys
import hubspot
from hubspot.crm.owners import ApiException
from dotenv import load_dotenv

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
    
    hubspot_api_key = os.getenv("HUBSPOT_API_KEY")
    if not hubspot_api_key:
        print("❌ HUBSPOT_API_KEY: NOT FOUND in environment.")
        print("   Please ensure HUBSPOT_API_KEY is set in your .env file.")
        sys.exit(1)

    print(f"✅ HUBSPOT_API_KEY: Found. (Value: {mask_value(hubspot_api_key)})")
    
    print("\nStep 2: Verifying HubSpot API connectivity and authentication...")
    try:
        client = hubspot.Client.create(api_key=hubspot_api_key)
        
        # CORRECTED: Restored the .basic_api attribute required for the owners endpoint.
        client.crm.owners.basic_api.get_page(limit=1)
        
        print("✅ HubSpot API Verification: SUCCESS")
        print("   Successfully authenticated and connected to the HubSpot API.")

    except ApiException as e:
        print("❌ HubSpot API Verification: FAILED")
        if e.status == 401:
            print("   Reason: Authentication error. The API key is likely invalid, expired, or lacks permissions.")
        else:
            print(f"   Reason: An API error occurred (Status: {e.status}): {e.reason}")
        sys.exit(1)
        
    except Exception as e:
        print("❌ HubSpot API Verification: FAILED")
        print(f"   An unexpected error occurred: {e}")
        sys.exit(1)

    print("=" * 60)

if __name__ == "__main__":
    load_dotenv()
    verify_hubspot_connectivity()
