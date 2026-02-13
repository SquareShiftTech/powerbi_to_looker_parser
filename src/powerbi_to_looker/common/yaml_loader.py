"""Load YAML config. Used by parser_normalizer and transformer."""

from pathlib import Path
from typing import Any


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file; return dict. Placeholder."""
    raise NotImplementedError("load_yaml")
