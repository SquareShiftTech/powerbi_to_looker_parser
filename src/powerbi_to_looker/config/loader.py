"""Load Power BI → canonical mapping from YAML."""

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

_DEFAULT_PATH = Path(__file__).resolve().parent / "powerbi_canonical_mapping.yaml"
_LOOKML_MAPPING_PATH = Path(__file__).resolve().parent / "canonical_lookml_mapping.yaml"


def load_canonical_mapping(path: Path | str | None = None) -> dict[str, Any]:
    """Load Power BI → canonical mapping from YAML file.

    Args:
        path: Path to YAML file. If None, uses bundled powerbi_canonical_mapping.yaml.

    Returns:
        Dict with keys: data_types, column_types, relationship, measure_aggregation, defaults.
    """
    if yaml is None:
        raise ImportError("PyYAML is required for config loading. Install with: pip install pyyaml")
    p = Path(path) if path is not None else _DEFAULT_PATH
    if not p.exists():
        return _empty_mapping()
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else _empty_mapping()


def load_lookml_mapping(path: Path | str | None = None) -> dict[str, Any]:
    """Load canonical → LookML mapping from YAML (transformer config).

    Args:
        path: Path to YAML file. If None, uses bundled canonical_lookml_mapping.yaml.

    Returns:
        Dict with dimension_types, measure_types, join_types, date_handling,
        measures, naming, and optional dax_to_sql.
    """
    if yaml is None:
        raise ImportError("PyYAML is required for config loading. Install with: pip install pyyaml")
    p = Path(path) if path is not None else _LOOKML_MAPPING_PATH
    if not p.exists():
        return _empty_lookml_mapping()
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else _empty_lookml_mapping()


def _empty_lookml_mapping() -> dict[str, Any]:
    return {
        "dimension_types": {},
        "measure_types": {"default": "number"},
        "join_types": {"default": "left_outer"},
        "date_handling": {"datetype": "date", "timeframes": ["day", "week", "month", "quarter", "year"]},
        "measures": {"value_format": "#,##0.00", "format": "decimal_2", "reuse_base_dimension": True},
        "naming": {"max_name_length": 64, "sanitize": True},
    }


def _empty_mapping() -> dict[str, Any]:
    return {
        "data_types": {},
        "column_types": {},
        "relationship": {"join_type": {"default": "LEFT"}},
        "measure_aggregation": {"default": None},
        "defaults": {"data_type": "string", "join_type": "LEFT"},
    }
