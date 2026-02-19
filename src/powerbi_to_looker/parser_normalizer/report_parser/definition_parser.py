"""Definition layout: Report/definition with pages.json, page.json, visuals/*/visual.json."""

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any] | list[Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class DefinitionReportParser:
    """Parses Report/definition layout. Outputs same contract: report, pages_metadata, pages."""

    def can_handle(self, folder: Path) -> bool:
        return (folder / "Report" / "definition").exists()

    def load(self, folder: Path) -> dict[str, Any]:
        report_def = folder / "Report" / "definition"
        out: dict[str, Any] = {
            "report": {},
            "pages_metadata": {},
            "pages": {},
        }
        report_json = report_def / "report.json"
        out["report"] = _read_json(report_json) if report_json.exists() else {}
        pages_meta_file = report_def / "pages" / "pages.json"
        out["pages_metadata"] = _read_json(pages_meta_file) if pages_meta_file.exists() else {}
        pages_dir = report_def / "pages"
        if pages_dir.exists():
            for page_dir in pages_dir.iterdir():
                if not page_dir.is_dir() or page_dir.name == "pages.json":
                    continue
                page_data: dict[str, Any] = {}
                page_json_file = page_dir / "page.json"
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
                out["pages"][page_dir.name] = page_data
        return out
