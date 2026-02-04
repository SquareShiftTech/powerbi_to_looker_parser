"""Canonical Field -> LookML dimension entry."""

from typing import Any

from powerbi_to_looker.models.canonical import Field

from powerbi_to_looker.transformer.dates import (
    dimension_sql_for_date,
    get_date_info,
    is_date_field,
)


def sanitize_name(name: str, config: dict[str, Any]) -> str:
    """Sanitize for LookML: lowercase, spaces to underscores; optional truncate."""
    if not name:
        return "field"
    s = name.replace(" ", "_").lower()
    for c in s:
        if c != "_" and not c.isalnum():
            s = s.replace(c, "_")
    naming = config.get("naming") or {}
    if naming.get("sanitize"):
        s = "".join(c if c.isalnum() or c == "_" else "_" for c in s)
    max_len = naming.get("max_name_length") or 64
    return s[:max_len] if len(s) > max_len else s


def field_to_dimension(
    field: Field,
    config: dict[str, Any],
    primary_key: bool = False,
) -> dict[str, Any]:
    """Build LookML dimension dict from canonical Field. Uses YAML dimension_types and date_handling."""
    dim_types = config.get("dimension_types") or {}
    dtype = (field.data_type or "string").lower()
    lookml_type = dim_types.get(dtype, "string")

    name = sanitize_name(field.name, config)
    label = field.name or name
    source_col = field.source_column or field.name

    if is_date_field(field.data_type):
        sql = dimension_sql_for_date(source_col, field.name, config)
        date_info = get_date_info(field.data_type, config)
    else:
        sql = f"${{TABLE}}.{source_col}" if source_col else f"${{TABLE}}.id"
        date_info = None

    out = {
        "name": name,
        "label": label,
        "type": lookml_type,
        "sql": sql,
    }
    if primary_key:
        out["primary_key"] = "yes"
    if date_info:
        out["date_info"] = date_info
    return out
