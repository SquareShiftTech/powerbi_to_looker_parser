"""Tests for DAX AST -> BigQuery formula converter."""

import pytest

from powerbi_to_looker.transformer.semantic.formula_converter import convert, convert_with_status


def test_sum_direct_mapping():
    # Pydantic model_dump uses "type": "FunctionCall"
    ast = {"type": "FunctionCall", "name": "SUM", "args": [{"type": "ColumnRef", "table": "sales", "column": "Revenue"}]}
    assert "SUM" in convert(ast)
    assert "revenue" in convert(ast).lower()


def test_calculate_is_unsupported():
    ast = {"type": "FunctionCall", "name": "CALCULATE", "args": []}
    result = convert_with_status(ast)
    assert result["conversion_status"] == "manual"
    assert result["bq_formula"] is None
    assert "CALCULATE" in (result.get("message") or "")


def test_unknown_function_is_manual():
    ast = {"type": "FunctionCall", "name": "MADEUPFUNC", "args": []}
    result = convert_with_status(ast)
    assert result["conversion_status"] == "manual"
    assert "MADEUPFUNC" in (result.get("message") or "")


def test_unqualified_column_ref_uses_looker_syntax():
    ast = {"type": "ColumnRef", "table": None, "column": "Total Revenue"}
    result = convert(ast, resolution_map={"Total Revenue": "total_revenue"})
    assert result == "${total_revenue}"


def test_qualified_column_ref_uses_table_dot_column():
    ast = {"type": "ColumnRef", "table": "marketing_campaign_data", "column": "Revenue"}
    assert "marketing_campaign_data" in convert(ast)
    assert "revenue" in convert(ast).lower()


def test_blank_maps_to_null():
    ast = {"type": "FunctionCall", "name": "BLANK", "args": []}
    result = convert_with_status(ast)
    assert result["bq_formula"] == "NULL"
