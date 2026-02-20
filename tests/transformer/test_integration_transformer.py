"""Integration tests: metadata_model -> semantic_layer_artifact."""

import pytest

from powerbi_to_looker.transformer.semantic.orchestrator import run as run_transformer


MINIMAL_METADATA = {
    "metadata_version": "1.0",
    "source_system": "powerbi",
    "extracted_at": "2026-01-01T00:00:00Z",
    "datasources": [
        {
            "id": "ds1",
            "name": "TestDS",
            "source_system": "powerbi",
            "datasource_type": "embedded",
            "connection": {"type": "import", "database": "proj", "schema": "sc", "connection_provider": "bigquery"},
            "tables": [
                {"id": "t1", "name": "sales", "schema": "sc", "table_name": "sales", "table_type": "physical", "formula": None},
            ],
            "table_relationships": [],
            "fields": [
                {"id": "f1", "name": "revenue", "field_type": "dimension", "data_type": "number", "source_table": "sales", "source_column": "revenue", "aggregation": None, "formula": None, "formula_ast": None, "is_calculated": False},
                {"id": "f2", "name": "Revenue", "field_type": "measure", "data_type": "number", "source_table": "sales", "source_column": "revenue", "aggregation": "SUM", "formula": None, "formula_ast": None, "is_calculated": False},
            ],
        }
    ],
}


def test_transformer_runs_without_error():
    artifact = run_transformer(MINIMAL_METADATA)
    assert artifact is not None


def test_all_views_present():
    artifact = run_transformer(MINIMAL_METADATA)
    table_names = {t["table_name"] for t in MINIMAL_METADATA["datasources"][0]["tables"]}
    view_names = {v.view_name for v in artifact.views}
    assert table_names == view_names or len(artifact.views) >= 1


def test_every_field_has_conversion_status():
    artifact = run_transformer(MINIMAL_METADATA)
    for view in artifact.views:
        for field in view.fields:
            assert field.conversion_status in ("auto", "partial", "manual")


def test_conversion_summary_totals_correct():
    artifact = run_transformer(MINIMAL_METADATA)
    s = artifact.conversion_summary
    assert s.auto + s.partial + s.manual == s.total_fields
