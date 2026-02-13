"""Build canonical MetadataModel from raw Power BI metadata (collector output)."""

import re
from datetime import datetime, timezone
from typing import Any

from powerbi_to_looker.config import load_canonical_mapping
from powerbi_to_looker.models.canonical import (
    Connection,
    Datasource,
    Field,
    MetadataModel,
    Parameter,
    Table,
    TableRelationship,
)


def _parse_connection_from_power_query(raw: dict[str, Any]) -> tuple[str, str, str | None]:
    """Infer server, database, schema from power_query M if present. Else return defaults."""
    server, database, schema = "localhost", "default", None
    power_query = raw.get("power_query") or []
    for item in power_query:
        if not isinstance(item, dict):
            continue
        expr = item.get("Expression") or item.get("expression") or ""
        if not isinstance(expr, str):
            continue
        # Sql.Databases("server-name")
        m = re.search(r'Sql\.Databases\s*\(\s*["\']([^"\']+)["\']', expr)
        if m:
            server = m.group(1)
        # Schema="dbo"
        schema_m = re.search(r'Schema\s*=\s*["\']([^"\']+)["\']', expr)
        if schema_m:
            schema = schema_m.group(1)
        # Name="DBName" (e.g. Super_Store_Data) as database
        db_m = re.search(r'Name\s*=\s*["\']([^"\']+)["\']', expr)
        if db_m:
            database = db_m.group(1)
    return server, database, schema


def _build_tables(dataset: dict[str, Any]) -> list[Table]:
    """Build canonical Table list from dataset.tables."""
    tables: list[Table] = []
    for t in dataset.get("tables") or []:
        name = t.get("name")
        if not name:
            continue
        tables.append(
            Table(
                id=name,
                name=name,
                schema=None,
                table_name=name,
            )
        )
    return tables


def _build_relationships(
    raw: dict[str, Any],
    mapping: dict[str, Any],
) -> list[TableRelationship]:
    """Build TableRelationship list from raw relationships; skip null toTable/toColumn; dedupe; join_type from config."""
    rels = raw.get("relationships") or []
    join_type = (
        (mapping.get("relationship") or {})
        .get("join_type", {})
        .get("default")
        or (mapping.get("defaults") or {}).get("join_type")
        or "LEFT"
    )
    seen: set[tuple[str, str, str, str]] = set()
    out: list[TableRelationship] = []
    for r in rels:
        from_table = r.get("fromTable")
        from_col = r.get("fromColumn")
        to_table = r.get("toTable")
        to_col = r.get("toColumn")
        if not from_table or not from_col:
            continue
        if to_table is None or to_col is None:
            continue
        key = (str(from_table), str(from_col), str(to_table), str(to_col))
        if key in seen:
            continue
        seen.add(key)
        out.append(
            TableRelationship(
                from_table=from_table,
                to_table=to_table,
                join_type=join_type,
                on_columns=[{"from": from_col, "to": to_col}],
            )
        )
    return out


def _map_data_type(pbi_type: str | None, mapping: dict[str, Any]) -> str:
    """Map Power BI dataType to canonical data_type using config."""
    data_types = mapping.get("data_types") or {}
    default = (mapping.get("defaults") or {}).get("data_type", "string")
    if not pbi_type:
        return default
    return data_types.get(pbi_type, default)


def _map_column_type(pbi_column_type: str | None, mapping: dict[str, Any]) -> str:
    """Map Power BI columnType to canonical field_type (dimension | calculated_field)."""
    column_types = mapping.get("column_types") or {}
    default = "dimension"
    if not pbi_column_type:
        return default
    return column_types.get(pbi_column_type, default)


def _infer_aggregation_from_dax(expression: str | None, mapping: dict[str, Any]) -> str | None:
    """Best-effort infer canonical aggregation from DAX expression using config."""
    if not expression or not isinstance(expression, str):
        return None
    agg_map = mapping.get("measure_aggregation") or {}
    expr_upper = expression.upper()
    for dax_key, canonical_agg in agg_map.items():
        if dax_key == "default":
            continue
        if dax_key.upper() in expr_upper:
            return canonical_agg
    return agg_map.get("default")


