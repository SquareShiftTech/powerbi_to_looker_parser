"""Tests for SectionsReportParser."""

import json
from pathlib import Path

from powerbi_to_looker.parser_normalizer.report_parser.sections_parser import SectionsReportParser


def test_sections_parser_can_handle_false_when_no_sections(tmp_path):
    (tmp_path / "Report").mkdir(parents=True)
    assert SectionsReportParser().can_handle(tmp_path) is False


def test_sections_parser_can_handle_true_when_sections_exists(tmp_path):
    (tmp_path / "Report" / "sections").mkdir(parents=True)
    assert SectionsReportParser().can_handle(tmp_path) is True


def test_sections_parser_load_returns_contract_keys(tmp_path):
    (tmp_path / "Report" / "sections").mkdir(parents=True)
    out = SectionsReportParser().load(tmp_path)
    assert "report" in out
    assert "pages_metadata" in out
    assert "pages" in out
    assert "pageOrder" in out["pages_metadata"]


def test_sections_parser_load_one_section_one_visual(tmp_path):
    """Minimal sections layout: one section, one visualContainer with config.json."""
    (tmp_path / "Report" / "sections" / "001_TestPage").mkdir(parents=True)
    (tmp_path / "Report" / "sections" / "001_TestPage" / "section.json").write_text(
        '{"name":"page-id-1","displayName":"Test Page","ordinal":1,"width":1280,"height":720}'
    )
    (tmp_path / "Report" / "sections" / "001_TestPage" / "visualContainers" / "vc1_Chart").mkdir(parents=True)
    (tmp_path / "Report" / "sections" / "001_TestPage" / "visualContainers" / "vc1_Chart" / "visualContainer.json").write_text(
        '{"x":10,"y":20,"z":0,"width":100,"height":80}'
    )
    config = {
        "name": "vis-1",
        "singleVisual": {
            "visualType": "clusteredColumnChart",
            "projections": {"Category": [{"queryRef": "t.f1"}]},
            "prototypeQuery": {
                "From": [{"Name": "t", "Entity": "mytable"}],
                "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": "f1"}, "Name": "t.f1"}],
            },
        },
    }
    (tmp_path / "Report" / "sections" / "001_TestPage" / "visualContainers" / "vc1_Chart" / "config.json").write_text(
        json.dumps(config)
    )
    out = SectionsReportParser().load(tmp_path)
    assert out["pages_metadata"]["pageOrder"] == ["page-id-1"]
    assert "page-id-1" in out["pages"]
    assert out["pages"]["page-id-1"]["page"]["displayName"] == "Test Page"
    visuals = out["pages"]["page-id-1"]["visuals"]
    assert len(visuals) == 1
    vis = list(visuals.values())[0]
    assert vis["visual"]["visualType"] == "clusteredColumnChart"
    assert vis["position"]["x"] == 10
    assert "queryState" in vis["visual"]["query"]
    assert "Category" in vis["visual"]["query"]["queryState"]
