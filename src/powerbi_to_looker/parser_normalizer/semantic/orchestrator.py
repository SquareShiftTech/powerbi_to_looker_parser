"""Semantic orchestrator: run handlers (tables, dimension, measure), merge fields, build MetadataModel."""

from datetime import datetime, timezone
from typing import Any

from powerbi_to_looker.models.canonical import (
    Datasource,
    MetadataModel,
    Parameter,
)
from powerbi_to_looker.parser_normalizer.semantic import dimension, measure, tables


def run(raw: dict[str, Any]) -> MetadataModel:
    """
    Build canonical MetadataModel from raw. Sends full raw to each handler.
    Merges dimension + measure fields into one list; tables handler supplies tables, relationships, connection.
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
    # Optional: apply calculated_field typing for any field with formula (already have is_calculated)
    # We keep dimension/measure field_type as-is; is_calculated and formula are set.

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
