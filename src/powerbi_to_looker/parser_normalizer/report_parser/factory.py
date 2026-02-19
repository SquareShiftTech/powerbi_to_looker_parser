"""Factory to pick definition vs sections parser from folder layout."""

from pathlib import Path

from powerbi_to_looker.parser_normalizer.report_parser.definition_parser import DefinitionReportParser
from powerbi_to_looker.parser_normalizer.report_parser.protocol import ReportStructureParser
from powerbi_to_looker.parser_normalizer.report_parser.sections_parser import SectionsReportParser


class ReportParserFactory:
    """Returns the parser that can handle the report folder. Prefer definition over sections if both exist."""

    def __init__(self) -> None:
        self._definition = DefinitionReportParser()
        self._sections = SectionsReportParser()

    def get_parser(self, folder: Path) -> ReportStructureParser | None:
        if self._definition.can_handle(folder):
            return self._definition
        if self._sections.can_handle(folder):
            return self._sections
        return None
