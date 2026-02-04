"""Build model dict (connection, explores with joins) from canonical datasource."""

from typing import Any

from powerbi_to_looker.models.canonical import Datasource, TableRelationship

from powerbi_to_looker.transformer.view_builder import sanitize_name


def _join_type_to_looker(join_type: str, config: dict[str, Any]) -> str:
    """Map canonical join_type to Looker join type."""
    join_types = config.get("join_types") or {}
    j = (join_type or "LEFT").upper()
    return join_types.get(j) or join_types.get("default", "left_outer")


def build_model(
    datasource: Datasource,
    config: dict[str, Any],
    connection_name: str = "powerbi_connection",
) -> dict[str, Any]:
    """Build model dict with explores and joins from datasource tables and table_relationships."""
    table_names = {t.name: sanitize_name(t.name, config) for t in datasource.tables}
    explores = []

    for table in datasource.tables:
        view_name = table_names.get(table.name) or sanitize_name(table.name, config)
        explore = {
            "name": view_name,
            "view": view_name,
            "label": table.name or view_name,
            "joins": [],
        }
        # Joins where this table is the "from" side
        for rel in datasource.table_relationships or []:
            if rel.from_table != table.name:
                continue
            to_view = table_names.get(rel.to_table)
            if not to_view:
                continue
            sql_on_parts = []
            for on in rel.on_columns or []:
                from_col = on.get("from") or ""
                to_col = on.get("to") or ""
                if from_col and to_col:
                    from_dim = sanitize_name(from_col, config)
                    to_dim = sanitize_name(to_col, config)
                    sql_on_parts.append(f"${{{view_name}.{from_dim}}} = ${{{to_view}.{to_dim}}}")
            if not sql_on_parts:
                continue
            join_type = _join_type_to_looker(rel.join_type, config)
            explore["joins"].append({
                "name": to_view,
                "view": to_view,
                "type": join_type,
                "sql_on": " AND ".join(sql_on_parts),
                "relationship": "many_to_one",
            })
        explores.append(explore)

    return {
        "connection": connection_name,
        "explores": explores,
    }
