"""Dimension handler: raw["model"].tables[].columns -> list[Field] (dimension or calculated_field)."""

from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml
from powerbi_to_looker.models.canonical import Field

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "powerbi_canonical_mapping.yaml"


def _get_config() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        return load_yaml(_CONFIG_PATH)
    return {}


def _data_type_from_config(data_type_key: str | None, data_types: dict[str, Any]) -> str | None:
    """Case-insensitive lookup; return None when unknown (no default)."""
    if not data_type_key:
        return None
    key_lower = data_type_key.strip().lower()
    if not key_lower:
        return None
    for k, v in data_types.items():
        if k.strip().lower() == key_lower:
            return v
    return None


def can_handle(raw: dict[str, Any]) -> bool:
    """Return True if raw model has tables with columns."""
    model = raw.get("model") or raw
    if isinstance(model, dict) and "model" in model:
        model = model["model"]
    tables = model.get("tables") if isinstance(model, dict) else None
    if not isinstance(tables, list):
        return False
    return any(isinstance(t.get("columns"), list) for t in tables)


def run(raw: dict[str, Any]) -> list[Field]:
    """Build list of canonical Field (dimension, measure, or calculated_field) from all table columns.
    Columns with aggregation (summarizeBy) are emitted as field_type=measure; others as dimension/calculated_field.
    data_type is None when Power BI type is missing or unmapped.
    """
    config = _get_config()
    data_types = config.get("data_types") or {}
    column_types = config.get("column_types") or {}
    summarize_by = config.get("summarizeBy") or {}
    defaults = config.get("defaults") or {}
    measure_data_type = defaults.get("measure_data_type", "number")

    model_obj = raw.get("model") or raw
    model = model_obj.get("model", model_obj) if isinstance(model_obj, dict) else model_obj
    if not isinstance(model, dict):
        return []

    fields: list[Field] = []
    for t in model.get("tables") or []:
        table_name = t.get("name") or ""
        for col in t.get("columns") or []:
            col_name = col.get("name") or ""
            lineage = col.get("lineageTag") or col_name
            data_type_key = col.get("dataType")
            data_type = _data_type_from_config(data_type_key, data_types)

            col_type_key = col.get("type") or "Data"
            base_field_type = column_types.get(col_type_key, column_types.get("Data", "dimension"))
            sum_by_key = (col.get("summarizeBy") or "none").strip().lower()
            aggregation = next(
                (v for k, v in summarize_by.items() if k.strip().lower() == sum_by_key),
                summarize_by.get("default"),
            )

            # If column has aggregation (e.g. summarizeBy sum), treat as measure
            if aggregation is not None:
                field_type = "measure"
                if data_type is None:
                    data_type = measure_data_type
            else:
                field_type = base_field_type

            expression = col.get("expression")
            formula = None
            if isinstance(expression, list):
                formula = "\n".join(str(x) for x in expression).strip() or None
            is_calculated = formula is not None

            ext: dict[str, Any] = {}
            if col.get("formatString"):
                ext["format_string"] = col.get("formatString")
            if col.get("lineageTag"):
                ext["lineageTag"] = col.get("lineageTag")

            fields.append(
                Field(
                    id=lineage,
                    name=col_name,
                    field_type=field_type,
                    data_type=data_type,
                    source_table=table_name,
                    source_column=col.get("sourceColumn") or col_name,
                    aggregation=aggregation,
                    formula=formula,
                    depends_on=None,
                    is_calculated=is_calculated,
                    extended_properties=ext if ext else None,
                )
            )
    return fields
