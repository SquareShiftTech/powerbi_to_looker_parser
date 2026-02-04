"""Collect Power BI metadata: API + .pbix (pbixray + layout) merged into one dict."""

import json
from pathlib import Path
from typing import Any

from powerbi_to_looker.collector.api_loader import fetch_report_metadata
from powerbi_to_looker.collector.layout_loader import load_report_layout
from powerbi_to_looker.collector.merge import merge_api_and_pbix
from powerbi_to_looker.collector.pbix_loader import load_from_pbix


def collect(
    workspace_id: str,
    report_name: str,
    credentials: dict[str, str],
    pbix_path: str | Path,
    *,
    scan_timeout: int = 300,
) -> dict[str, Any]:
    """Collect full metadata for a report: API (dataset) + pbix (relationships + layout).

    All parameters are mandatory. Uses Power BI Scanner API for tables/columns/measures,
    pbixray on the .pbix for relationships (and optional M/RLS), and Report/Layout
    from .pbix for pages/visuals/filters/slicers.

    Args:
        workspace_id: Power BI workspace (group) id.
        report_name: Report/dataset name to filter in scan result.
        credentials: tenant_id, client_id, client_secret (or access_token).
        pbix_path: Path to .pbix report file.
        scan_timeout: Max seconds to wait for Scanner API (default 300).

    Returns:
        Single raw metadata dict: workspace_id, workspace_name, report_name, workspaces,
        relationships (from pbix), report_layout (pages, visuals, slicers), optional
        dax_measures, power_query, rls.

    Raises:
        FileNotFoundError: If pbix_path does not exist.
        ValueError: If API or merge fails.
        ImportError: If pbixray/pandas missing when loading from .pbix.
    """
    path = Path(pbix_path)
    if not path.exists():
        raise FileNotFoundError(f"PBIX file not found: {pbix_path}")

    api_result = fetch_report_metadata(
        workspace_id,
        report_name,
        credentials,
        timeout=scan_timeout,
    )
    pbix_result = load_from_pbix(path)
    report_layout = load_report_layout(path)

    return merge_api_and_pbix(api_result, pbix_result, report_layout)


def collect_from_dict_or_path(path_or_metadata: str | dict[str, Any]) -> dict[str, Any]:
    """Return raw metadata from a dict or JSON file path (backward compatibility).

    Use for migrate_metadata(metadata_dict) or migrate_file(json_path) when not
    using the full API + .pbix flow.

    Args:
        path_or_metadata: In-memory metadata dict or path to .json file.

    Returns:
        Raw Power BI metadata dict.
    """
    if isinstance(path_or_metadata, dict):
        return path_or_metadata
    path = Path(path_or_metadata)
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path_or_metadata}")
    if path.suffix.lower() != ".json":
        raise ValueError(f"Expected .json file, got {path.suffix}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
