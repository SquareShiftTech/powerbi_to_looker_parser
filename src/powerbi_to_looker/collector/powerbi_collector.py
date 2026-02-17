"""Collect Power BI metadata: API + .pbix (pbixray + layout) merged into one dict."""

import json
import subprocess
from pathlib import Path
from typing import Any

from powerbi_to_looker.collector.api_loader import fetch_report_metadata
from powerbi_to_looker.collector.layout_loader import load_report_layout
from powerbi_to_looker.collector.merge import (
    EMPTY_PBIX_RESULT,
    EMPTY_REPORT_LAYOUT,
    merge_api_and_pbix,
    raw_from_pbix_only,
)
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


def collect_server_only(
    workspace_id: str,
    report_name: str,
    credentials: dict[str, str],
    *,
    scan_timeout: int = 300,
) -> dict[str, Any]:
    """Collect metadata from Power BI Scanner API only (no .pbix file).

    Returns raw metadata with dataset structure from API; relationships and
    pbix-only fields will be empty. Use when you only have API access.

    Args:
        workspace_id: Power BI workspace (group) id.
        report_name: Report/dataset name to filter in scan result.
        credentials: tenant_id, client_id, client_secret (or access_token).
        scan_timeout: Max seconds to wait for Scanner API (default 300).

    Returns:
        Raw metadata dict (same shape as collect()); relationships empty.
    """
    api_result = fetch_report_metadata(
        workspace_id,
        report_name,
        credentials,
        timeout=scan_timeout,
    )
    return merge_api_and_pbix(
        api_result,
        EMPTY_PBIX_RESULT,
        EMPTY_REPORT_LAYOUT,
    )


def _run_pbi_tools_extract(pbi_tools_path: str | Path, pbix_path: Path, out_dir: Path) -> None:
    """Run pbi-tools extract on .pbix; output to out_dir. Raises on failure."""
    path = Path(pbi_tools_path)
    exe = path / "pbi-tools.exe"
    if not exe.is_file():
        raise FileNotFoundError(f"pbi-tools not found at {exe}")
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(exe), "extract", str(pbix_path.resolve()), str(out_dir.resolve())],
        check=True,
        capture_output=True,
        text=True,
    )


def collect_local(
    pbix_path: str | Path,
    report_name: str | None = None,
    *,
    use_pbi_tools: bool = False,
    pbi_tools_path: str | Path | None = None,
) -> dict[str, Any]:
    """Collect metadata from .pbix file only (no Power BI API).

    Optionally runs pbi-tools extract first (e.g. to unpack .pbix for inspection).
    Then loads data model and layout from the .pbix via pbixray and returns
    raw metadata in the same shape as collect().

    Args:
        pbix_path: Path to .pbix file.
        report_name: Name for the report/dataset (default: stem of pbix_path).
        use_pbi_tools: If True, run pbi-tools extract before loading (requires pbi_tools_path).
        pbi_tools_path: Directory containing pbi-tools.exe (required if use_pbi_tools).

    Returns:
        Raw metadata dict (same shape as collect()).
    """
    path = Path(pbix_path)
    if not path.exists():
        raise FileNotFoundError(f"PBIX file not found: {pbix_path}")
    name = report_name or path.stem

    if use_pbi_tools and pbi_tools_path:
        # Extract to a folder next to the .pbix for user inspection
        out_dir = path.parent / f"{path.stem}_extracted"
        _run_pbi_tools_extract(pbi_tools_path, path, out_dir)

    pbix_result = load_from_pbix(path)
    report_layout = load_report_layout(path)
    return raw_from_pbix_only(pbix_result, report_layout, report_name=name)


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
