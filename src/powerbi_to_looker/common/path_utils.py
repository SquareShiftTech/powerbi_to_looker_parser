"""Local path vs GCS (gs://); read bytes/JSON. Used by parser_normalizer loader and optionally collector."""

from pathlib import Path
from typing import Any


def resolve_path(path_or_uri: str) -> str:
    """Resolve path: local file or gs:// URI. Placeholder."""
    return path_or_uri


def read_json_or_bytes(path_or_uri: str) -> bytes | dict[str, Any]:
    """Read file at path or GCS URI; return bytes or parsed JSON. Placeholder."""
    raise NotImplementedError("read_json_or_bytes")
