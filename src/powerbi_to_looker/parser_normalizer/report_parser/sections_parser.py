"""Sections layout: Report/sections with section.json and visualContainers/* (visualContainer, config, query)."""

import json
from pathlib import Path
from typing import Any

from powerbi_to_looker.parser_normalizer.report_parser.sections_query import build_visual_query


def _read_json(path: Path) -> dict[str, Any] | list[Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _merge_visual_container(
    container_dir: Path,
    container_id: str,
) -> dict[str, Any] | None:
    """Read visualContainer.json, config.json, (optional query.json); merge into one definition-style visual."""
    vc_file = container_dir / "visualContainer.json"
    config_file = container_dir / "config.json"
    if not config_file.exists():
        return None
    config = _read_json(config_file)
    if not isinstance(config, dict):
        return None
    single = config.get("singleVisual") or {}
    visual_type = single.get("visualType")
    if not visual_type:
        return None

    # Position: prefer visualContainer, then config.layouts[0].position
    position: dict[str, Any] = {}
    if vc_file.exists():
        vc = _read_json(vc_file)
        if isinstance(vc, dict):
            position = {
                "x": vc.get("x", 0),
                "y": vc.get("y", 0),
                "z": vc.get("z", 0),
                "width": vc.get("width", 0),
                "height": vc.get("height", 0),
            }
    if not position and config.get("layouts"):
        lay = config["layouts"][0] if isinstance(config["layouts"], list) else None
        if isinstance(lay, dict) and lay.get("position"):
            position = dict(lay["position"])

    vis_name = config.get("name") or container_id
    query = build_visual_query(config)

    return {
        "name": vis_name,
        "position": position,
        "visual": {
            "visualType": visual_type,
            "query": query,
            **({} if not single.get("objects") else {"objects": single["objects"]}),
        },
    }


class SectionsReportParser:
    """Parses Report/sections layout. Outputs same contract: report, pages_metadata, pages."""

    def can_handle(self, folder: Path) -> bool:
        return (folder / "Report" / "sections").exists()

    def load(self, folder: Path) -> dict[str, Any]:
        sections_dir = folder / "Report" / "sections"
        out: dict[str, Any] = {
            "report": {},
            "pages_metadata": {"pageOrder": []},
            "pages": {},
        }
        report_json = folder / "Report" / "report.json"
        if report_json.exists():
            out["report"] = _read_json(report_json) or {}
        if not sections_dir.exists():
            return out

        section_dirs = sorted(
            [d for d in sections_dir.iterdir() if d.is_dir()],
            key=lambda d: d.name,
        )
        page_order: list[str] = []
        for section_dir in section_dirs:
            section_file = section_dir / "section.json"
            if not section_file.exists():
                continue
            section_data = _read_json(section_file)
            if not isinstance(section_data, dict):
                continue
            page_id = section_data.get("name") or section_dir.name
            page_order.append(page_id)
            page_data: dict[str, Any] = {
                "page": {
                    "name": page_id,
                    "displayName": section_data.get("displayName", section_dir.name),
                    "displayOption": section_data.get("displayOption", 1),
                    "height": section_data.get("height", 720),
                    "width": section_data.get("width", 1280),
                },
                "visuals": {},
            }
            vc_dir = section_dir / "visualContainers"
            if vc_dir.exists():
                for container_dir in vc_dir.iterdir():
                    if not container_dir.is_dir():
                        continue
                    merged = _merge_visual_container(container_dir, container_dir.name)
                    if merged:
                        vis_id = (merged.get("name") or container_dir.name)
                        page_data["visuals"][vis_id] = merged
            out["pages"][page_id] = page_data
        out["pages_metadata"]["pageOrder"] = page_order
        return out
