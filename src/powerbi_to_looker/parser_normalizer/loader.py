"""Input: dict | local path -> raw dict. Uses common.path_utils."""

import json
from pathlib import Path
from typing import Any

from powerbi_to_looker.common.path_utils import resolve_path
from powerbi_to_looker.parser_normalizer.report_parser import ReportParserFactory


def discover_report_folders(parsed_output_root: str | Path) -> list[tuple[str, Path]]:
    """Discover report folders. If root has Model/database.json, return [(root.name, root)]. Else list subdirs that have it."""
    root = Path(resolve_path(str(parsed_output_root)))
    if not root.is_dir():
        return []
    model_in_root = root / "Model" / "database.json"
    if model_in_root.exists():
        return [(root.name, root)]
    result: list[tuple[str, Path]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        model_file = child / "Model" / "database.json"
        if model_file.exists():
            result.append((child.name, child))
    return result


def _read_json(path: Path) -> dict[str, Any] | list[Any]:
    """Read JSON file; return dict or list."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load(path_or_metadata: str | dict[str, Any]) -> dict[str, Any]:
    """
    Resolve input (read from path or use dict); return raw metadata for one report.
    When path: must point to a single report folder (containing Model/database.json).
    Returns {"model": <database.json>, "report": <report tree>}.
    """
    if isinstance(path_or_metadata, dict):
        return path_or_metadata

    folder = Path(resolve_path(str(path_or_metadata)))
    if not folder.is_dir():
        raise FileNotFoundError(f"Not a directory: {folder}")

    model_file = folder / "Model" / "database.json"
    if not model_file.exists():
        raise FileNotFoundError(f"Model/database.json not found under {folder}")

    raw: dict[str, Any] = {}
    raw["model"] = _read_json(model_file)

    factory = ReportParserFactory()
    parser = factory.get_parser(folder)
    if parser is not None:
        loaded = parser.load(folder)
        raw["report"] = loaded.get("report", {})
        raw["pages_metadata"] = loaded.get("pages_metadata", {})
        raw["pages"] = loaded.get("pages", {})
    else:
        raw["report"] = {}
        raw["pages_metadata"] = {}
        raw["pages"] = {}

    return raw
