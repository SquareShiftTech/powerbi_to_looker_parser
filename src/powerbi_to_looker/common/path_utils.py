"""Local path vs GCS (gs://); read bytes/JSON. Used by parser_normalizer loader and optionally collector."""

import json
from pathlib import Path
from typing import Any


def resolve_path(path_or_uri: str) -> str:
    """Resolve path: local file or gs:// URI. Returns as-is for local; GCS not yet implemented."""
    if path_or_uri.startswith("gs://"):
        return path_or_uri
    return str(Path(path_or_uri).resolve())


def read_json_or_bytes(path_or_uri: str) -> bytes | dict[str, Any]:
    """Read file at path or GCS URI; return bytes or parsed JSON. GCS returns bytes (not parsed)."""
    if path_or_uri.startswith("gs://"):
        raise NotImplementedError("GCS read not implemented; use local path")
    p = Path(path_or_uri)
    if not p.exists():
        raise FileNotFoundError(f"Path not found: {p}")
    with open(p, encoding="utf-8") as f:
        if p.suffix.lower() in (".json",):
            return json.load(f)
    with open(p, "rb") as f:
        return f.read()
