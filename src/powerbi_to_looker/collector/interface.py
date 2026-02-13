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

    def extract(self, blob: bytes | str, artifact_type: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Turn blob into structured metadata. artifact_type: model | report | dashboard | None (infer)."""
        ...

    def collect(self, item_id: str, artifact_type: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Convenience: download(item_id) then extract(blob, artifact_type)."""
        ...
