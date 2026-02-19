"""Tests for ReportParserFactory: correct parser for definition/sections/both/neither."""

from pathlib import Path

from powerbi_to_looker.parser_normalizer.report_parser import ReportParserFactory
from powerbi_to_looker.parser_normalizer.report_parser.definition_parser import DefinitionReportParser
from powerbi_to_looker.parser_normalizer.report_parser.sections_parser import SectionsReportParser


def test_factory_returns_none_when_no_report_structure(tmp_path):
    """Folder with no Report/definition or Report/sections -> None."""
    (tmp_path / "Model").mkdir()
    (tmp_path / "Model" / "database.json").write_text("{}")
    factory = ReportParserFactory()
    assert factory.get_parser(tmp_path) is None


def test_factory_returns_definition_parser_when_definition_exists(tmp_path):
    """Report/definition present -> DefinitionReportParser."""
    (tmp_path / "Report" / "definition").mkdir(parents=True)
    factory = ReportParserFactory()
    parser = factory.get_parser(tmp_path)
    assert parser is not None
    assert isinstance(parser, DefinitionReportParser)


def test_factory_returns_sections_parser_when_only_sections_exists(tmp_path):
    """Report/sections present, no definition -> SectionsReportParser."""
    (tmp_path / "Report" / "sections").mkdir(parents=True)
    factory = ReportParserFactory()
    parser = factory.get_parser(tmp_path)
    assert parser is not None
    assert isinstance(parser, SectionsReportParser)


def test_factory_prefers_definition_over_sections(tmp_path):
    """Both Report/definition and Report/sections -> DefinitionReportParser."""
    (tmp_path / "Report" / "definition").mkdir(parents=True)
    (tmp_path / "Report" / "sections").mkdir(parents=True)
    factory = ReportParserFactory()
    parser = factory.get_parser(tmp_path)
    assert parser is not None
    assert isinstance(parser, DefinitionReportParser)
