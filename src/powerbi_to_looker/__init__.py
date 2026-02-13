"""Power BI to LookML migration library.

Pipeline: Collector -> Parser/Normalizer -> Transformer -> Generator.
See docs/code_layout.md for layout. Old implementation in archive/.
"""

from powerbi_to_looker.collector import Collector, CollectorProtocol
from powerbi_to_looker.parser_normalizer import load
from powerbi_to_looker.transformer import to_lookml_terms
from powerbi_to_looker.generator import write

__version__ = "0.1.0"

__all__ = [
    "Collector",
    "CollectorProtocol",
    "load",
    "to_lookml_terms",
    "write",
    "__version__",
]
