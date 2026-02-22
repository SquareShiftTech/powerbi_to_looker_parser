"""Build artifact explores from metadata: one explore per physical table, joins from table_relationships."""

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


def build_explores(
    tables: list[dict[str, Any]],
    table_relationships: list[dict[str, Any]],
    views: list[Any],
) -> list[ArtifactExplore]:
    """One explore per physical table. Joins from table_relationships; relationship default many_to_one, conversion_status partial."""
    join_map = _join_type_map()
    reserved = _reserved_words()
    table_to_view: dict[str, str] = {v.source_table: v.view_name for v in views}

    explores: list[ArtifactExplore] = []
    for t in tables:
        table_name = (t.get("table_name") or t.get("name") or "").strip()
        if not table_name:
            continue
        if (t.get("table_type") or "physical").strip().lower() != "physical":
            continue
        view_name = table_to_view.get(table_name)
        if not view_name:
            continue
        label = (t.get("name") or table_name).strip()
        joins: list[ArtifactJoin] = []
        for rel in table_relationships:
            from_t = (rel.get("from_table") or "").strip()
            to_t = (rel.get("to_table") or "").strip()
            if from_t != table_name:
                continue
            to_view = table_to_view.get(to_t)
            if not to_view:
                continue
            join_type_raw = (rel.get("join_type") or "LEFT").strip().upper()
            join_type = join_map.get(join_type_raw) or "left_outer"
            on_cols = rel.get("on_columns") or []
            if not on_cols:
                continue
            parts = []
            for oc in on_cols:
                f_col = (oc.get("from") or "").strip()
                t_col = (oc.get("to") or "").strip()
                if f_col and t_col:
                    parts.append(f"${{{view_name}.{f_col}}} = ${{{to_view}.{t_col}}}")
            sql_on = " AND ".join(parts) if parts else ""
            if not sql_on:
                continue
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
        explores.append(
            ArtifactExplore(
                explore_name=view_name,
                label=label,
                description=None,
                joins=joins,
            )
        )
    return explores
