"""Map queryState + sortDefinition to canonical DataMapping. mapping_role from projection (Measure->measure, Column->role from config)."""

from typing import Any

from powerbi_to_looker.models.dashboard import DataMapping
from powerbi_to_looker.parser_normalizer.dashboard.config import get_query_state_role_for_column, get_viz_config


def _resolve_field_from_projection(proj: dict[str, Any]) -> tuple[str | None, str | None, bool]:
    """
    Resolve datasource_id and field_id from a projection.
    Returns (datasource_id, field_id, is_measure).
    """
    field_obj = proj.get("field")
    if not isinstance(field_obj, dict):
        return None, None, False
    # Measure: field.Measure.Expression.SourceRef.Entity + .Property
    if "Measure" in field_obj:
        m = field_obj["Measure"]
        expr = (m or {}).get("Expression") or {}
        ref = expr.get("SourceRef") or {}
        entity = ref.get("Entity")
        prop = (m or {}).get("Property")
        if entity and prop:
            return str(entity), str(prop), True
        # queryRef fallback: "table.field"
        qref = proj.get("queryRef") or proj.get("nativeQueryRef")
        if isinstance(qref, str) and "." in qref:
            a, _, b = qref.partition(".")
            return a.strip(), b.strip(), True
        return None, None, True
    # Column: field.Column.Expression.SourceRef.Entity + .Property
    if "Column" in field_obj:
        c = field_obj["Column"]
        expr = (c or {}).get("Expression") or {}
        ref = expr.get("SourceRef") or {}
        entity = ref.get("Entity")
        prop = (c or {}).get("Property")
        if entity and prop:
            return str(entity), str(prop), False
        qref = proj.get("queryRef") or proj.get("nativeQueryRef")
        if isinstance(qref, str) and "." in qref:
            a, _, b = qref.partition(".")
            return a.strip(), b.strip(), False
    return None, None, False


def _direction_to_sort_order(direction: str) -> str | None:
    if not direction:
        return None
    d = str(direction).lower()
    if d == "descending" or d == "desc":
        return "desc"
    if d == "ascending" or d == "asc":
        return "asc"
    return None


def build_data_mappings(
    query_state: dict[str, Any],
    sort_definition: dict[str, Any] | None,
    config: dict[str, Any] | None,
) -> list[DataMapping]:
    """
    Build canonical DataMapping list from queryState and optional sortDefinition.
    Only processes queryState keys that are in config query_state_roles.
    mapping_role: Measure projection -> measure; Column projection -> role from query_state_roles[key].
    """
    if config is None:
        config = get_viz_config()
    roles_map = (config.get("query_state_roles") or {})
    out: list[DataMapping] = []
    # Collect (datasource_id, field_id) -> index in out for applying sort_order
    key_to_indices: dict[tuple[str, str], list[int]] = {}

    for qkey, role_spec in (query_state or {}).items():
        if qkey not in roles_map:
            continue
        projections = (role_spec or {}).get("projections") or []
        column_role = roles_map[qkey]  # dimension | grouping | tooltip | detail | label

        for proj in projections:
            ds_id, field_id, is_measure = _resolve_field_from_projection(proj)
            if not ds_id or not field_id:
                continue
            if is_measure:
                mapping_role = "measure"
            else:
                mapping_role = column_role
            dm = DataMapping(
                field_id=field_id,
                datasource_id=ds_id,
                mapping_role=mapping_role,
                aggregation=None,
                sort_order=None,
            )
            idx = len(out)
            out.append(dm)
            key_to_indices.setdefault((ds_id, field_id), []).append(idx)

    # Apply sortDefinition to matching DataMapping
    if sort_definition:
        sort_list = (sort_definition.get("sort") or [])
        for sort_entry in sort_list:
            field_obj = (sort_entry or {}).get("field")
            if not field_obj:
                continue
            # Same structure as projection: Measure or Column with Expression.SourceRef.Entity + Property
            ds_id, field_id = None, None
            if "Measure" in field_obj:
                m = field_obj["Measure"]
                expr = (m or {}).get("Expression") or {}
                ref = expr.get("SourceRef") or {}
                ds_id = ref.get("Entity")
                field_id = (m or {}).get("Property")
            elif "Column" in field_obj:
                c = field_obj["Column"]
                expr = (c or {}).get("Expression") or {}
                ref = expr.get("SourceRef") or {}
                ds_id = ref.get("Entity")
                field_id = (c or {}).get("Property")
            if not ds_id or not field_id:
                continue
            direction = (sort_entry or {}).get("direction")
            sort_order = _direction_to_sort_order(direction) if direction else None
            for idx in key_to_indices.get((str(ds_id), str(field_id)), []):
                out[idx].sort_order = sort_order

    return out
