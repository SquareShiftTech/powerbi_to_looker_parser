"""Tests for transformer modules: dimensions, measures, dates, formula_to_sql, view_builder, model_builder, semantic_layer."""

import pytest
from datetime import datetime, timezone

from powerbi_to_looker.models.canonical import (
    Connection,
    Datasource,
    Field,
    MetadataModel,
    Table,
    TableRelationship,
)
from powerbi_to_looker.transformer.dates import get_date_info, is_date_field
from powerbi_to_looker.transformer.dimensions import field_to_dimension, sanitize_name
from powerbi_to_looker.transformer.formula_to_sql import dax_to_lookml_sql
from powerbi_to_looker.transformer.measures import field_to_measure
from powerbi_to_looker.transformer.model_builder import build_model
from powerbi_to_looker.transformer.semantic_layer import to_lookml_terms
from powerbi_to_looker.transformer.view_builder import build_view


# --- Config fixture ---
@pytest.fixture
def config():
    return {
        "dimension_types": {"string": "string", "number": "number", "date": "time", "datetime": "time"},
        "measure_types": {"SUM": "sum", "AVG": "avg", "COUNT": "count", "default": "number"},
        "join_types": {"LEFT": "left_outer", "default": "left_outer"},
        "date_handling": {"datetype": "date", "timeframes": ["day", "week", "month"]},
        "measures": {"value_format": "#,##0.00", "format": "decimal_2", "reuse_base_dimension": True},
        "naming": {"max_name_length": 64, "sanitize": True},
    }


# --- dimensions ---
def test_sanitize_name(config):
    assert sanitize_name("Order Date", config) == "order_date"
    assert sanitize_name("Total Sales", config) == "total_sales"


def test_field_to_dimension(config):
    f = Field(
        id="t.col",
        name="Order Date",
        field_type="dimension",
        data_type="datetime",
        source_table="Orders",
        source_column="Order_Date",
        aggregation=None,
        formula=None,
        depends_on=None,
        is_calculated=None,
    )
    d = field_to_dimension(f, config, primary_key=False)
    assert d["name"] == "order_date"
    assert d["label"] == "Order Date"
    assert d["type"] == "time"
    assert "order_date" in d["sql"] or "Order_Date" in d["sql"]
    assert d.get("date_info") is not None


def test_field_to_dimension_primary_key(config):
    f = Field(id="t.id", name="id", field_type="dimension", data_type="string", source_table="t", source_column="id", aggregation=None, formula=None, depends_on=None, is_calculated=None)
    d = field_to_dimension(f, config, primary_key=True)
    assert d["primary_key"] == "yes"


# --- measures ---
def test_field_to_measure_simple(config):
    f = Field(id="t.sales", name="Total Sales", field_type="measure", data_type="number", source_table="t", source_column="sales", aggregation="SUM", formula=None, depends_on=None, is_calculated=None)
    m = field_to_measure(f, config, base_dimension_name="sales")
    assert m["name"] == "total_sales"
    assert m["type"] == "sum"
    assert m["sql"] == "${sales}"


def test_field_to_measure_calculated(config):
    f = Field(id="t.m", name="Margin", field_type="measure", data_type="number", source_table="t", source_column=None, aggregation="SUM", formula="DIVIDE([A],[B],0)", depends_on=None, is_calculated=True)
    m = field_to_measure(f, config, base_dimension_name=None)
    assert m["type"] in ("number", "sum")  # sum from aggregation; number when overridden by formula_to_sql
    assert "description" in m
    assert "DAX" in m["description"]


# --- dates ---
def test_is_date_field():
    assert is_date_field("date") is True
    assert is_date_field("datetime") is True
    assert is_date_field("string") is False


def test_get_date_info(config):
    info = get_date_info("date", config)
    assert info["datetype"] == "date"
    assert "day" in info["timeframes"]


# --- formula_to_sql ---
def test_formula_to_sql_divide(config):
    name_map = {"Total Profit": "total_profit", "Total Sales": "total_sales"}
    sql, mtype = dax_to_lookml_sql("DIVIDE ( [Total Profit], [Total Sales], 0 )", name_map, config)
    assert sql is not None
    assert "total_profit" in sql
    assert "total_sales" in sql
    assert "NULLIF" in sql
    assert mtype == "number"


