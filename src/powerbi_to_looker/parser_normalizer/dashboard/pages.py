"""Build list of DashboardPage from raw pages and pages_metadata."""

from typing import Any

from powerbi_to_looker.models.dashboard import DashboardPage
from powerbi_to_looker.parser_normalizer.dashboard.visuals import process_page_visuals


def build_pages(
    raw_pages: dict[str, Any],
    pages_metadata: dict[str, Any],
    config: dict[str, Any],
) -> tuple[list[DashboardPage], list[Any], list[Any]]:
    """
    Build DashboardPage list and collect all visualizations and filter_components.
    Returns (pages, visualizations, filter_components) where visualizations/filter_components
    are flattened from all pages.
    """
    page_order_ids = (pages_metadata or {}).get("pageOrder") or []
    if not page_order_ids:
        # No pageOrder: use keys of raw_pages in arbitrary order
        page_order_ids = list((raw_pages or {}).keys())

    all_visualizations: list[Any] = []
    all_filter_components: list[Any] = []
    pages: list[DashboardPage] = []

    for order, page_id in enumerate(page_order_ids):
        page_data = (raw_pages or {}).get(page_id)
        if not page_data:
            continue
        page_obj = (page_data.get("page") or {})
        page_name = page_obj.get("displayName") or page_obj.get("name") or page_id
        layout = {}
        if page_obj.get("displayOption"):
            layout["displayOption"] = page_obj["displayOption"]
        if page_obj.get("width") is not None:
            layout["width"] = page_obj["width"]
        if page_obj.get("height") is not None:
            layout["height"] = page_obj["height"]

        visuals = page_data.get("visuals") or {}
        components, viz_list, filt_list = process_page_visuals(page_id, visuals, config)
        all_visualizations.extend(viz_list)
        all_filter_components.extend(filt_list)

        pages.append(
            DashboardPage(
                page_id=page_id,
                page_name=str(page_name),
                page_order=order,
                layout=layout,
                components=components,
            )
        )

    return pages, all_visualizations, all_filter_components
