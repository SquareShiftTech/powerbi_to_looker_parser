"""LookML terms -> render -> write files to output_dir."""

from pathlib import Path
from typing import Any


def write(lookml_terms: dict[str, Any], output_dir: str | Path) -> list[str]:
    """Render templates and write .view.lkml, .model.lkml, dashboard files. Placeholder."""
    raise NotImplementedError("write")
