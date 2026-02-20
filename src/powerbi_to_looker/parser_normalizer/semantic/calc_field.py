"""Calculated-field handler: all fields with formula -> list[Field] as dimension or measure.

Sources: (1) model.tables[].columns[] with expression, (2) model.tables[].measures[].
Emits field_type="dimension" for calculated columns, field_type="measure" for model measures;
is_calculated=True and formula set for both. Parses each formula and sets formula_ast or
formula_parse_error on Field. No separate calculated_field type.
"""

from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml
from powerbi_to_looker.dax import parse_formula
from powerbi_to_looker.models.canonical import Field

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "powerbi_canonical_mapping.yaml"


def _get_config() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        return load_yaml(_CONFIG_PATH)
    return {}


def _data_type_from_config(data_type_key: str | None, data_types: dict[str, Any]) -> str | None:
    if not data_type_key:
        return None
    key_lower = data_type_key.strip().lower()
    for k, v in data_types.items():
        if k.strip().lower() == key_lower:
            return v
    return None


def can_handle(raw: dict[str, Any]) -> bool:
    """Return True if raw model has any column with expression or any measures."""
    model = raw.get("model") or raw
    if isinstance(model, dict) and "model" in model:
        model = model["model"]
    if not isinstance(model, dict):
        return False
    for t in model.get("tables") or []:
        for col in t.get("columns") or []:
            if col.get("expression"):
                return True
        if t.get("measures"):
            return True
    return False


def run(raw: dict[str, Any]) -> list[Field]:
    """Build list of canonical Field for all formula-based fields (dimension or measure + is_calculated=True).
    (1) Calculated columns: columns with expression -> field_type=dimension.
    (2) Model measures: tables[].measures[] -> field_type=measure.
    """
    config = _get_config()
    data_types = config.get("data_types") or {}
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
            expression = col.get("expression")
            if not expression:
                continue
            if isinstance(expression, str):
                formula = expression.strip() or None
            else:
                formula = "\n".join(str(x) for x in expression).strip() or None
            if not formula:
                continue

            col_name = col.get("name") or ""
            lineage = col.get("lineageTag") or col_name
            data_type_key = col.get("dataType")
            data_type = _data_type_from_config(data_type_key, data_types)
            if data_type is None:
                data_type = measure_data_type

            ext: dict[str, Any] = {}
            if col.get("formatString"):
                ext["format_string"] = col.get("formatString")
            if col.get("lineageTag"):
                ext["lineageTag"] = col.get("lineageTag")

            formula_ast, formula_parse_error = parse_formula(formula)

            fields.append(
                Field(
                    id=lineage,
                    name=col_name,
                    field_type="dimension",
                    data_type=data_type,
                    source_table=table_name,
                    source_column=col.get("sourceColumn") or col_name,
                    aggregation=None,
                    formula=formula,
                    formula_ast=formula_ast,
                    formula_parse_error=formula_parse_error,
                    depends_on=None,
                    is_calculated=True,
                    extended_properties=ext if ext else None,
                )
            )

        for m in t.get("measures") or []:
            expression = m.get("expression") or []
            if isinstance(expression, str):
                formula = expression.strip() or None
            elif expression:
                formula = "\n".join(str(x) for x in expression).strip()
            else:
                formula = None
            if not formula:
                continue

            name = m.get("name") or ""
            lineage = m.get("lineageTag") or name

            ext = {}
            if m.get("formatString"):
                ext["format_string"] = m.get("formatString")
            if m.get("lineageTag"):
                ext["lineageTag"] = m.get("lineageTag")

            formula_ast, formula_parse_error = parse_formula(formula)

            fields.append(
                Field(
                    id=lineage,
                    name=name,
                    field_type="measure",
                    data_type=measure_data_type,
                    source_table=table_name,
                    source_column=None,
                    aggregation=None,
                    formula=formula,
                    formula_ast=formula_ast,
                    formula_parse_error=formula_parse_error,
                    depends_on=None,
                    is_calculated=True,
                    extended_properties=ext if ext else None,
                )
            )

    return fields
