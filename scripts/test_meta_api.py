import os
import requests

API_VERSION = "v17.0"
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
AD_ACCOUNT = os.getenv("META_AD_ACCOUNT_ID")  # e.g. act_12345

def list_ad_accounts():
    url = f"https://graph.facebook.com/{API_VERSION}/me/adaccounts"
    r = requests.get(url, params={"access_token": ACCESS_TOKEN})
    print("Ad Accounts Response:", r.text)  # Debug print
    r.raise_for_status()
    return r.json()

def fetch_campaigns():
    url = f"https://graph.facebook.com/{API_VERSION}/{AD_ACCOUNT}/campaigns"
    r = requests.get(url, params={
        "access_token": ACCESS_TOKEN,
        "fields": "id,name,status,effective_status",
        "limit": 50
    })
    print("Campaigns Response:", r.text)  # Debug print
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    print(list_ad_accounts())
    print(fetch_campaigns())
