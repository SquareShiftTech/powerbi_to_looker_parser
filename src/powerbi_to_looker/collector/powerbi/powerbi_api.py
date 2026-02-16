"""Power BI REST API: list reports and export report (.pbix). All inputs from caller."""

from typing import Any

import requests

BASE_URL = "https://api.powerbi.com/v1.0/myorg"


def list_groups(access_token: str) -> list[dict[str, Any]]:
    """List workspaces (groups) the app or user has access to.

    Args:
        access_token: Bearer token from auth.get_token(credentials).

    Returns:
        List of group dicts (id, name, ...).

    Raises:
        ValueError: On 401/403. requests.RequestException on other errors.
    """
    url = f"{BASE_URL}/groups"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, timeout=60)
    if resp.status_code == 401:
        raise ValueError("Unauthorized: token invalid or expired")
    if resp.status_code == 403:
        raise ValueError("Forbidden: app or user lacks permission")
    resp.raise_for_status()
    data = resp.json()
    return data.get("value", [])


def get_workspace_id_by_name(workspace_name: str, access_token: str) -> str | None:
    """Resolve workspace name to workspace (group) id.

    Args:
        workspace_name: Display name of the workspace (case-insensitive match).
        access_token: Bearer token from auth.get_token(credentials).

    Returns:
        The group id if a matching workspace is found, else None.
    """
    groups = list_groups(access_token)
    name_lower = workspace_name.strip().lower()
    for g in groups:
        if (g.get("name") or "").strip().lower() == name_lower:
            return g.get("id")
    return None


def list_reports(workspace_id: str | None, access_token: str) -> list[dict[str, Any]]:
    """List reports in a workspace. workspace_id None = My Workspace.

    Args:
        workspace_id: Power BI group (workspace) id, or None for My Workspace.
        access_token: Bearer token from auth.get_token(credentials).

    Returns:
        List of report dicts (id, name, datasetId, webUrl, ...).

    Raises:
        ValueError: On 401/403. requests.RequestException on other errors.
    """
    if workspace_id:
        path = f"/groups/{workspace_id}/reports"
    else:
        path = "/reports"
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, timeout=60)
    if resp.status_code == 401:
        raise ValueError("Unauthorized: token invalid or expired")
    if resp.status_code == 403:
        raise ValueError("Forbidden: app or user lacks permission")
    resp.raise_for_status()
    data = resp.json()
    return data.get("value", [])


def export_report(
    report_id: str,
    workspace_id: str | None,
    access_token: str,
    *,
    prefer_client_routing: bool = True,
) -> bytes:
    """Export a report as .pbix bytes.

    Args:
        report_id: Power BI report id.
        workspace_id: Group id, or None for My Workspace.
        access_token: Bearer token.
        prefer_client_routing: Add ?preferClientRouting=true (recommended workaround for various API issues).

    Returns:
        .pbix file bytes (application/zip).

    Raises:
        ValueError: On 401/403/404 (404 = report not exportable, e.g. usage metrics) or 400 (bad request, may indicate report configuration issues).
        requests.RequestException: On other errors.
    """
    if workspace_id:
        path = f"/groups/{workspace_id}/reports/{report_id}/Export"
        url = f"{BASE_URL}{path}"
        if prefer_client_routing:
            url += "?preferClientRouting=true"
    else:
        path = f"/reports/{report_id}/Export"
        url = f"{BASE_URL}{path}"
        if prefer_client_routing:
            url += "?preferClientRouting=true"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, timeout=120)
    if resp.status_code == 401:
        raise ValueError("Unauthorized: token invalid or expired")
    if resp.status_code == 403:
        raise ValueError("Forbidden: app or user lacks permission")
    if resp.status_code == 400:
        raise ValueError(
            "Bad request (400). Report may have unsupported configuration "
            "(e.g. live connection, certain data sources, or requires different export method)."
        )
    if resp.status_code == 404:
        raise ValueError(
            "Report not found or not exportable (404). "
            "Usage metrics and some system reports cannot be downloaded as .pbix."
        )
    resp.raise_for_status()
    return resp.content
