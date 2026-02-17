"""Calculated-field handler: raw["model"] -> list[Field] with formula (calculated_field)."""

from typing import Any

from powerbi_to_looker.models.canonical import Field
from powerbi_to_looker.parser_normalizer.semantic import dimension, measure


def can_handle(raw: dict[str, Any]) -> bool:
    """Return True if raw model has any calculated columns or measures (with expression)."""
    model = raw.get("model") or raw
    if isinstance(model, dict) and "model" in model:
        model = model["model"]
    if not isinstance(model, dict):
        return False
    for t in model.get("tables") or []:
        for col in t.get("columns") or []:
            if col.get("expression"):
                return True
        for m in t.get("measures") or []:
            if m.get("expression"):
                return True
    return False


def run(raw: dict[str, Any]) -> list[Field]:
    """
    Return list of canonical Field that have formula (calculated_field).
    Collects from dimension and measure output; filters to those with is_calculated true and sets field_type to calculated_field.
    """
    dim_fields = dimension.run(raw) if dimension.can_handle(raw) else []
    meas_fields = measure.run(raw) if measure.can_handle(raw) else []
    calculated: list[Field] = []
    for f in dim_fields:
        if f.is_calculated and f.formula:
            calculated.append(
                Field(
                    id=f.id,
                    name=f.name,
                    field_type="calculated_field",
                    data_type=f.data_type,
                    source_table=f.source_table,
                    source_column=f.source_column,
                    aggregation=f.aggregation,
                    formula=f.formula,
                    depends_on=f.depends_on,
                    is_calculated=True,
                    extended_properties=f.extended_properties,
                )
            )
    for f in meas_fields:
        if f.is_calculated and f.formula:
            calculated.append(
                Field(
                    id=f.id,
                    name=f.name,
                    field_type="calculated_field",
                    data_type=f.data_type,
                    source_table=f.source_table,
                    source_column=f.source_column,
                    aggregation=f.aggregation,
                    formula=f.formula,
                    depends_on=f.depends_on,
                    is_calculated=True,
                    extended_properties=f.extended_properties,
                )
            )
    return calculated
