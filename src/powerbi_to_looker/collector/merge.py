"""Merge API metadata, pbixray output, and report layout into one collector output."""

from typing import Any

# Empty structures for server-only mode (no .pbix file).
EMPTY_PBIX_RESULT: dict[str, Any] = {
    "relationships": [],
    "dax_measures": [],
    "power_query": [],
    "rls": [],
}
EMPTY_REPORT_LAYOUT: dict[str, Any] = {}


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


def raw_from_pbix_only(
    pbix_result: dict[str, Any],
    report_layout: dict[str, Any],
    report_name: str = "Report",
) -> dict[str, Any]:
    """Build raw metadata dict from pbix result + layout only (no API).

    Converts pbix_loader + layout output into the same shape expected by
    canonical builder: workspaces with one dataset, tables with columns and measures.
    """
    relationships_pbix = pbix_result.get("relationships") or []
    relationships_api_style = [_pbix_relationship_to_api_style(r) for r in relationships_pbix]
    dax_measures = pbix_result.get("dax_measures") or []

    # Group measures by table (TableName from pbixray)
    measures_by_table: dict[str, list[dict]] = {}
    for m in dax_measures:
        if not isinstance(m, dict):
            continue
        table_name = m.get("TableName") or m.get("table_name") or ""
        meas_name = m.get("MeasureName") or m.get("name") or m.get("measure_name")
        expr = m.get("Expression") or m.get("expression")
        if not meas_name:
            continue
        measures_by_table.setdefault(table_name, []).append({
            "name": meas_name,
            "expression": expr if isinstance(expr, str) else None,
            "Expression": expr,
        })

    # Build dataset.tables from pbix_result.tables + measures
    api_tables: list[dict[str, Any]] = []
    for t in pbix_result.get("tables") or []:
        table_name = t.get("table_name") or t.get("name") or ""
        if not table_name:
            continue
        columns = []
        for c in t.get("columns") or []:
            col_name = c.get("column_name") or c.get("name")
            if not col_name:
                continue
            data_type = c.get("data_type") or c.get("dataType")
            columns.append({
                "name": col_name,
                "dataType": data_type,
                "columnType": c.get("columnType", "Data"),
            })
        measures = measures_by_table.get(table_name, [])
        api_tables.append({
            "name": table_name,
            "columns": columns,
            "measures": measures,
        })

    dataset = {
        "id": "local_1",
        "name": report_name,
        "tables": api_tables,
        "relationships": relationships_api_style,
    }
    return {
        "workspace_id": "",
        "workspace_name": "",
        "report_name": report_name,
        "workspaces": [{
            "id": "",
            "name": "",
            "datasets": [dataset],
            "reports": [],
            "dashboards": [],
        }],
        "relationships": relationships_api_style,
        "report_layout": report_layout,
        "dax_measures": dax_measures,
        "power_query": pbix_result.get("power_query") or [],
        "rls": pbix_result.get("rls"),
    }
