"""
Meta Integration FastAPI App
OAuth endpoints and analytics proxy for Meta (Instagram/Facebook).
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import os
from meta_client import MetaAPIClient

app = FastAPI()

@app.get("/auth")
def auth():
    client = MetaAPIClient()
    url = client.get_auth_url()
    return RedirectResponse(url)

@app.get("/callback")
def callback(code: str):
    client = MetaAPIClient()
    try:
        token_data = client.exchange_code(code)
        # Store token_data["access_token"] securely (e.g., DB, session)
        return JSONResponse(token_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/insights/{ig_user_id}")
def insights(ig_user_id: str):
    access_token = os.getenv("META_ACCESS_TOKEN")
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token configured.")
    client = MetaAPIClient(access_token)
    try:
        data = client.get_instagram_insights(ig_user_id)
        return JSONResponse(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
