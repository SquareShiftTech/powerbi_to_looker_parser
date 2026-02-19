"""Build DashboardComponent, Visualization, FilterComponent from raw visuals. Uses config for visual type -> component type."""

from typing import Any

from powerbi_to_looker.models.dashboard import (
    DashboardComponent,
    FilterComponent,
    Position,
    Visualization,
)
from powerbi_to_looker.parser_normalizer.dashboard.config import (
    creates_filter_component,
    creates_visualization,
    empty_data_mappings,
    get_component_type,
    get_viz_config,
)
from powerbi_to_looker.parser_normalizer.dashboard.query_state import (
    _resolve_field_from_projection,
    build_data_mappings,
)


def _position_from_raw(pos: dict[str, Any] | None) -> Position:
    if not pos:
        return Position(x=0.0, y=0.0, width=0.0, height=0.0)
    return Position(
        x=float(pos.get("x", 0)),
        y=float(pos.get("y", 0)),
        width=float(pos.get("width", 0)),
        height=float(pos.get("height", 0)),
        z=int(pos["z"]) if pos.get("z") is not None else None,
        tab_order=int(pos["tabOrder"]) if pos.get("tabOrder") is not None else None,
    )


def _slicer_field_from_query_state(query: dict[str, Any] | None, config: dict[str, Any]) -> tuple[str | None, str | None]:
    """Get (datasource_id, field_id) from slicer queryState.Values. Only first projection. Only if Values is in config."""
    if not query or "Values" not in (config.get("query_state_roles") or {}):
        return None, None
    qs = query.get("queryState") or {}
    values_spec = qs.get("Values")
    if not values_spec:
        return None, None
    projections = values_spec.get("projections") or []
    if not projections:
        return None, None
    ds_id, field_id, _ = _resolve_field_from_projection(projections[0])
    return ds_id, field_id


def process_visual(
    visual_id: str,
    visual_container: dict[str, Any],
    config: dict[str, Any],
) -> tuple[DashboardComponent | None, Visualization | None, FilterComponent | None]:
    """
    Process one visual container (visual.json). Returns (DashboardComponent, Visualization or None, FilterComponent or None).
    If visualType is not in config, returns (None, None, None) — caller should skip or fail per requirements.
    """
    visual = visual_container.get("visual") or {}
    visual_type = visual.get("visualType")
    if not visual_type:
        return None, None, None

    component_type = get_component_type(visual_type, config)
    if component_type is None:
        return None, None, None

    pos = _position_from_raw(visual_container.get("position"))
    comp = DashboardComponent(
        id=visual_id,
        type=component_type,
        position=pos,
        visualization_id=None,
        filter_id=None,
    )

    viz: Visualization | None = None
    filt: FilterComponent | None = None
    query = visual.get("query") or {}

    if creates_filter_component(visual_type, config):
        ds_id, field_id = _slicer_field_from_query_state(query, config)
        if ds_id and field_id:
            filt = FilterComponent(
                id=f"filter_{visual_id}",
                field_id=field_id,
                datasource_id=ds_id,
                extended_properties=None,
            )
            comp.filter_id = filt.id

    if creates_visualization(visual_type, config):
        if empty_data_mappings(visual_type, config):
            data_mappings = []
        else:
            qs = query.get("queryState") or {}
            sort_def = query.get("sortDefinition")
            data_mappings = build_data_mappings(qs, sort_def, config)
        viz = Visualization(
            id=visual_id,
            name=visual_type,
            visualization_type=visual_type,
            source_system="powerbi",
            viz_calculated_fields=[],
            data_mappings=data_mappings,
            filters=[],
            parameters=[],
            conditional_formatting=None,
            extended_properties=None,
        )
        comp.visualization_id = viz.id

    return comp, viz, filt


def process_page_visuals(
    page_id: str,
    visuals: dict[str, Any],
    config: dict[str, Any],
) -> tuple[list[DashboardComponent], list[Visualization], list[FilterComponent]]:
    """Process all visuals on a page. Returns (components, visualizations, filter_components)."""
    if config is None:
        config = get_viz_config()
    components: list[DashboardComponent] = []
    visualizations: list[Visualization] = []
    filter_components: list[FilterComponent] = []

    for vis_id, vis_data in (visuals or {}).items():
        comp, viz, filt = process_visual(vis_id, vis_data, config)
        if comp is None:
            continue
        components.append(comp)
        if viz is not None:
            visualizations.append(viz)
        if filt is not None:
            filter_components.append(filt)

    return components, visualizations, filter_components
