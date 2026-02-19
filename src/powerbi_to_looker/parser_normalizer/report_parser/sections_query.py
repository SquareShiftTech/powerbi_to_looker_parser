"""Build definition-style queryState and sortDefinition from sections config (prototypeQuery + projections)."""

from typing import Any


def _entity_and_property_from_expression(expr: dict[str, Any], from_by_name: dict[str, str]) -> tuple[str, str] | None:
    """From a Select expression (Column or Aggregation), get (Entity, Property)."""
    if not expr:
        return None
    # Column wrapper: { Column: { Expression: { SourceRef: { Source } }, Property } }
    if "Column" in expr:
        col = expr["Column"]
        prop = col.get("Property") or ""
        src = (col.get("Expression") or {}).get("SourceRef") or {}
        source_name = src.get("Source")
        if source_name is None:
            return None
        entity = from_by_name.get(source_name, source_name)
        return (entity, prop)
    # Bare column shape (inside Aggregation): { Expression: { SourceRef: { Source } }, Property }
    if "Expression" in expr and "Property" in expr and "Aggregation" not in expr:
        src = (expr.get("Expression") or {}).get("SourceRef") or {}
        source_name = src.get("Source")
        if source_name is None:
            return None
        entity = from_by_name.get(source_name, source_name)
        return (entity, expr.get("Property") or "")
    # Aggregation: { Expression: { Column: { ... } }, Function: 0 }
    if "Aggregation" in expr:
        agg = expr["Aggregation"]
        inner = agg.get("Expression")
        if not inner or "Column" not in inner:
            return None
        return _entity_and_property_from_expression(inner["Column"], from_by_name)
    return None


def _build_from_by_name(prototype: dict[str, Any]) -> dict[str, str]:
    """From prototypeQuery.From list, build Name -> Entity."""
    from_list = prototype.get("From") or []
    return {item["Name"]: item["Entity"] for item in from_list if isinstance(item, dict) and "Name" in item and "Entity" in item}


def _select_entry_to_field(sel: dict[str, Any], from_by_name: dict[str, str]) -> dict[str, Any] | None:
    """One Select entry -> definition field (Column or Measure)."""
    name = sel.get("Name")
    if name is None:
        return None
    if "Column" in sel:
        pair = _entity_and_property_from_expression(sel, from_by_name)
        if not pair:
            return None
        entity, prop = pair
        return {
            "field": {
                "Column": {
                    "Expression": {"SourceRef": {"Entity": entity}},
                    "Property": prop,
                }
            },
            "queryRef": name,
            "active": sel.get("active", True),
        }
    if "Aggregation" in sel:
        pair = _entity_and_property_from_expression(sel, from_by_name)
        if not pair:
            return None
        entity, prop = pair
        return {
            "field": {
                "Measure": {
                    "Expression": {"SourceRef": {"Entity": entity}},
                    "Property": prop,
                }
            },
            "queryRef": name,
        }
    return None


def _name_to_select_index(prototype: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map Select[].Name -> full Select entry."""
    select_list = prototype.get("Select") or []
    out: dict[str, dict[str, Any]] = {}
    for item in select_list:
        if isinstance(item, dict) and item.get("Name") is not None:
            out[item["Name"]] = item
    return out


def build_query_state(projections: dict[str, Any], prototype_query: dict[str, Any]) -> dict[str, Any]:
    """Build definition-style queryState from singleVisual.projections and prototypeQuery."""
    from_by_name = _build_from_by_name(prototype_query)
    name_to_select = _name_to_select_index(prototype_query)
    query_state: dict[str, Any] = {}
    for role, items in (projections or {}).items():
        if not isinstance(items, list):
            continue
        projs: list[dict[str, Any]] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            query_ref = it.get("queryRef")
            if not query_ref:
                continue
            sel = name_to_select.get(query_ref)
            if not sel:
                continue
            field_entry = _select_entry_to_field(sel, from_by_name)
            if field_entry:
                projs.append(field_entry)
        if projs:
            query_state[role] = {"projections": projs}
    return query_state


def _order_by_to_sort_def(order_by: list[Any], prototype_query: dict[str, Any]) -> dict[str, Any] | None:
    """Build sortDefinition from prototypeQuery.OrderBy."""
    if not order_by:
        return None
    from_by_name = _build_from_by_name(prototype_query)
    sort_list: list[dict[str, Any]] = []
    for ob in order_by:
        if not isinstance(ob, dict):
            continue
        direction = ob.get("Direction", 0)
        direction_str = "Descending" if direction == 2 else "Ascending"
        expr = ob.get("Expression")
        if not expr:
            continue
        # Expression can be Column or Aggregation (same shape as Select)
        if "Column" in expr:
            pair = _entity_and_property_from_expression(expr, from_by_name)
            if pair:
                entity, prop = pair
                sort_list.append({
                    "field": {
                        "Column": {
                            "Expression": {"SourceRef": {"Entity": entity}},
                            "Property": prop,
                        }
                    },
                    "direction": direction_str,
                })
        elif "Aggregation" in expr:
            pair = _entity_and_property_from_expression(expr, from_by_name)
            if pair:
                entity, prop = pair
                sort_list.append({
                    "field": {
                        "Measure": {
                            "Expression": {"SourceRef": {"Entity": entity}},
                            "Property": prop,
                        }
                    },
                    "direction": direction_str,
                })
    if not sort_list:
        return None
    return {
        "sort": sort_list,
        "isDefaultSort": True,
    }


def build_sort_definition(prototype_query: dict[str, Any]) -> dict[str, Any] | None:
    """Build definition-style sortDefinition from prototypeQuery.OrderBy."""
    order_by = prototype_query.get("OrderBy") or []
    return _order_by_to_sort_def(order_by, prototype_query)


def build_visual_query(config: dict[str, Any]) -> dict[str, Any]:
    """Build visual.query (queryState + sortDefinition) from config singleVisual.projections and prototypeQuery."""
    single = config.get("singleVisual") or {}
    projections = single.get("projections") or {}
    prototype = single.get("prototypeQuery") or config.get("prototypeQuery") or {}
    query_state = build_query_state(projections, prototype)
    sort_def = build_sort_definition(prototype)
    out: dict[str, Any] = {}
    if query_state:
        out["queryState"] = query_state
    if sort_def:
        out["sortDefinition"] = sort_def
    return out
