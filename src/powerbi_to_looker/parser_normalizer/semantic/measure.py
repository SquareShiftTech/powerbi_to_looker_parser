"""Measure handler: raw["model"].tables[].measures -> list[Field] (measure)."""

import re
from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml
from powerbi_to_looker.models.canonical import Field

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "powerbi_canonical_mapping.yaml"


def _get_config() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        return load_yaml(_CONFIG_PATH)
    return {}


def _infer_aggregation_from_dax(expression: list[str] | str, config: dict[str, Any]) -> str | None:
    """Infer canonical aggregation from DAX expression using measure_aggregation map."""
    agg_map = config.get("measure_aggregation") or {}
    text = "\n".join(expression).strip() if isinstance(expression, list) else str(expression)
    for dax_key, canonical_agg in agg_map.items():
        if dax_key == "default":
            continue
        if canonical_agg is None:
            continue
        # Match word boundary for SUM, COUNT, etc.
        if re.search(rf"\b{dax_key}\s*\(", text, re.IGNORECASE):
            return canonical_agg
    return agg_map.get("default")


def can_handle(raw: dict[str, Any]) -> bool:
    """Return True if raw model has tables with measures."""
    model = raw.get("model") or raw
    if isinstance(model, dict) and "model" in model:
        model = model["model"]
    tables = model.get("tables") if isinstance(model, dict) else None
    if not isinstance(tables, list):
        return False
    return any(isinstance(t.get("measures"), list) for t in tables)


def run(raw: dict[str, Any]) -> list[Field]:
    """Build list of canonical Field (measure) from all table measures.
    Model measures have a formula (DAX) that is already the full expression; we leave
    aggregation=None so the transform layer can emit the formula as-is and avoid double aggregation.
    """
    config = _get_config()
    defaults = config.get("defaults") or {}
    measure_data_type = defaults.get("measure_data_type", "number")

    model_obj = raw.get("model") or raw
    model = model_obj.get("model", model_obj) if isinstance(model_obj, dict) else model_obj
    if not isinstance(model, dict):
        return []

    fields: list[Field] = []
    for t in model.get("tables") or []:
        table_name = t.get("name") or ""
        for m in t.get("measures") or []:
            name = m.get("name") or ""
            lineage = m.get("lineageTag") or name
            expression = m.get("expression") or []
            if isinstance(expression, str):
                formula = expression.strip() or None
            elif expression:
                formula = "\n".join(str(x) for x in expression).strip()
            else:
                formula = None
            # Leave aggregation=None for model measures; formula is the full expression.
            # Transform layer: measure with formula and no aggregation → emit formula only.
            is_calculated = formula is not None

            ext: dict[str, Any] = {}
            if m.get("formatString"):
                ext["format_string"] = m.get("formatString")
            if m.get("lineageTag"):
                ext["lineageTag"] = m.get("lineageTag")

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
                    depends_on=None,
                    is_calculated=is_calculated,
                    extended_properties=ext if ext else None,
                )
            )
    return fields
