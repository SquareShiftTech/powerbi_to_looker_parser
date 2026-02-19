"""Tests for DefinitionReportParser."""

from pathlib import Path

from powerbi_to_looker.parser_normalizer.report_parser.definition_parser import DefinitionReportParser


def test_definition_parser_can_handle_false_when_no_definition(tmp_path):
    (tmp_path / "Report").mkdir(parents=True)
    assert DefinitionReportParser().can_handle(tmp_path) is False


def test_definition_parser_can_handle_true_when_definition_exists(tmp_path):
    (tmp_path / "Report" / "definition").mkdir(parents=True)
    assert DefinitionReportParser().can_handle(tmp_path) is True


def test_definition_parser_load_returns_contract_keys(tmp_path):
    (tmp_path / "Report" / "definition").mkdir(parents=True)
    (tmp_path / "Report" / "definition" / "report.json").write_text("{}")
    (tmp_path / "Report" / "definition" / "pages").mkdir(parents=True)
    (tmp_path / "Report" / "definition" / "pages" / "pages.json").write_text('{"pageOrder":[]}')
    out = DefinitionReportParser().load(tmp_path)
    assert "report" in out
    assert "pages_metadata" in out
    assert "pages" in out
    assert out["pages_metadata"].get("pageOrder") == []


def test_definition_parser_load_reads_page_and_visual(tmp_path):
    (tmp_path / "Report" / "definition").mkdir(parents=True)
    (tmp_path / "Report" / "definition" / "report.json").write_text("{}")
    (tmp_path / "Report" / "definition" / "pages").mkdir(parents=True)
    (tmp_path / "Report" / "definition" / "pages" / "pages.json").write_text('{"pageOrder":["pid1"]}')
    (tmp_path / "Report" / "definition" / "pages" / "pid1").mkdir()
    (tmp_path / "Report" / "definition" / "pages" / "pid1" / "page.json").write_text('{"name":"pid1","displayName":"Page 1"}')
    (tmp_path / "Report" / "definition" / "pages" / "pid1" / "visuals").mkdir()
    (tmp_path / "Report" / "definition" / "pages" / "pid1" / "visuals" / "vid1").mkdir()
    (tmp_path / "Report" / "definition" / "pages" / "pid1" / "visuals" / "vid1" / "visual.json").write_text(
        '{"name":"vid1","visual":{"visualType":"clusteredColumnChart"}}'
    )
    out = DefinitionReportParser().load(tmp_path)
    assert "pid1" in out["pages"]
    assert out["pages"]["pid1"]["page"]["displayName"] == "Page 1"
    assert "vid1" in out["pages"]["pid1"]["visuals"]
    assert out["pages"]["pid1"]["visuals"]["vid1"]["visual"]["visualType"] == "clusteredColumnChart"
