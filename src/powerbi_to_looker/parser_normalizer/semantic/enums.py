"""Enums for semantic mapping; validate YAML keys against these."""

from enum import Enum


class FieldType(str, Enum):
    """Canonical field_type. Must match config column_types / measure output."""

    DIMENSION = "dimension"
    MEASURE = "measure"
    CALCULATED_FIELD = "calculated_field"


class DataType(str, Enum):
    """Canonical data_type. Must match config data_types."""

    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class Aggregation(str, Enum):
    """Canonical aggregation. Must match config measure_aggregation / summarizeBy."""

    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"


class JoinType(str, Enum):
    """Canonical join_type. Must match config relationship.join_type."""

    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"
    CROSS = "CROSS"


class ConnectionProvider(str, Enum):
    """Datasource/connection provider from M or source. Must match config connection_provider."""

    BIGQUERY = "bigquery"
    SQL_SERVER = "sql_server"
    ODBC = "odbc"
    SNOWFLAKE = "snowflake"
    UNKNOWN = "unknown"
