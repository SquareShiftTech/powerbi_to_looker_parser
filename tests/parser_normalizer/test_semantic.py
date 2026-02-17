"""Tests for parser_normalizer.semantic handlers and orchestrator."""

import pytest

from powerbi_to_looker.models.canonical import MetadataModel
from powerbi_to_looker.parser_normalizer.semantic import dimension, measure, tables
from powerbi_to_looker.parser_normalizer.semantic.orchestrator import run as run_semantic


MINIMAL_RAW = {
    "model": {
        "name": "TestModel",
        "model": {
            "tables": [
                {
                    "name": "T1",
                    "lineageTag": "lt1",
                    "columns": [
                        {
                            "name": "Col1",
                            "dataType": "String",
                            "lineageTag": "c1",
                            "summarizeBy": "none",
                        }
                    ],
                    "measures": [
                        {
                            "name": "Total",
                            "lineageTag": "m1",
                            "expression": ["SUM(T1[Amount])"],
                        }
                    ],
                    "partitions": [
                        {
                            "name": "P1",
                            "mode": "import",
                            "source": {"type": "m", "expression": ["let", "Source = GoogleBigQuery.Database()", "in", "x"]},
                        }
                    ],
                }
            ],
            "relationships": [
                {"fromTable": "T1", "fromColumn": "Id", "toTable": "T2", "toColumn": "Id"}
            ],
        },
    }
}


def test_tables_can_handle():
    assert tables.can_handle(MINIMAL_RAW) is True
    assert tables.can_handle({}) is False
    assert tables.can_handle({"model": {"tables": []}}) is True


def test_tables_run_returns_tables_result():
    result = tables.run(MINIMAL_RAW)
    assert result.tables
    assert result.table_relationships
    assert result.connection
    assert result.connection.connection_provider == "bigquery"
    assert len(result.tables) == 1
    assert result.tables[0].name == "T1"
    assert len(result.table_relationships) == 1
    assert result.table_relationships[0].from_table == "T1"


def test_dimension_can_handle():
    assert dimension.can_handle(MINIMAL_RAW) is True


def test_dimension_run_returns_fields():
    fields = dimension.run(MINIMAL_RAW)
    assert len(fields) == 1
    assert fields[0].name == "Col1"
    assert fields[0].field_type == "dimension"
    assert fields[0].data_type == "string"


def test_measure_can_handle():
    assert measure.can_handle(MINIMAL_RAW) is True


def test_measure_run_returns_fields():
    fields = measure.run(MINIMAL_RAW)
    assert len(fields) == 1
    assert fields[0].name == "Total"
    assert fields[0].field_type == "measure"
    assert fields[0].formula
    assert fields[0].is_calculated is True


def test_orchestrator_run_returns_metadata_model():
    model = run_semantic(MINIMAL_RAW)
    assert isinstance(model, MetadataModel)
    assert model.metadata_version == "1.0"
    assert model.source_system == "powerbi"
    assert len(model.datasources) == 1
    ds = model.datasources[0]
    assert ds.name == "TestModel"
    assert len(ds.tables) == 1
    assert len(ds.table_relationships) == 1
    assert len(ds.fields) == 2  # one dimension, one measure
