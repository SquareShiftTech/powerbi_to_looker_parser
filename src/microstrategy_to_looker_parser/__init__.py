"""MicroStrategy to Looker Assessment Library.

This library provides tools for extracting and analyzing MicroStrategy
dossiers, documents, and reports for migration to Looker.
"""

from microstrategy_to_looker_parser.mstr_client import MicroStrategyClient
from microstrategy_to_looker_parser.data_extractor import DataExtractor
from microstrategy_to_looker_parser.json_formatter import JSONFormatter

# Version
__version__ = "1.0.0"

# Public API
__all__ = [
    "MicroStrategyClient",
    "DataExtractor",
    "JSONFormatter",
    "__version__",
]
