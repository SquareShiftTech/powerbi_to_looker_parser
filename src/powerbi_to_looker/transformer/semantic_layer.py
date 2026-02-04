"""Transform canonical MetadataModel to LookML terms (views, explores) for semantic layer."""

from typing import Any

from powerbi_to_looker.config import load_lookml_mapping
from powerbi_to_looker.models.canonical import Datasource, MetadataModel

from powerbi_to_looker.transformer.model_builder import build_model
from powerbi_to_looker.transformer.view_builder import build_view


def to_lookml_terms(
    metadata: MetadataModel,
    config_path: str | None = None,
    connection_name: str = "powerbi_connection",
) -> dict[str, Any]:
    """Convert canonical MetadataModel to LookML semantic layer terms.

    Uses YAML config for dimension_types, measure_types, join_types, date_handling, measures, naming.
    One view per table; explores with joins from table_relationships.

    Args:
        metadata: Canonical metadata model.
        config_path: Optional path to canonical_lookml_mapping.yaml.
        connection_name: LookML connection name.

    Returns:
        Dict with keys: views (list of view dicts), model (dict with connection, explores).
    """
    config = load_lookml_mapping(config_path)
    views: list[dict[str, Any]] = []
    model: dict[str, Any] = {"connection": connection_name, "explores": []}

    for ds in metadata.datasources:
        # Group fields by source_table
        by_table: dict[str, list] = {}
        for f in ds.fields:
            t = f.source_table or ""
            if t not in by_table:
                by_table[t] = []
            by_table[t].append(f)

        # sql_table_name: BigQuery dataset.table (or project.dataset.table) when configured; else schema.table
        conn = ds.connection
        dialect = (config.get("sql_dialect") or "generic").lower()
        bq = config.get("bigquery") or {}
        if dialect == "bigquery" and bq.get("dataset"):
            dataset = bq["dataset"]
            project = bq.get("project")
            if project:
                prefix = f"{project}.{dataset}."
            else:
                prefix = f"{dataset}."
        else:
            prefix = f"{conn.schema}." if conn.schema else ""
        def sql_table(tname: str) -> str:
            return f"{prefix}{tname}" if prefix else tname

        # One view per table
        for table in ds.tables:
            table_fields = by_table.get(table.name) or []
            view = build_view(
                table,
                table_fields,
                config,
                sql_table_name=sql_table(table.table_name),
            )
            views.append(view)

        # Model: explores + joins (from first datasource that has tables; or merge later)
        if ds.tables and not model["explores"]:
            model = build_model(ds, config, connection_name=connection_name)

    if not views:
        views = [{
            "view_name": "sample_view",
            "sql_table_name": "sample_view",
            "dimensions": [
                {"name": "id", "label": "ID", "type": "string", "sql": "${TABLE}.id", "primary_key": "yes"},
            ],
            "measures": [
                {"name": "count", "label": "Count", "type": "count", "sql": "*", "value_format": "#,##0", "format": "decimal_2"},
            ],
        }]
    if not model.get("explores"):
        model["explores"] = [
            {"name": v["view_name"], "view": v["view_name"], "label": v["view_name"], "joins": []}
            for v in views
        ]

    return {
        "views": views,
        "model": model,
    }
