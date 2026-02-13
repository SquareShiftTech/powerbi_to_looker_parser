"""Input: dict | local path | gs:// path -> raw dict. Uses common.path_utils."""

from typing import Any


def load(path_or_metadata: str | dict[str, Any]) -> dict[str, Any]:
    """Resolve input (read from path or use dict); return raw metadata for downstream. Placeholder."""
    if isinstance(path_or_metadata, dict):
        return path_or_metadata
    raise NotImplementedError("load from path/GCS")
