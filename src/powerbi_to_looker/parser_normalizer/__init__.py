"""Parser & normalizer: path_or_metadata -> canonical bundle. Use load() or run_all()."""

from powerbi_to_looker.parser_normalizer.loader import discover_report_folders, load
from powerbi_to_looker.parser_normalizer.run import run_all

__all__ = ["load", "discover_report_folders", "run_all"]
