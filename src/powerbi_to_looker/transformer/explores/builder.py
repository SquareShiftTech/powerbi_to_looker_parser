"""Build artifact explores from metadata: one explore per fact table, joins from table_relationships (direct + transitive)."""

from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml
from powerbi_to_looker.models.artifact import ArtifactExplore, ArtifactJoin
from powerbi_to_looker.transformer.views.field_cleanup import clean_field_name

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "field_type_mapping.yaml"
_RESERVED_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "looker_reserved_words.yaml"


def _join_type_map() -> dict[str, str]:
    try:
        cfg = load_yaml(_CONFIG_PATH)
        return cfg.get("join_type_map") or {}
    except FileNotFoundError:
        return {"LEFT": "left_outer", "INNER": "inner", "RIGHT": "right_outer", "FULL": "full_outer"}


def _reserved_words() -> set[str]:
    try:
        cfg = load_yaml(_RESERVED_PATH)
        return set(cfg.get("reserved_words") or [])
    except FileNotFoundError:
        return set()


def _view_name_from_table(table_name: str, reserved: set[str]) -> str:
    return clean_field_name(table_name, reserved)


def _is_hidden_table(tables: list[dict[str, Any]], table_name: str) -> bool:
    tbl = next(
        (t for t in tables if (t.get("table_name") or t.get("name") or "").strip() == table_name),
        None,
    )
    if not tbl:
        return False
    ext = tbl.get("extended_properties") or {}
    return bool(ext.get("isHidden", False))


def _build_sql_on(
    from_view: str,
    to_view: str,
    on_cols: list[dict[str, Any]],
    view_field_map: dict[tuple[str, str], str],
) -> str:
    """Build sql_on using view field names (single source of truth from views)."""
    parts = []
    for oc in on_cols:
        f_col = (oc.get("from") or oc.get("fromColumn") or "").strip()
        t_col = (oc.get("to") or oc.get("toColumn") or "").strip()
        if not f_col or not t_col:
            continue
        from_field = view_field_map.get((from_view, f_col)) or f_col
        to_field = view_field_map.get((to_view, t_col)) or t_col
        parts.append(f"${{{from_view}.{from_field}}} = ${{{to_view}.{to_field}}}")
    return " AND ".join(parts) if parts else ""


def _build_joins_for_fact(
    fact_table_name: str,
    fact_view_name: str,
    tables: list[dict[str, Any]],
    table_relationships: list[dict[str, Any]],
    table_to_view: dict[str, str],
    join_map: dict[str, str],
    view_field_map: dict[tuple[str, str], str],
) -> list[ArtifactJoin]:
    """Build all joins for a fact explore: direct + transitive (walk outgoing relationships from each joined table)."""
    joins: list[ArtifactJoin] = []
    joined_views: set[str] = {fact_view_name}
    # BFS: (intermediate_view_name, intermediate_table_name) from which we expand
    queue: list[tuple[str, str]] = [(fact_view_name, fact_table_name)]

    while queue:
        from_view, from_table = queue.pop(0)
        for rel in table_relationships:
            from_t = (rel.get("from_table") or rel.get("fromTable") or "").strip()
            to_t = (rel.get("to_table") or rel.get("toTable") or "").strip()
            if from_t != from_table:
                continue
            to_view = table_to_view.get(to_t)
            if not to_view or to_view in joined_views:
                continue
            if _is_hidden_table(tables, to_t):
                continue
            on_cols = rel.get("on_columns") or []
            if not on_cols:
                continue
            sql_on = _build_sql_on(from_view, to_view, on_cols, view_field_map)
            if not sql_on:
                continue
            join_type_raw = (rel.get("join_type") or "LEFT").strip().upper()
            join_type = join_map.get(join_type_raw) or "left_outer"
            joins.append(
                ArtifactJoin(
                    join_name=to_view,
                    join_type=join_type,
                    relationship="many_to_one",
                    sql_on=sql_on,
                    conversion_status="partial",
                    message="Relationship type defaulted to many_to_one - verify cardinality",
                )
            )
            joined_views.add(to_view)
            queue.append((to_view, to_t))

    return joins


def build_explores(
    tables: list[dict[str, Any]],
    table_relationships: list[dict[str, Any]],
    views: list[Any],
) -> list[ArtifactExplore]:
    """One explore per fact table (never a to_table). Joins from table_relationships: direct + transitive."""
    to_tables = {(rel.get("to_table") or rel.get("toTable") or "").strip() for rel in table_relationships}
    fact_tables = [
        t
        for t in tables
        if (t.get("table_name") or t.get("name") or "").strip() not in to_tables
    ]

    join_map = _join_type_map()
    table_to_view: dict[str, str] = {v.source_table: v.view_name for v in views}

    # Single source of truth: (view_name, original_name) -> field_name from views
    # For dimension_group (date/time), use _date timeframe in joins
    view_field_map: dict[tuple[str, str], str] = {}
    for v in views:
        for f in v.fields:
            orig = (f.original_name or "").strip()
            if not orig:
                continue
            if f.field_type == "dimension_group":
                view_field_map[(v.view_name, orig)] = f.field_name + "_date"
            else:
                view_field_map[(v.view_name, orig)] = f.field_name

    explores: list[ArtifactExplore] = []
    for t in fact_tables:
        table_name = (t.get("table_name") or t.get("name") or "").strip()
        if not table_name:
            continue
        if (t.get("table_type") or "physical").strip().lower() != "physical":
            continue
        view_name = table_to_view.get(table_name)
        if not view_name:
            continue
        label = (t.get("name") or table_name).strip()
        joins = _build_joins_for_fact(
            table_name,
            view_name,
            tables,
            table_relationships,
            table_to_view,
            join_map,
            view_field_map,
        )
        explores.append(
            ArtifactExplore(
                explore_name=view_name,
                label=label,
                description=None,
                joins=joins,
            )
        )
    return explores
