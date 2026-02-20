"""Tests for parser_normalizer.semantic handlers and orchestrator."""

import pytest

from powerbi_to_looker.models.canonical import MetadataModel
from powerbi_to_looker.parser_normalizer.semantic import calc_field, dimension, measure, tables
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

# Raw with a column that has summarizeBy (measure, no formula)
RAW_WITH_SUMMARIZE_BY = {
    "model": {
        "name": "M",
        "model": {
            "tables": [
                {
                    "name": "T1",
                    "columns": [
                        {"name": "Amount", "dataType": "Double", "lineageTag": "a1", "summarizeBy": "sum"}
                    ],
                    "partitions": [{"name": "P1", "source": {"type": "m"}}],
                }
            ],
            "relationships": [],
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
    assert measure.can_handle(MINIMAL_RAW) is False
    assert measure.can_handle(RAW_WITH_SUMMARIZE_BY) is True


def test_measure_run_returns_fields():
    fields = measure.run(MINIMAL_RAW)
    assert len(fields) == 0
    fields = measure.run(RAW_WITH_SUMMARIZE_BY)
    assert len(fields) == 1
    assert fields[0].name == "Amount"
    assert fields[0].field_type == "measure"
    assert fields[0].formula is None
    assert fields[0].aggregation == "SUM"
    assert fields[0].is_calculated is False


def test_calc_field_can_handle():
    assert calc_field.can_handle(MINIMAL_RAW) is True
    assert calc_field.can_handle(RAW_WITH_SUMMARIZE_BY) is False


def test_calc_field_run_returns_formula_fields():
    fields = calc_field.run(MINIMAL_RAW)
    assert len(fields) == 1
    assert fields[0].name == "Total"
    assert fields[0].field_type == "measure"  # model measure -> measure + is_calculated
    assert fields[0].formula
    assert fields[0].is_calculated is True


def test_calc_field_run_sets_formula_ast_on_success():
    fields = calc_field.run(MINIMAL_RAW)
    total = next(f for f in fields if f.name == "Total")
    assert total.formula_ast is not None
    assert total.formula_parse_error is None
    # AST for SUM(T1[Amount]) is FunctionCall with name and args
    assert "name" in total.formula_ast
    assert total.formula_ast["name"] == "SUM"
    assert "args" in total.formula_ast


def test_calc_field_run_sets_formula_parse_error_on_invalid_dax():
    raw_invalid = {
        "model": {
            "name": "M",
            "model": {
                "tables": [
                    {
                        "name": "T1",
                        "measures": [
                            {"name": "Bad", "lineageTag": "bad", "expression": ["SUM(T1[  "]},
                        ],
                        "partitions": [{"name": "P1", "source": {"type": "m"}}],
                    }
                ],
                "relationships": [],
            },
        }
    }
    fields = calc_field.run(raw_invalid)
    assert len(fields) == 1
    assert fields[0].name == "Bad"
    assert fields[0].formula_ast is None
    assert fields[0].formula_parse_error is not None
    assert len(fields[0].formula_parse_error) > 0


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
    assert len(ds.fields) == 2  # one dimension (Col1), one measure with formula (Total)
    by_type = {f.field_type for f in ds.fields}
    assert "dimension" in by_type
    assert "measure" in by_type
    total_field = next(f for f in ds.fields if f.name == "Total")
    assert total_field.formula
    assert total_field.field_type == "measure"
    assert total_field.is_calculated is True
