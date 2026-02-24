"""Semantic layer artifact: Transformer output and Generator input (views, explores, conversion summary)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field as PydanticField


class ArtifactField(BaseModel):
    """Single field in a view (dimension, dimension_group, or measure)."""

    field_name: str
    original_name: str
    field_type: str  # dimension | dimension_group | measure
    looker_type: str  # string, number, yesno, time, sum, average, count, count_distinct, min, max
    label: str
    description: str | None = None
    sql: str
    value_format: str | None = None
    timeframes: list[str] | None = None  # for dimension_group: raw, time, date, week, month, quarter, year
    hidden: bool = False
    tags: list[str] = []
    conversion_status: str  # auto | partial | manual
    message: str | None = None
    original_formula: str | None = None
    bq_formula: str | None = None
    # two_step = hidden dimension + measure (aggregation set); one_step = single measure (model measure, no aggregation)
    measure_pattern: str | None = None  # "two_step" | "one_step" for measures; None for dimensions


class ArtifactView(BaseModel):
    """One view (table) in the artifact."""

    view_name: str
    label: str
    source_table: str
    view_type: str  # physical | calculated
    sql_table_name: str | None = None  # `project.schema.table` for physical
    derived_table_sql: str | None = None  # for calculated tables
    conversion_status: str = "auto"
    message: str | None = None
    fields: list[ArtifactField] = []


class ArtifactJoin(BaseModel):
    """One join in an explore."""

    join_name: str
    join_type: str  # left_outer, inner, full_outer, right_outer
    relationship: str  # many_to_one, one_to_one, etc.
    sql_on: str
    conversion_status: str = "partial"
    message: str | None = None


class ArtifactExplore(BaseModel):
    """One explore (base table + joins)."""

    explore_name: str
    label: str
    description: str | None = None
    joins: list[ArtifactJoin] = []


class ConversionSummary(BaseModel):
    """Counts of auto/partial/manual and list of manual fields for reporting."""

    total_fields: int = 0
    auto: int = 0
    partial: int = 0
    manual: int = 0
    manual_fields: list[dict[str, Any]] = []  # [{"view_name": "...", "field_name": "...", "message": "..."}]


class SemanticLayerArtifact(BaseModel):
    """Full semantic layer artifact: Transformer output, Generator input."""

    artifact_version: str = "1.0"
    source: str = "powerbi"
    target: str = "looker"
    generated_at: datetime = PydanticField(default_factory=datetime.utcnow)
    project_name: str
    database: str
    schema: str
    views: list[ArtifactView] = []
    explores: list[ArtifactExplore] = []
    conversion_summary: ConversionSummary = PydanticField(default_factory=ConversionSummary)
