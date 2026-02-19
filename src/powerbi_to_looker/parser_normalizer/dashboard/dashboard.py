"""Build one Dashboard from report identity and pages."""

from typing import Any

from powerbi_to_looker.models.dashboard import Dashboard


def build_dashboard(
    report_id: str,
    report_name: str | None,
    pages: list[Any],
    source_system: str = "powerbi",
) -> Dashboard:
    """Build canonical Dashboard. report_id is stable id (e.g. folder name); report_name from report or first page."""
    name = report_name or report_id
    is_multi_page = len(pages) > 1
    return Dashboard(
        id=report_id,
        name=name,
        source_system=source_system,
        report_id=report_id,
        is_multi_page=is_multi_page,
        pages=pages,
        interactions=[],
    )


def get_report_name_from_raw(raw: dict[str, Any], report_id: str) -> str | None:
    """Derive report display name from raw. Prefer first page displayName or report_id."""
    pages_meta = raw.get("pages_metadata") or {}
    page_order = pages_meta.get("pageOrder") or []
    pages = raw.get("pages") or {}
    for pid in page_order:
        page_data = pages.get(pid)
        if not page_data:
            continue
        page_obj = (page_data.get("page") or {})
        display_name = page_obj.get("displayName") or page_obj.get("name")
        if display_name:
            return str(display_name).strip()
    return report_id
