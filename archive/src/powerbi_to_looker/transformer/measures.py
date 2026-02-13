"""Canonical Field -> LookML measure entry."""

from typing import Any

from powerbi_to_looker.models.canonical import Field

from powerbi_to_looker.transformer.dimensions import sanitize_name


def field_to_measure(
    field: Field,
    config: dict[str, Any],
    base_dimension_name: str | None = None,
) -> dict[str, Any]:
    """Build LookML measure dict from canonical Field. Uses YAML measure_types and measures defaults."""
    measure_types = config.get("measure_types") or {}
    measures_defaults = config.get("measures") or {}
    value_format = measures_defaults.get("value_format", "#,##0.00")
    reuse_base = measures_defaults.get("reuse_base_dimension", True)

    name = sanitize_name(field.name, config)
    label = field.name or name

    # LookML measure type from canonical aggregation
    agg = (field.aggregation or "").upper()
    lookml_measure_type = measure_types.get(agg) or measure_types.get("default", "number")

    # SQL: reuse base dimension if configured and we have one; else TABLE.column or placeholder
    if reuse_base and base_dimension_name:
        sql = f"${{{base_dimension_name}}}"
    elif field.source_column:
        sql = f"${{TABLE}}.{field.source_column}"
    elif field.formula:
        # Calculated measure: placeholder; formula_to_sql can replace later
        sql = "NULL"
        if not lookml_measure_type or lookml_measure_type == "number":
            lookml_measure_type = "number"
    else:
        sql = "NULL"

    out = {
        "name": name,
        "label": label,
        "type": lookml_measure_type,
        "sql": sql,
        "value_format": value_format,
    }
    if field.formula:
        out["description"] = f"DAX: {field.formula.strip()[:200]}"
    return out
