"""Protocol for report structure parsers. Same contract: report, pages_metadata, pages."""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ReportStructureParser(Protocol):
    """Parses a report folder into the standard raw report shape. Implementations: definition vs sections."""

    def can_handle(self, folder: Path) -> bool:
        """True if this layout exists under folder (e.g. Report/definition or Report/sections)."""
        ...

    def load(self, folder: Path) -> dict[str, Any]:
        """Return {"report": ..., "pages_metadata": ..., "pages": ...}. Call only when can_handle(folder) is True."""
        ...
