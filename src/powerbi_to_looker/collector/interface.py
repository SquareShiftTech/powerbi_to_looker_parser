"""Contract: list, download, extract, collect."""

from typing import Any, Protocol


class CollectorProtocol(Protocol):
    """Interface for metadata collector. Implement list, download, extract; collect is optional convenience."""

    def list(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Return list of report/dataset identifiers (id, name, workspace, type, etc.)."""
        ...

    def download(self, item_id: str, **kwargs: Any) -> bytes | str:
        """Fetch artifact for one item; returns blob (bytes or path)."""
        ...

    def extract(
        self,
        blob: str,
        output_path: str,
        pbi_tools_exe: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run pbi-tools on .pbix (blob = path); write parsed output to output_path. Returns e.g. {"output_path": str}."""
        ...

    def collect(self, item_id: str, **kwargs: Any) -> dict[str, Any]:
        """Convenience: download(item_id) then, when output_dir and pbi_tools_exe provided, extract(pbix_path, output_path, pbi_tools_exe)."""
        ...
