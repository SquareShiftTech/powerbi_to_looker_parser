"""Canonical dashboard/report models: multi-BI (Dashboard, Visualization, etc.) for future viz/dashboard generation."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class Position(BaseModel):
    x: float
    y: float
    width: float
    height: float


class DataMapping(BaseModel):
    field_id: str
    datasource_id: str
    mapping_role: Literal["dimension", "measure", "grouping", "filter", "sort", "detail", "label", "tooltip"]
    aggregation: Optional[str] = None
    sort_order: Optional[Literal["asc", "desc"]] = None


class Filter(BaseModel):
    field_id: str
    filter_type: Literal["include", "exclude", "range", "top_n", "wildcard"]
    values: Optional[List[Any]] = None
    value_start: Optional[Any] = None
    value_end: Optional[Any] = None


class VisibilityCondition(BaseModel):
    type: Literal["parameter", "field", "always", "never"]
    parameter_id: Optional[str] = None
    field_id: Optional[str] = None
    operator: Optional[Literal["equals", "not_equals", "greater_than", "less_than", "contains"]] = None
    value: Optional[Any] = None


class DashboardComponent(BaseModel):
    id: str
    type: Literal["visualization", "text", "filter", "image", "container", "parameter", "web_content"]
    position: Position
    visualization_id: Optional[str] = None
    text_id: Optional[str] = None
    filter_id: Optional[str] = None
    image_id: Optional[str] = None
    container_id: Optional[str] = None
    parameter_id: Optional[str] = None
    web_content_id: Optional[str] = None
    visibility_condition: Optional[VisibilityCondition] = None


class DashboardPage(BaseModel):
    page_id: str
    page_name: str
    page_order: int
    layout: Dict[str, Any]
    components: List[DashboardComponent]


class Interaction(BaseModel):
    id: str
    type: Literal["filter", "highlight", "navigate", "parameter_change", "drill_down", "cross_filter"]
    source_component_id: str
    target_component_ids: List[str]
    source_field_id: Optional[str] = None
    target_field_id: Optional[str] = None
    url_template: Optional[str] = None
    parameter_id: Optional[str] = None


class Dashboard(BaseModel):
    id: str
    name: str
    source_system: str
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    description: Optional[str] = None
    is_multi_page: bool = False
    layout: Optional[Dict[str, Any]] = None
    components: Optional[List[DashboardComponent]] = None
    pages: Optional[List[DashboardPage]] = None
    interactions: List[Interaction] = []


class VizCalculatedField(BaseModel):
    id: str
    name: str
    formula: str
    calculation_type: Literal["table_calculation", "window_function", "quick_calc"]
    depends_on: Optional[List[str]] = None


class ConditionalFormatting(BaseModel):
    type: Literal["color_scale", "data_bars", "icon_set", "highlight_cells"]
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    min_color: Optional[str] = None
    max_color: Optional[str] = None
    thresholds: Optional[List[Dict[str, Any]]] = None


class Visualization(BaseModel):
    id: str
    name: str
    visualization_type: str
    source_system: str
    viz_calculated_fields: List[VizCalculatedField] = []
    data_mappings: List[DataMapping]
    filters: List[Filter] = []
    parameters: List[str] = []
    conditional_formatting: Optional[List[ConditionalFormatting]] = None
    extended_properties: Optional[Dict[str, Any]] = None


class TextComponent(BaseModel):
    id: str
    content: str
    extended_properties: Optional[Dict[str, Any]] = None


class FilterComponent(BaseModel):
    id: str
    field_id: str
    datasource_id: str
    extended_properties: Optional[Dict[str, Any]] = None


class ImageComponent(BaseModel):
    id: str
    image_url: str
    extended_properties: Optional[Dict[str, Any]] = None


class LayoutProperties(BaseModel):
    container_type: Literal["horizontal", "vertical", "grid", "tabs"]
    distribution: Optional[Literal["equal", "weighted", "auto"]] = None
    spacing: Optional[int] = None
    alignment: Optional[Literal["stretch", "start", "center", "end"]] = None


class ContainerComponent(BaseModel):
    id: str
    child_component_ids: List[str]
    layout_properties: Optional[LayoutProperties] = None
    extended_properties: Optional[Dict[str, Any]] = None


class ParameterComponent(BaseModel):
    id: str
    parameter_id: str
    label: Optional[str] = None
    extended_properties: Optional[Dict[str, Any]] = None


class WebContentComponent(BaseModel):
    id: str
    url: str
    allow_interaction: bool = True
    extended_properties: Optional[Dict[str, Any]] = None


class ReportComponent(BaseModel):
    id: str
    type: Literal["table", "chart", "text", "image", "parameter"]
    position: Position
    table_id: Optional[str] = None
    chart_id: Optional[str] = None
    text_id: Optional[str] = None
    image_id: Optional[str] = None
    parameter_id: Optional[str] = None


class ReportSection(BaseModel):
    components: List[ReportComponent]


class DrillThrough(BaseModel):
    id: str
    source_component_id: str
    target_report_id: str
    pass_parameters: List[Dict[str, str]]


class Report(BaseModel):
    id: str
    name: str
    source_system: str
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    description: Optional[str] = None
    page_layout: Dict[str, Any]
    sections: Dict[str, ReportSection]
    drill_throughs: List[DrillThrough] = []


class TableColumn(BaseModel):
    field_id: str
    datasource_id: str
    column_width: Optional[float] = None
    header: str
    aggregation: Optional[str] = None
    conditional_formatting: Optional[ConditionalFormatting] = None


class ReportTable(BaseModel):
    """Report/dashboard table component (list, crosstab, pivot). Named to avoid clash with canonical Table."""

    id: str
    name: str
    table_type: Literal["list", "crosstab", "pivot"]
    columns: Optional[List[TableColumn]] = None
    row_fields: Optional[List[Dict[str, str]]] = None
    column_fields: Optional[List[Dict[str, str]]] = None
    measure_fields: Optional[List[Dict[str, Any]]] = None
    grouping: Optional[List[str]] = None
    sorting: Optional[List[Dict[str, str]]] = None
    show_subtotals: bool = False
    show_grand_total: bool = False
    filters: List[Filter] = []
    extended_properties: Optional[Dict[str, Any]] = None


class Chart(BaseModel):
    id: str
    name: str
    chart_type: str
    data_mappings: List[DataMapping]
    filters: List[Filter] = []
    extended_properties: Optional[Dict[str, Any]] = None


class DashboardMetadata(BaseModel):
    metadata_version: str = "1.0"
    source_system: str
    extracted_at: datetime
    dashboards: List[Dashboard]
    visualizations: List[Visualization]
    text_components: List[TextComponent] = []
    filter_components: List[FilterComponent] = []
    image_components: List[ImageComponent] = []
    container_components: List[ContainerComponent] = []
    parameter_components: List[ParameterComponent] = []
    web_content_components: List[WebContentComponent] = []


class ReportMetadata(BaseModel):
    metadata_version: str = "1.0"
    source_system: str
    extracted_at: datetime
    reports: List[Report]
    tables: List[ReportTable]
    charts: List[Chart]
    text_components: List[TextComponent] = []
    parameter_components: List[ParameterComponent] = []
    image_components: List[ImageComponent] = []
