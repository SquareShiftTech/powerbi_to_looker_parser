"""Load dataset metadata from Power BI Scanner API."""

import time
from typing import Any

import requests

BASE_URL = "https://api.powerbi.com/v1.0/myorg"
DEFAULT_SCAN_TIMEOUT = 300
DEFAULT_POLL_INTERVAL = 5


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


def _api_get(headers: dict, path: str, params: dict | None = None) -> requests.Response:
    url = f"{BASE_URL}{path}"
    return requests.get(url, headers=headers, params=params or {}, timeout=60)


def _api_post(
    headers: dict,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
) -> requests.Response:
    url = f"{BASE_URL}{path}"
    kwargs: dict = {"headers": headers}
    if params:
        kwargs["params"] = params
    if json_body is not None:
        kwargs["json"] = json_body
    return requests.post(url, **kwargs, timeout=60)


def run_scanner(
    headers: dict,
    workspace_id: str,
    *,
    timeout: int = DEFAULT_SCAN_TIMEOUT,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
) -> dict[str, Any]:
    """Start Scanner for workspace, poll until Succeeded, return full scan result.

    Args:
        headers: Authorization and Content-Type headers.
        workspace_id: Power BI workspace (group) id.
        timeout: Max seconds to wait for scan.
        poll_interval: Seconds between scanStatus polls.

    Returns:
        Full scan result dict (workspaces, datasets, reports, dashboards).

    Raises:
        ValueError: If getInfo/scanStatus/scanResult fail or scan times out.
    """
    params = {
        "datasetSchema": "true",
        "datasetExpressions": "true",
        "datasourceDetails": "true",
        "lineage": "true",
        "getArtifactUsers": "true",
    }
    body = {"workspaces": [workspace_id]}
    r = _api_post(headers, "/admin/workspaces/getInfo", params=params, json_body=body)
    if r.status_code not in (200, 202):
        raise ValueError(f"getInfo failed: {r.status_code} - {r.text}")
    scan_id = r.json().get("id")
    if not scan_id:
        raise ValueError("getInfo did not return scan id")

    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise ValueError(f"Scan did not complete within {timeout}s")
        r = _api_get(headers, f"/admin/workspaces/scanStatus/{scan_id}")
        if r.status_code != 200:
            raise ValueError(f"scanStatus error: {r.status_code}")
        status = r.json().get("status")
        if status == "Succeeded":
            break
        if status == "Failed":
            raise ValueError("Scan failed")
        time.sleep(poll_interval)

    r = _api_get(headers, f"/admin/workspaces/scanResult/{scan_id}")
    if r.status_code != 200:
        raise ValueError(f"scanResult error: {r.status_code}")
    return r.json()


def filter_scan_result(
    scan_result: dict[str, Any],
    workspace_id: str,
    report_name: str,
) -> dict[str, Any]:
    """Filter scan result to one workspace and one report/dataset by name.

    Returns a dict with workspace_id, workspace_name, report_name, workspaces
    (list with one workspace, datasets/reports filtered by report_name).
    """
    workspace_name = ""
    filtered_workspaces = []
    for ws in scan_result.get("workspaces", []):
        if ws.get("id") != workspace_id:
            continue
        workspace_name = ws.get("name", "")
        datasets = [d for d in ws.get("datasets", []) if d.get("name") == report_name]
        reports = [r for r in ws.get("reports", []) if r.get("name") == report_name]
        dashboards = ws.get("dashboards", [])
        filtered_workspaces.append({
            "id": ws.get("id"),
            "name": ws.get("name"),
            "datasets": datasets,
            "reports": reports,
            "dashboards": dashboards,
        })
        break

    return {
        "workspace_id": workspace_id,
        "workspace_name": workspace_name,
        "report_name": report_name,
        "workspaces": filtered_workspaces,
    }


def fetch_report_metadata(
    workspace_id: str,
    report_name: str,
    credentials: dict[str, str],
    *,
    timeout: int = DEFAULT_SCAN_TIMEOUT,
) -> dict[str, Any]:
    """Get token, run scanner, filter to one report. Returns API metadata for that report.

    Args:
        workspace_id: Power BI workspace id.
        report_name: Report/dataset name to filter.
        credentials: tenant_id, client_id, client_secret (or access_token).
        timeout: Scanner wait timeout.

    Returns:
        Dict with workspace_id, workspace_name, report_name, workspaces.
    """
    token = get_token(credentials)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    scan_result = run_scanner(headers, workspace_id, timeout=timeout)
    return filter_scan_result(scan_result, workspace_id, report_name)
