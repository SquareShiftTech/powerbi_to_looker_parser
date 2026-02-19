"""Viz/dashboard orchestrator: raw -> DashboardMetadata."""

from datetime import datetime, timezone
from typing import Any

from powerbi_to_looker.models.dashboard import DashboardMetadata
from powerbi_to_looker.parser_normalizer.dashboard.config import get_viz_config
from powerbi_to_looker.parser_normalizer.dashboard.dashboard import (
    build_dashboard,
    get_report_name_from_raw,
)
from powerbi_to_looker.parser_normalizer.dashboard.pages import build_pages


def run_viz(raw: dict[str, Any], report_id: str | None = None) -> DashboardMetadata:
    """
    Build canonical DashboardMetadata from raw report structure.
    raw must have keys: pages_metadata, pages (from loader).
    report_id: stable report id (e.g. folder name). If None, derived from first page or "unknown".
    """
    config = get_viz_config()
    pages_meta = raw.get("pages_metadata") or {}
    raw_pages = raw.get("pages") or {}

    if report_id is None:
        page_order = pages_meta.get("pageOrder") or list(raw_pages.keys())
        report_id = page_order[0] if page_order else "unknown"

    pages, visualizations, filter_components = build_pages(raw_pages, pages_meta, config)
    report_name = get_report_name_from_raw(raw, report_id)
    dashboard = build_dashboard(report_id, report_name, pages)

    return DashboardMetadata(
        metadata_version="1.0",
        source_system="powerbi",
        extracted_at=datetime.now(timezone.utc),
        dashboards=[dashboard],
        visualizations=visualizations,
        text_components=[],
        filter_components=filter_components,
        image_components=[],
        container_components=[],
        parameter_components=[],
        web_content_components=[],
    )
