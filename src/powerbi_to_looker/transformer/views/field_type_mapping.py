"""Map Power BI data_type and aggregation to Looker field_type, looker_type, value_format, timeframes."""

from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "field_type_mapping.yaml"

# Keywords that suggest datetime -> dimension_group
_DATETIME_NAME_KEYWORDS = ("date", "time", "timestamp", "created", "updated", "modified")


def _get_config() -> dict[str, Any]:
    try:
        return load_yaml(_CONFIG_PATH)
    except FileNotFoundError:
        return {}


def infer_measure_type_from_formula_ast(formula_ast: Any) -> str | None:
    """Infer Looker measure type from model measure formula AST (e.g. COUNT -> count). Returns None if not inferrable."""
    if not formula_ast or not isinstance(formula_ast, dict):
        return None
    name = (formula_ast.get("name") or "").strip().upper()
    if not name:
        return None
    config = _get_config()
    agg_to_measure = config.get("aggregation_to_measure_type") or {}
    return agg_to_measure.get(name)


def map_field_type(
    data_type: str | None,
    aggregation: str | None,
    field_name: str = "",
) -> dict[str, Any]:
    """Map Power BI data_type and aggregation to Looker field_type, looker_type, timeframes, value_format.

    Returns dict with: field_type, looker_type, timeframes (optional), value_format (optional), conversion_status.
    """
    config = _get_config()
    data_type_map = config.get("data_type_map") or {}
    agg_to_measure = config.get("aggregation_to_measure_type") or {}
    value_format_map = config.get("value_format_map") or {}
    timeframes = config.get("dimension_group_timeframes") or [
        "raw", "time", "date", "week", "month", "quarter", "year"
    ]

    dt = (data_type or "").lower().strip()
    agg = (aggregation or "").upper().strip() if aggregation else None
    name_lower = (field_name or "").lower()

    # Measure: has aggregation
    if agg and agg in agg_to_measure:
        looker_type = agg_to_measure[agg]
        value_format = None
        if dt == "currency":
            value_format = value_format_map.get("currency") or "usd"
        return {
            "field_type": "measure",
            "looker_type": looker_type,
            "timeframes": None,
            "value_format": value_format,
            "conversion_status": "auto",
        }

    # Percent without aggregation -> measure number + value_format (per requirements table)
    if dt == "percent":
        return {
            "field_type": "measure",
            "looker_type": data_type_map.get("percent") or "number",
            "timeframes": None,
            "value_format": value_format_map.get("percent") or "percent_2",
            "conversion_status": "auto",
        }

    # Datetime or name suggests date -> dimension_group
    if dt == "datetime" or any(k in name_lower for k in _DATETIME_NAME_KEYWORDS):
        return {
            "field_type": "dimension_group",
            "looker_type": data_type_map.get("datetime") or "time",
            "timeframes": timeframes,
            "value_format": None,
            "conversion_status": "auto",
        }

    # Dimension: map data_type to looker_type
    looker_type = data_type_map.get(dt) or data_type_map.get("string") or "string"
    status = "partial" if dt and dt not in data_type_map else "auto"
    return {
        "field_type": "dimension",
        "looker_type": looker_type,
        "timeframes": None,
        "value_format": None,
        "conversion_status": status,
    }
