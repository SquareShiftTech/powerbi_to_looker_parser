"""Tests for parser_normalizer.dashboard handlers and orchestrator."""

import pytest

from powerbi_to_looker.models.dashboard import (
    DashboardMetadata,
    DataMapping,
    FilterComponent,
    Visualization,
)
from powerbi_to_looker.parser_normalizer.dashboard.config import (
    creates_filter_component,
    creates_visualization,
    empty_data_mappings,
    get_component_type,
    get_viz_config,
)
from powerbi_to_looker.parser_normalizer.dashboard.orchestrator import run_viz
from powerbi_to_looker.parser_normalizer.dashboard.query_state import build_data_mappings
from powerbi_to_looker.parser_normalizer.dashboard.visuals import process_visual


def test_config_loads():
    config = get_viz_config()
    assert "visual_types" in config
    assert "query_state_roles" in config
    assert config.get("visual_types", {}).get("component_type", {}).get("slicer") == "filter"
    assert config.get("visual_types", {}).get("component_type", {}).get("clusteredColumnChart") == "visualization"


def test_get_component_type():
    config = get_viz_config()
    assert get_component_type("slicer", config) == "filter"
    assert get_component_type("clusteredColumnChart", config) == "visualization"
    assert get_component_type("actionButton", config) == "visualization"
    assert get_component_type("unknownType", config) is None


def test_creates_filter_component():
    config = get_viz_config()
    assert creates_filter_component("slicer", config) is True
    assert creates_filter_component("listSlicer", config) is True
    assert creates_filter_component("clusteredColumnChart", config) is False


def test_creates_visualization():
    config = get_viz_config()
    assert creates_visualization("clusteredColumnChart", config) is True
    assert creates_visualization("slicer", config) is False
    assert creates_visualization("actionButton", config) is True


def test_empty_data_mappings():
    config = get_viz_config()
    assert empty_data_mappings("actionButton", config) is True
    assert empty_data_mappings("clusteredColumnChart", config) is False


def test_query_state_measure_gets_measure_role():
    """Measure projection -> mapping_role measure (from projection, not YAML)."""
    query_state = {
        "Y": {
            "projections": [
                {
                    "field": {
                        "Measure": {
                            "Expression": {"SourceRef": {"Entity": "campaign_products"}},
                            "Property": "Conversion Rate",
                        }
                    },
                }
            ]
        },
    }
    config = get_viz_config()
    out = build_data_mappings(query_state, None, config)
    assert len(out) == 1
    assert out[0].mapping_role == "measure"
    assert out[0].field_id == "Conversion Rate"
    assert out[0].datasource_id == "campaign_products"


def test_query_state_column_gets_role_from_yaml():
    """Column projection -> mapping_role from query_state_roles (e.g. dimension for Category)."""
    query_state = {
        "Category": {
            "projections": [
                {
                    "field": {
                        "Column": {
                            "Expression": {"SourceRef": {"Entity": "marketing_campaign_data"}},
                            "Property": "Campaign Name",
                        }
                    },
                }
            ]
        },
    }
    config = get_viz_config()
    out = build_data_mappings(query_state, None, config)
    assert len(out) == 1
    assert out[0].mapping_role == "dimension"
    assert out[0].field_id == "Campaign Name"
    assert out[0].datasource_id == "marketing_campaign_data"


def test_query_state_sort_applied_to_matching_mapping():
    query_state = {
        "Y": {
            "projections": [
                {
                    "field": {
                        "Measure": {
                            "Expression": {"SourceRef": {"Entity": "t1"}},
                            "Property": "Revenue",
                        }
                    },
                }
            ]
        },
    }
    sort_definition = {
        "sort": [
            {
                "field": {
                    "Measure": {
                        "Expression": {"SourceRef": {"Entity": "t1"}},
                        "Property": "Revenue",
                    }
                },
                "direction": "Descending",
            }
        ]
    }
    config = get_viz_config()
    out = build_data_mappings(query_state, sort_definition, config)
    assert len(out) == 1
    assert out[0].sort_order == "desc"


def test_process_visual_chart():
    config = get_viz_config()
    visual_container = {
        "name": "vid1",
        "position": {"x": 0, "y": 0, "width": 100, "height": 80},
        "visual": {
            "visualType": "clusteredColumnChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            {
                                "field": {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Entity": "T1"}},
                                        "Property": "Col1",
                                    }
                                },
                            }
                        ]
                    },
                    "Y": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": {"SourceRef": {"Entity": "T1"}},
                                        "Property": "Total",
                                    }
                                },
                            }
                        ]
                    },
                }
            },
        },
    }
    comp, viz, filt = process_visual("vid1", visual_container, config)
    assert comp is not None
    assert comp.id == "vid1"
    assert comp.type == "visualization"
    assert comp.visualization_id == "vid1"
    assert viz is not None
    assert viz.visualization_type == "clusteredColumnChart"
    assert len(viz.data_mappings) == 2
    assert filt is None


def test_process_visual_slicer():
    config = get_viz_config()
    visual_container = {
        "name": "slicer1",
        "position": {"x": 0, "y": 0, "width": 100, "height": 50},
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            {
                                "field": {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Entity": "customers"}},
                                        "Property": "Country",
                                    }
                                },
                            }
                        ]
                    },
                }
            },
        },
    }
    comp, viz, filt = process_visual("slicer1", visual_container, config)
    assert comp is not None
    assert comp.type == "filter"
    assert comp.filter_id is not None
    assert filt is not None
    assert filt.field_id == "Country"
    assert filt.datasource_id == "customers"
    assert viz is None


def test_process_visual_action_button():
    config = get_viz_config()
    visual_container = {
        "name": "btn1",
        "position": {"x": 0, "y": 0, "width": 48, "height": 40},
        "visual": {"visualType": "actionButton"},
    }
    comp, viz, filt = process_visual("btn1", visual_container, config)
    assert comp is not None
    assert comp.type == "visualization"
    assert viz is not None
    assert viz.data_mappings == []
    assert filt is None


def test_run_viz_minimal_raw():
    raw = {
        "pages_metadata": {"pageOrder": ["p1"]},
        "pages": {
            "p1": {
                "page": {"displayName": "Page 1", "name": "p1"},
                "visuals": {},
            }
        },
    }
    meta = run_viz(raw, report_id="r1")
    assert isinstance(meta, DashboardMetadata)
    assert meta.source_system == "powerbi"
    assert len(meta.dashboards) == 1
    assert meta.dashboards[0].id == "r1"
    assert meta.dashboards[0].name == "Page 1"
    assert len(meta.dashboards[0].pages) == 1
    assert meta.dashboards[0].pages[0].page_id == "p1"
    assert meta.dashboards[0].is_multi_page is False


def test_run_viz_unknown_visual_type_skipped():
    """Visual type not in config is skipped (process_visual returns None)."""
    raw = {
        "pages_metadata": {"pageOrder": ["p1"]},
        "pages": {
            "p1": {
                "page": {"displayName": "Page 1", "name": "p1"},
                "visuals": {
                    "v1": {
                        "name": "v1",
                        "position": {"x": 0, "y": 0, "width": 10, "height": 10},
                        "visual": {"visualType": "_unknownTypeNotInYaml_"},
                    },
                },
            }
        },
    }
    meta = run_viz(raw, report_id="r1")
    assert len(meta.dashboards[0].pages[0].components) == 0
    assert len(meta.visualizations) == 0