def _build_fields(dataset: dict[str, Any], mapping: dict[str, Any]) -> list[Field]:
    """Build Field list: dimensions from columns, measures from measures. Uses config for data_type and field_type."""
    fields: list[Field] = []
    defaults = mapping.get("defaults") or {}
    default_data_type = defaults.get("data_type", "string")
    measure_data_type = defaults.get("measure_data_type", "number")
    measure_default_agg = defaults.get("measure_default_aggregation", "SUM")
    dimension_number_agg = defaults.get("dimension_number_aggregation", "SUM")

    for t in dataset.get("tables") or []:
        table_name = t.get("name")
        if not table_name:
            continue
        for col in t.get("columns") or []:
            col_name = col.get("name")
            if not col_name:
                continue
            field_id = f"{table_name}.{col_name}"
            pbi_data_type = col.get("dataType")
            pbi_column_type = col.get("columnType", "Data")
            canonical_data_type = _map_data_type(pbi_data_type, mapping)
            # Numeric columns get default aggregation and are treated as measures
            if canonical_data_type == "number":
                col_agg = dimension_number_agg
                col_field_type = "measure"
            else:
                col_agg = None
                col_field_type = _map_column_type(pbi_column_type, mapping)
            fields.append(
                Field(
                    id=field_id,
                    name=col_name,
                    field_type=col_field_type,
                    data_type=canonical_data_type,
                    source_table=table_name,
                    source_column=col_name,
                    aggregation=col_agg,
                    formula=None,
                    depends_on=None,
                    is_calculated=None,
                )
            )
        for meas in t.get("measures") or []:
            meas_name = meas.get("name")
            if not meas_name:
                continue
            field_id = f"{table_name}.{meas_name}"
            expression = meas.get("expression") or meas.get("Expression")
            formula_str = expression if isinstance(expression, str) else None
            agg = _infer_aggregation_from_dax(expression, mapping)
            if agg is None:
                agg = measure_default_agg
            fields.append(
                Field(
                    id=field_id,
                    name=meas_name,
                    field_type="measure",
                    data_type=measure_data_type,
                    source_table=table_name,
                    source_column=None,
                    aggregation=agg,
                    formula=formula_str,
                    depends_on=None,
                    is_calculated=formula_str is not None,
                )
            )

    return fields


def build_metadata_model(raw: dict[str, Any], mapping_path: str | None = None) -> MetadataModel:
    """Convert raw Power BI metadata to canonical MetadataModel.

    Populates datasource with tables, table_relationships, and fields from raw.
    Uses config YAML for data_types, column_types, relationship join_type, measure_aggregation.

    Args:
        raw: Raw metadata from collector.
        mapping_path: Optional path to Power BI canonical mapping YAML; default uses bundled config.

    Returns:
        Canonical MetadataModel.
    """
    mapping = load_canonical_mapping(mapping_path)

    source_system = raw.get("source_system", "powerbi")
    extracted_at = raw.get("extracted_at")
    if extracted_at is None:
        extracted_at = datetime.now(timezone.utc)
    elif isinstance(extracted_at, str):
        extracted_at = datetime.fromisoformat(extracted_at.replace("Z", "+00:00"))

    server, database, schema = _parse_connection_from_power_query(raw)
    connection = Connection(
        type="direct_query",
        server=server,
        database=database,
        schema=schema,
    )

    ds_id = raw.get("datasource_id", "ds_1")
    ds_name = raw.get("datasource_name") or raw.get("report_name", "Default")
    dataset: dict[str, Any] = {}
    for ws in raw.get("workspaces") or []:
        for ds in ws.get("datasets") or []:
            ds_id = ds.get("id", ds_id)
            ds_name = ds.get("name", ds_name)
            dataset = ds
            break
        if dataset:
            break

    tables = _build_tables(dataset) if dataset else []
    table_relationships = _build_relationships(raw, mapping)
    fields = _build_fields(dataset, mapping) if dataset else []
    parameters: list[Parameter] = []

    datasource = Datasource(
        id=ds_id,
        name=ds_name,
        source_system=source_system,
        datasource_type="embedded",
        connection=connection,
        tables=tables,
        table_relationships=table_relationships,
        fields=fields,
        parameters=parameters,
    )

    return MetadataModel(
        metadata_version="1.0",
        source_system=source_system,
        extracted_at=extracted_at,
        datasources=[datasource],
        cross_datasource_relationships=[],
    )
