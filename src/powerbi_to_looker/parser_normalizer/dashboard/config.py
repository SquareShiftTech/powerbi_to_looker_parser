"""Load visualization_mapping.yaml. No defaults in code for missing keys."""

from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "visualization_mapping.yaml"


def get_viz_config() -> dict[str, Any]:
    """Load visualization mapping config. Returns empty dict if file missing."""
    if _CONFIG_PATH.exists():
        return load_yaml(_CONFIG_PATH)
    return {}


def get_component_type(visual_type: str, config: dict[str, Any]) -> str | None:
    """Return canonical DashboardComponent.type for Power BI visualType, or None if not in config."""
    ct = (config.get("visual_types") or {}).get("component_type") or {}
    return ct.get(visual_type)


def creates_filter_component(visual_type: str, config: dict[str, Any]) -> bool:
    """True if this visual type creates a FilterComponent (slicer)."""
    lst = (config.get("visual_types") or {}).get("creates_filter_component") or []
    return visual_type in lst


def creates_visualization(visual_type: str, config: dict[str, Any]) -> bool:
    """True if this visual type creates a Visualization."""
    lst = (config.get("visual_types") or {}).get("creates_visualization") or []
    return visual_type in lst


def empty_data_mappings(visual_type: str, config: dict[str, Any]) -> bool:
    """True if this visual type has no queryState -> data_mappings = []."""
    lst = (config.get("visual_types") or {}).get("empty_data_mappings") or []
    return visual_type in lst


def get_query_state_role_for_column(query_state_key: str, config: dict[str, Any]) -> str | None:
    """Return canonical role for Column projections for this queryState key, or None if key not in config."""
    roles = (config.get("query_state_roles") or {})
    return roles.get(query_state_key)
