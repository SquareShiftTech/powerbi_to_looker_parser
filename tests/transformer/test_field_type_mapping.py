"""Tests for Power BI -> Looker field type mapping."""

import pytest

from powerbi_to_looker.transformer.views.field_type_mapping import infer_measure_type_from_formula_ast, map_field_type


def test_string_maps_to_dimension():
    result = map_field_type(data_type="string", aggregation=None)
    assert result["field_type"] == "dimension"
    assert result["looker_type"] == "string"


def test_number_with_sum_maps_to_measure():
    result = map_field_type(data_type="number", aggregation="SUM")
    assert result["field_type"] == "measure"
    assert result["looker_type"] == "sum"


def test_number_with_distinctcount_maps_to_count_distinct():
    result = map_field_type(data_type="number", aggregation="DISTINCTCOUNT")
    assert result["field_type"] == "measure"
    assert result["looker_type"] == "count_distinct"


def test_datetime_maps_to_dimension_group():
    result = map_field_type(data_type="datetime", aggregation=None)
    assert result["field_type"] == "dimension_group"
    assert result["looker_type"] == "time"
    assert result["timeframes"] == ["raw", "time", "date", "week", "month", "quarter", "year"]


def test_boolean_maps_to_yesno():
    result = map_field_type(data_type="boolean", aggregation=None)
    assert result["looker_type"] == "yesno"


def test_unknown_data_type_falls_back_to_string():
    result = map_field_type(data_type="exotic_type", aggregation=None)
    assert result["looker_type"] == "string"
    assert result["conversion_status"] == "partial"


def test_infer_measure_type_from_formula_ast_count():
    ast = {"type": "FunctionCall", "name": "COUNT", "args": []}
    assert infer_measure_type_from_formula_ast(ast) == "count"


def test_infer_measure_type_from_formula_ast_sum():
    ast = {"name": "SUM"}
    assert infer_measure_type_from_formula_ast(ast) == "sum"


def test_infer_measure_type_from_formula_ast_unknown_returns_none():
    assert infer_measure_type_from_formula_ast({"name": "SOMETHING"}) is None
    assert infer_measure_type_from_formula_ast(None) is None
    assert infer_measure_type_from_formula_ast([]) is None
