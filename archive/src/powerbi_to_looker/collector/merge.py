"""Merge API metadata, pbixray output, and report layout into one collector output."""

from typing import Any


def _pbix_relationship_to_api_style(rel: dict) -> dict:
    """Map pbixray relationship keys to API-style (fromTable, toTable, etc.)."""
    return {
        "fromTable": rel.get("FromTableName"),
        "fromColumn": rel.get("FromColumnName"),
        "toTable": rel.get("ToTableName"),
        "toColumn": rel.get("ToColumnName"),
        "cardinality": rel.get("Cardinality"),
        "crossFilteringBehavior": rel.get("CrossFilteringBehavior"),
        "isActive": bool(rel.get("IsActive", True)),
    }


def merge_api_and_pbix(
    api_result: dict[str, Any],
    pbix_result: dict[str, Any],
    report_layout: dict[str, Any],
) -> dict[str, Any]:
    """Merge API result (dataset structure), pbix result (relationships, etc.), and report_layout.

    - API provides workspace_id, workspace_name, report_name, workspaces (datasets with tables/columns/measures).
    - pbix provides relationships (injected into first dataset and as top-level), plus dax_measures, power_query, rls.
    - report_layout is attached as top-level report_layout.

    Args:
        api_result: Output of api_loader.fetch_report_metadata or filter_scan_result.
        pbix_result: Output of pbix_loader.load_from_pbix.
        report_layout: Output of layout_loader.load_report_layout.

    Returns:
        Single dict for pipeline (canonical stage).
    """
    out = dict(api_result)
    out["report_layout"] = report_layout

    relationships_pbix = pbix_result.get("relationships") or []
    relationships_api_style = [_pbix_relationship_to_api_style(r) for r in relationships_pbix]
    out["relationships"] = relationships_api_style

    if pbix_result.get("dax_measures"):
        out["dax_measures"] = pbix_result["dax_measures"]
    if pbix_result.get("power_query"):
        out["power_query"] = pbix_result["power_query"]
    if pbix_result.get("rls") is not None:
        out["rls"] = pbix_result["rls"]

    for ws in out.get("workspaces", []):
        for ds in ws.get("datasets", []):
            ds["relationships"] = relationships_api_style
        break

    return out
