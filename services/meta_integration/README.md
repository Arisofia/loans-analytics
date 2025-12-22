# Meta (Instagram/Facebook) Integration Service

This service provides backend integration with Meta (Facebook/Instagram) Graph API for analytics and data sync.

## Setup

1. Register a Meta App at https://developers.facebook.com/ and obtain:
   - App ID
   - App Secret
   - Redirect URI (for OAuth)
2. Set the following environment variables:
   - `META_APP_ID`
   - `META_APP_SECRET`
   - `META_REDIRECT_URI`
   - `META_ACCESS_TOKEN` (optional, for long-lived tokens)

## Endpoints

- `/auth`: Initiate OAuth flow
- `/callback`: Handle OAuth redirect
- `/insights`: Fetch Instagram/Facebook insights

## Usage

- Use this service as a backend API for your Figma-driven frontend.
- Secure all endpoints and never expose secrets to the client.

## References
- [Meta Graph API Docs](https://developers.facebook.com/docs/graph-api)
- [Instagram Graph API Docs](https://developers.facebook.com/docs/instagram-api)
