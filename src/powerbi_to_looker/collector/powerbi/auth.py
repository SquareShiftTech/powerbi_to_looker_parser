"""Power BI API auth: get access token from credentials (from orchestration)."""

import requests


def get_token(credentials: dict[str, str]) -> str:
    """Get Power BI access token via client credentials.

    Args:
        credentials: Must contain tenant_id, client_id, client_secret.
            Alternatively access_token (returned as-is).

    Returns:
        Access token string.

    Raises:
        ValueError: If credentials are missing or token request fails.
    """
    if credentials.get("access_token"):
        return credentials["access_token"]
    tenant_id = credentials.get("tenant_id")
    client_id = credentials.get("client_id")
    client_secret = credentials.get("client_secret")
    if not all((tenant_id, client_id, client_secret)):
        raise ValueError(
            "credentials must contain tenant_id, client_id, client_secret, or access_token"
        )
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://analysis.windows.net/powerbi/api/.default",
    }
    r = requests.post(token_url, data=data, timeout=30)
    if r.status_code != 200:
        raise ValueError(f"Token request failed: {r.status_code} - {r.text}")
    out = r.json()
    token = out.get("access_token")
    if not token:
        raise ValueError("Token response did not contain access_token")
    return token
