"""Power BI REST API client for workspace metadata (reports, dashboards, datasets)."""
import logging
import re
import requests

BASE_URL = "https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"

logger = logging.getLogger(__name__)

# Invalid path characters on Windows and common on Unix
_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')
_MAX_FILENAME_LENGTH = 200


def _get(workspace_id: str, access_token: str, path: str) -> list:
    """GET a Power BI list endpoint and return the 'value' array."""
    url = f"{BASE_URL.format(workspace_id=workspace_id)}/{path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 401:
        logger.error("Power BI API returned 401 Unauthorized")
        raise ValueError("Unauthorized: token invalid or expired")
    if resp.status_code == 403:
        logger.error("Power BI API returned 403 Forbidden")
        raise ValueError("Forbidden: app or user lacks permission to this workspace")
    if resp.status_code == 404:
        logger.warning("Power BI API returned 404 for %s", url)
        return []
    resp.raise_for_status()
    data = resp.json()
    return data.get("value", [])


def get_reports(workspace_id: str, access_token: str) -> list:
    """Return list of reports in the workspace (id, name, webUrl, datasetId, ...)."""
    return _get(workspace_id, access_token, "reports")


def get_dashboards(workspace_id: str, access_token: str) -> list:
    return _get(workspace_id, access_token, "dashboards")


def get_datasets(workspace_id: str, access_token: str) -> list:
    return _get(workspace_id, access_token, "datasets")


def _safe_filename(report_name: str, report_id: str) -> str:
    """Derive a safe .pbix filename from report name and id (unique per report)."""
    name = (report_name or "report").strip()
    name = _INVALID_FILENAME_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip() or "report"
    if len(name) > _MAX_FILENAME_LENGTH - 10:
        name = name[:_MAX_FILENAME_LENGTH - 10]
    return f"{name}_{report_id[:8]}.pbix"


def export_report(
    workspace_id: str,
    report_id: str,
    access_token: str,
    prefer_client_routing: bool = True,
) -> bytes:
    """
    Export a report from the workspace as .pbix bytes.
    Uses Export Report In Group API. For large files, follows blob URL if returned as JSON.
    """
    url = f"{BASE_URL.format(workspace_id=workspace_id)}/reports/{report_id}/Export"
    if prefer_client_routing:
        url += "?preferClientRouting=true"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, timeout=120)
    if resp.status_code == 401:
        logger.error("Power BI API returned 401 Unauthorized")
        raise ValueError("Unauthorized: token invalid or expired")
    if resp.status_code == 403:
        logger.error("Power BI API returned 403 Forbidden")
        raise ValueError("Forbidden: app or user lacks permission to this workspace")
    resp.raise_for_status()

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "application/json" in content_type:
        data = resp.json()
        blob_url = data.get("Url") or data.get("url")
        if not blob_url:
            raise ValueError("Export returned JSON but no blob URL (Url/url)")
        blob_resp = requests.get(blob_url, headers=headers, timeout=120)
        blob_resp.raise_for_status()
        return blob_resp.content
    return resp.content
