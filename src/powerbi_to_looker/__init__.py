"""Power BI to LookML migration library.

Pipeline: Collector -> Canonical -> Transformer -> Generator.
Output: LookML semantic layer (views, explores, model).
"""

from powerbi_to_looker.migration_engine import MigrationEngine

__version__ = "0.1.0"

__all__ = [
    "MigrationEngine",
    "__version__",
]
