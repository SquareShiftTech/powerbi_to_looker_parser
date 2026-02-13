"""Extract report metadata from blob. Stateless: blob in -> dict out."""

from typing import Any


def extract(blob: bytes | str) -> dict[str, Any]:
    """Extract report metadata from blob. Placeholder."""
    raise NotImplementedError("extract report")
