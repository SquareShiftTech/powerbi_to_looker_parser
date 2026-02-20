"""Semantic orchestrator: run handlers (tables, dimension, measure, calc_field), merge fields, build MetadataModel."""

from datetime import datetime, timezone
from typing import Any

from powerbi_to_looker.models.canonical import (
    Datasource,
    MetadataModel,
    Parameter,
)
from powerbi_to_looker.parser_normalizer.semantic import calc_field, dimension, measure, tables


def run(raw: dict[str, Any]) -> MetadataModel:
    """
    Build canonical MetadataModel from raw. Sends full raw to each handler.
    Dimension = no formula. Measure = summarizeBy only (no formula). Calc_field = all formulas emitted as dimension or measure with is_calculated=True.
    Merges dimension + measure + calc_field into one fields list.
    """
    model_obj = raw.get("model") or raw
    db_name = model_obj.get("name", "unknown") if isinstance(model_obj, dict) else "unknown"
    ds_id = db_name.replace(" ", "_").strip() or "datasource"

    tables_result = None
    if tables.can_handle(raw):
        tables_result = tables.run(raw)
    else:
        raise ValueError("Raw model has no tables; cannot build MetadataModel")

    all_fields = []
    if dimension.can_handle(raw):
        all_fields.extend(dimension.run(raw))
    if measure.can_handle(raw):
        all_fields.extend(measure.run(raw))
    if calc_field.can_handle(raw):
        all_fields.extend(calc_field.run(raw))

    datasource = Datasource(
        id=ds_id,
        name=db_name,
        source_system="powerbi",
        datasource_type="embedded",
        connection=tables_result.connection,
        tables=tables_result.tables,
        table_relationships=tables_result.table_relationships,
        fields=all_fields,
        parameters=[],
        extended_properties=None,
    )

    return MetadataModel(
        metadata_version="1.0",
        source_system="powerbi",
        extracted_at=datetime.now(timezone.utc),
        datasources=[datasource],
        cross_datasource_relationships=[],
    )
