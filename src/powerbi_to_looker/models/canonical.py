"""Canonical data model: multi-BI source-agnostic schema (MetadataModel, Datasource, Field, etc.)."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Connection(BaseModel):
    type: str  # live, extract, direct_query
    server: str
    database: str
    schema: Optional[str] = None
    connection_provider: Optional[str] = None  # e.g. bigquery, sql_server, snowflake; from M/source


class Table(BaseModel):
    id: str
    name: str
    schema: Optional[str] = None
    table_name: str
    table_type: Optional[str] = None  # "physical" | "calculated"
    formula: Optional[str] = None  # DAX expression for calculated tables (for later conversion to SQL/LookML)
    extended_properties: Optional[dict] = None  # e.g. isHidden, hierarchies


class TableRelationship(BaseModel):
    from_table: str
    to_table: str
    join_type: str  # INNER, LEFT, RIGHT, FULL, CROSS
    on_columns: List[dict]  # [{"from": "customer_id", "to": "customer_id"}]


class Field(BaseModel):
    id: str
    name: str
    field_type: str  # dimension, measure, calculated_field
    data_type: Optional[str] = None  # string, number, date, datetime, boolean; None when unknown
    source_table: Optional[str] = None
    source_column: Optional[str] = None
    aggregation: Optional[str] = None  # SUM, AVG, COUNT, MIN, MAX
    formula: Optional[str] = None
    depends_on: Optional[List[str]] = None
    is_calculated: Optional[bool] = None  # True when field has formula (e.g. calculated measure)
    extended_properties: Optional[dict] = None  # e.g. format_string, lineageTag


class Parameter(BaseModel):
    id: str
    name: str
    data_type: str
    default_value: Optional[str] = None


class Datasource(BaseModel):
    id: str
    name: str
    source_system: str
    datasource_type: str  # embedded, published, shared
    connection: Connection
    tables: List[Table]
    table_relationships: List[TableRelationship]
    fields: List[Field]
    parameters: List[Parameter] = []
    extended_properties: Optional[dict] = None


class CrossDatasourceRelationship(BaseModel):
    relationship_type: str  # blend, union, join
    primary_datasource_id: str
    secondary_datasource_id: str
    blend_fields: List[dict]  # [{"primary_field_id": "fld_1", "secondary_field_id": "fld_2"}]


class MetadataModel(BaseModel):
    metadata_version: str = "1.0"
    source_system: str
    extracted_at: datetime
    datasources: List[Datasource]
    cross_datasource_relationships: List[CrossDatasourceRelationship] = []
