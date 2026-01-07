"""Fetch data from HubSpot API."""

import os
from typing import Dict, List


def fetch_contacts(api_key: str) -> List[Dict]:
    """
    Fetch contacts from HubSpot.

    Args:
        api_key: HubSpot API key from environment

    Returns:
        List of contact dictionaries
    """
    # TODO: Implement HubSpot API integration
    return []


def fetch_deals(api_key: str) -> List[Dict]:
    """
    Fetch deals from HubSpot.

    Args:
        api_key: HubSpot API key from environment

    Returns:
        List of deal dictionaries
    """
    # TODO: Implement HubSpot deals API integration
    return []


if __name__ == "__main__":
    api_key = os.getenv("HUBSPOT_API_KEY")
    if api_key:
        contacts = fetch_contacts(api_key)
        deals = fetch_deals(api_key)
        print(f"Fetched {len(contacts)} contacts and {len(deals)} deals")
    else:
        print("HUBSPOT_API_KEY not found in environment")
