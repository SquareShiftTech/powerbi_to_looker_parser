"""Input: dict | local path -> raw dict. Uses common.path_utils."""

import json
from pathlib import Path
from typing import Any

from powerbi_to_looker.common.path_utils import resolve_path


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

    report_def = folder / "Report" / "definition"
    if report_def.exists():
        report_json = report_def / "report.json"
        raw["report"] = _read_json(report_json) if report_json.exists() else {}
        pages_meta_file = report_def / "pages" / "pages.json"
        raw["pages_metadata"] = _read_json(pages_meta_file) if pages_meta_file.exists() else {}
        raw["pages"] = {}
        pages_dir = report_def / "pages"
        if pages_dir.exists():
            for page_dir in pages_dir.iterdir():
                if not page_dir.is_dir() or page_dir.name == "pages.json":
                    continue
                page_json_file = page_dir / "page.json"
                page_data: dict[str, Any] = {}
                if page_json_file.exists():
                    page_data["page"] = _read_json(page_json_file)
                visuals_dir = page_dir / "visuals"
                page_data["visuals"] = {}
                if visuals_dir.exists():
                    for vis_dir in visuals_dir.iterdir():
                        if not vis_dir.is_dir():
                            continue
                        vis_file = vis_dir / "visual.json"
                        if vis_file.exists():
                            page_data["visuals"][vis_dir.name] = _read_json(vis_file)
                raw["pages"][page_dir.name] = page_data
    else:
        raw["report"] = {}
        raw["pages_metadata"] = {}
        raw["pages"] = {}

    return raw