def test_formula_to_sql_divide_bigquery(config):
    name_map = {"Total Profit": "total_profit", "Total Sales": "total_sales"}
    bigquery_config = {**config, "sql_dialect": "bigquery"}
    sql, mtype = dax_to_lookml_sql("DIVIDE ( [Total Profit], [Total Sales], 0 )", name_map, bigquery_config)
    assert sql is not None
    assert "total_profit" in sql
    assert "total_sales" in sql
    assert "SAFE_DIVIDE" in sql
    assert "IFNULL" in sql
    assert mtype == "number"


def test_formula_to_sql_sum(config):
    name_map = {"Sales": "sales"}
    sql, mtype = dax_to_lookml_sql("SUM ( Order_Details[Sales] )", name_map, config)
    assert sql is not None
    assert mtype == "sum"


def test_formula_to_sql_unmatched_returns_none(config):
    name_map = {}
    sql, mtype = dax_to_lookml_sql("RANKX(ALL(...), ...)", name_map, config)
    assert sql is None
    assert mtype is None


# --- view_builder ---
def test_build_view_empty_fields(config):
    table = Table(id="t1", name="Orders", schema=None, table_name="Orders")
    view = build_view(table, [], config)
    assert view["view_name"] == "orders"
    assert len(view["dimensions"]) >= 1
    assert len(view["measures"]) >= 1


def test_build_view_with_dimension_and_measure(config):
    table = Table(id="t1", name="Orders", schema=None, table_name="Orders")
    fields = [
        Field(id="t.order_id", name="Order_ID", field_type="dimension", data_type="string", source_table="Orders", source_column="Order_ID", aggregation=None, formula=None, depends_on=None, is_calculated=None),
        Field(id="t.sales", name="Sales", field_type="measure", data_type="number", source_table="Orders", source_column="sales", aggregation="SUM", formula=None, depends_on=None, is_calculated=None),
    ]
    view = build_view(table, fields, config)
    assert view["view_name"] == "orders"
    dim_names = [d["name"] for d in view["dimensions"]]
    assert "order_id" in dim_names or "sales" in dim_names  # base dim for sales
    meas = [m for m in view["measures"] if m["name"] == "sales"]
    assert len(meas) == 1
    assert meas[0]["sql"] == "${sales}"


# --- model_builder ---
def test_build_model_explores_and_joins(config):
    conn = Connection(type="direct", server="s", database="d", schema=None)
    tables = [
        Table(id="a", name="Orders", schema=None, table_name="Orders"),
        Table(id="b", name="Order_Details", schema=None, table_name="Order_Details"),
    ]
    rels = [
        TableRelationship(from_table="Orders", to_table="Order_Details", join_type="LEFT", on_columns=[{"from": "Order_ID", "to": "Order_ID"}]),
    ]
    ds = Datasource(id="ds1", name="DS", source_system="powerbi", datasource_type="embedded", connection=conn, tables=tables, table_relationships=rels, fields=[], parameters=[])
    model = build_model(ds, config)
    assert model["connection"] == "powerbi_connection"
    assert len(model["explores"]) == 2
    orders_exp = next(e for e in model["explores"] if e["name"] == "orders")
    assert len(orders_exp["joins"]) == 1
    assert orders_exp["joins"][0]["view"] == "order_details"
    assert "sql_on" in orders_exp["joins"][0]


# --- semantic_layer integration ---
def test_to_lookml_terms_returns_views_and_model():
    conn = Connection(type="direct", server="s", database="d", schema=None)
    ds = Datasource(
        id="ds1",
        name="DS",
        source_system="powerbi",
        datasource_type="embedded",
        connection=conn,
        tables=[Table(id="t1", name="Orders", schema=None, table_name="Orders")],
        table_relationships=[],
        fields=[],
        parameters=[],
    )
    metadata = MetadataModel(metadata_version="1.0", source_system="powerbi", extracted_at=datetime.now(timezone.utc), datasources=[ds], cross_datasource_relationships=[])
    result = to_lookml_terms(metadata)
    assert "views" in result
    assert "model" in result
    assert len(result["views"]) >= 1
    assert result["model"]["connection"] == "powerbi_connection"
    assert len(result["model"]["explores"]) >= 1
