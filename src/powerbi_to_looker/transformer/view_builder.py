"""Build one LookML view dict from a table and its fields."""

from typing import Any

from powerbi_to_looker.models.canonical import Field, Table

from powerbi_to_looker.transformer.dimensions import field_to_dimension, sanitize_name
from powerbi_to_looker.transformer.formula_to_sql import dax_to_lookml_sql
from powerbi_to_looker.transformer.measures import field_to_measure


def build_view(
    table: Table,
    fields: list[Field],
    config: dict[str, Any],
    sql_table_name: str | None = None,
) -> dict[str, Any]:
    """Build one view dict (view_name, sql_table_name, dimensions, measures) from a table and its fields."""
    view_name = sanitize_name(table.name, config)
    table_label = table.name or view_name
    dims: list[dict[str, Any]] = []
    meas: list[dict[str, Any]] = []

    # Track which dimensions we added so measures can reference them (base dimension)
    dimension_names: set[str] = set()

    # Dimensions first (field_type == dimension)
    for f in fields:
        if f.field_type != "dimension":
            continue
        # Heuristic: id column as primary_key when name is id (case-insensitive)
        primary = (f.name or "").strip().lower() == "id"
        dim = field_to_dimension(f, config, primary_key=primary)
        dims.append(dim)
        dimension_names.add(dim["name"])

    # Base dimensions for measures: if reuse_base_dimension and measure has source_column, ensure a dimension
    measures_defaults = config.get("measures") or {}
    reuse_base = measures_defaults.get("reuse_base_dimension", True)
    for f in fields:
        if f.field_type != "measure":
            continue
        if not reuse_base or not f.source_column:
            continue
        base_name = sanitize_name(f.source_column, config)
        if base_name in dimension_names:
            continue
        # Add a dimension for the base column so measure can reference it
        base_field = Field(
            id=f.id + "_base",
            name=f.source_column,
            field_type="dimension",
            data_type=f.data_type or "number",
            source_table=f.source_table,
            source_column=f.source_column,
            aggregation=None,
            formula=None,
            depends_on=None,
            is_calculated=None,
        )
        dims.append(field_to_dimension(base_field, config, primary_key=False))
        dimension_names.add(base_name)

    # All names in this view (dimensions + measures as we add them); used to avoid collisions
    used_names: set[str] = set(dimension_names)
    # Name map: display name -> LookML field name (for formula_to_sql refs like [Total Sales])
    # Measures get their final name in the loop below (with agg suffix when colliding)
    name_map: dict[str, str] = {d["label"]: d["name"] for d in dims}

    # Measures (calculated ones may get sql/type from formula_to_sql)
    for f in fields:
        if f.field_type != "measure":
            continue
        base_dim = sanitize_name(f.source_column, config) if (reuse_base and f.source_column) else None
        if base_dim and base_dim not in dimension_names:
            base_dim = None
        m = field_to_measure(f, config, base_dimension_name=base_dim)
        # Disambiguate measure name when it collides with a dimension or prior measure (suffix = LookML type, e.g. _sum, _count)
        candidate = m["name"]
        if candidate in used_names:
            candidate = m["name"] + "_" + m["type"]
            n = 2
            while candidate in used_names:
                candidate = m["name"] + "_" + m["type"] + "_" + str(n)
                n += 1
        m["name"] = candidate
        used_names.add(candidate)
        # Prefer dimension in name_map so formulas like [Quantity] resolve to ${quantity} not ${quantity_sum}
        if f.name not in name_map:
            name_map[f.name] = candidate
        if f.formula:
            sql, mtype = dax_to_lookml_sql(f.formula, name_map, config)
            if sql:
                m["sql"] = sql
                if mtype:
                    m["type"] = mtype
                if "description" in m:
                    del m["description"]
        meas.append(m)

    # Placeholder if empty
    if not dims:
        dims = [{
            "name": "id",
            "label": "ID",
            "type": "string",
            "sql": "${TABLE}.id",
            "primary_key": "yes",
        }]
    if not meas:
        meas = [{
            "name": "count",
            "label": "Count",
            "type": "count",
            "sql": "*",
            "value_format": "#,##0",
            "format": "decimal_2",
        }]

    out = {
        "view_name": view_name,
        "dimensions": dims,
        "measures": meas,
    }
    if sql_table_name is not None:
        out["sql_table_name"] = sql_table_name
    else:
        out["sql_table_name"] = view_name
    return out
