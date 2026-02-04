"""Load report layout (pages, visuals, filters, slicers) from .pbix Report/Layout."""

import json
from pathlib import Path
from zipfile import BadZipFile, ZipFile

LAYOUT_PATH = "Report/Layout"
ENCODING = "utf-16-le"


def _safe_json_loads(s: str | None) -> list | dict | None:
    if s is None or (isinstance(s, str) and s.strip() in ("", "{}", "[]")):
        return None
    try:
        out = json.loads(s)
        return out if out else None
    except (json.JSONDecodeError, TypeError):
        return None


def _extract_visual_from_container(container: dict) -> dict | None:
    config_str = container.get("config")
    if not config_str or not isinstance(config_str, str):
        return None
    config = _safe_json_loads(config_str)
    if not config:
        return None
    single_visual = config.get("singleVisual")
    if not single_visual:
        return None
    visual_type = single_visual.get("visualType", "")
    name = config.get("name", "")
    position = {
        "x": container.get("x"),
        "y": container.get("y"),
        "width": container.get("width"),
        "height": container.get("height"),
    }
    filters_raw = container.get("filters")
    filters = _safe_json_loads(filters_raw) if isinstance(filters_raw, str) else filters_raw
    if filters is None and isinstance(filters_raw, list):
        filters = filters_raw
    out: dict = {
        "visual_type": visual_type,
        "name": name,
        "position": position,
        "filters": filters if filters is not None else [],
    }
    if visual_type == "slicer":
        out["slicer_config"] = _extract_slicer_config(single_visual)
    return out


def _extract_slicer_config(single_visual: dict) -> dict:
    config: dict = {}
    projections = single_visual.get("projections") or {}
    values = projections.get("Values") or []
    if values:
        config["values"] = [
            {"queryRef": v.get("queryRef"), "active": v.get("active")}
            for v in values
            if isinstance(v, dict)
        ]
    objects = single_visual.get("objects") or {}
    data_objs = (objects.get("data") or []) if isinstance(objects.get("data"), list) else []
    for obj in data_objs:
        props = (obj.get("properties") or {}) if isinstance(obj, dict) else {}
        if "mode" in props:
            expr = props.get("mode") or {}
            if isinstance(expr, dict) and "expr" in expr:
                lit = (expr.get("expr") or {}).get("Literal") or {}
                if isinstance(lit, dict) and "Value" in lit:
                    config["mode"] = lit.get("Value")
            break
    return config


def load_report_layout(pbix_path: str | Path) -> dict:
    """Extract report layout (pages, visuals, filters, slicers) from a PBIX file.

    Reads Report/Layout from the PBIX ZIP (UTF-16-LE JSON) and returns
    source_file, report_level_filters, pages (with visuals), and slicers.

    Args:
        pbix_path: Path to .pbix file.

    Returns:
        Dict with source_file, report_level_filters, pages, slicers.

    Raises:
        FileNotFoundError: If pbix_path does not exist.
        ValueError: If file is not a valid ZIP or Layout is missing.
    """
    pbix_path = Path(pbix_path)
    if not pbix_path.exists():
        raise FileNotFoundError(f"PBIX file not found: {pbix_path}")

    try:
        with ZipFile(pbix_path, "r") as zf:
            layout_member = None
            for name in zf.namelist():
                if name.replace("\\", "/") == LAYOUT_PATH:
                    layout_member = name
                    break
            if not layout_member:
                raise ValueError(f"Layout file not found in PBIX: {LAYOUT_PATH}")
            with zf.open(layout_member) as f:
                raw = f.read()
    except BadZipFile as e:
        raise ValueError(f"File is not a valid ZIP/PBIX: {pbix_path}") from e

    try:
        layout_text = raw.decode(ENCODING)
    except UnicodeDecodeError:
        layout_text = raw.decode("utf-16")
    layout = json.loads(layout_text)

    source_file = str(pbix_path.resolve())
    report_filters = _safe_json_loads(layout.get("filters"))
    if report_filters is None and isinstance(layout.get("filters"), list):
        report_filters = layout.get("filters") or []

    pages: list[dict] = []
    all_slicers: list[dict] = []

    for section in layout.get("sections") or []:
        section_id = section.get("id")
        section_name = section.get("displayName") or section.get("name") or ""
        page_filters_raw = section.get("filters")
        page_filters = _safe_json_loads(page_filters_raw) if isinstance(page_filters_raw, str) else page_filters_raw
        if page_filters is None and isinstance(page_filters_raw, list):
            page_filters = page_filters_raw
        page_filters = page_filters if page_filters is not None else []

        visuals: list[dict] = []
        for vc in section.get("visualContainers") or []:
            visual = _extract_visual_from_container(vc)
            if visual:
                visuals.append(visual)
                if visual.get("visual_type") == "slicer":
                    all_slicers.append({
                        "page_name": section_name,
                        "page_id": section_id,
                        "visual_name": visual.get("name"),
                        "position": visual.get("position"),
                        "filters": visual.get("filters"),
                        "slicer_config": visual.get("slicer_config"),
                    })
        pages.append({
            "id": section_id,
            "name": section_name,
            "ordinal": section.get("ordinal"),
            "width": section.get("width"),
            "height": section.get("height"),
            "page_level_filters": page_filters,
            "visuals": visuals,
        })

    return {
        "source_file": source_file,
        "report_level_filters": report_filters if report_filters is not None else [],
        "pages": pages,
        "slicers": all_slicers,
    }
