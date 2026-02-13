import msal

PBI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]


def get_powerbi_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    Obtain an access token for Power BI API using client credentials flow.
    Returns the access token string.
    Raises ValueError if token is empty or auth fails.
    """
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority,
    )
    result = app.acquire_token_for_client(scopes=PBI_SCOPE)
    if not result:
        raise ValueError(
            "Failed to acquire Power BI token. Check tenant ID, client ID, client secret, "
            "and that the app has Power BI API permissions with admin consent."
        )
    if "access_token" not in result:
        error = result.get("error_description") or result.get("error") or "no access_token in result"
        raise ValueError(f"Power BI token response missing access_token: {error}")
    return result["access_token"]
