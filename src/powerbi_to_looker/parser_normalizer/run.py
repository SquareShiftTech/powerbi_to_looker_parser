"""Top-level: loop report folders, load -> semantic -> write canonical_output; record errors."""

import json
from pathlib import Path
from typing import Any

from powerbi_to_looker.parser_normalizer.loader import discover_report_folders, load
from powerbi_to_looker.parser_normalizer.semantic.orchestrator import run as run_semantic


def run_all(
    parsed_output_root: str | Path,
    canonical_output_dir: str | Path,
    *,
    write_manifest: bool = True,
) -> list[dict[str, Any]]:
    """
    For each report folder under parsed_output_root: load raw -> run semantic -> write
    canonical_output/<report_id>/metadata_model.json. On failure write _error.json.
    Returns manifest list: [{"report_id": ..., "success": bool, ...}].
    """
    root = Path(parsed_output_root)
    out_dir = Path(canonical_output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report_folders = discover_report_folders(root)
    if not report_folders:
        return []

    manifest: list[dict[str, Any]] = []

    for report_id, report_path in report_folders:
        entry: dict[str, Any] = {"report_id": report_id, "success": False}
        report_out = out_dir / report_id
        report_out.mkdir(parents=True, exist_ok=True)

        try:
            raw = load(str(report_path))
        except Exception as e:
            entry["error"] = str(e)
            entry["stage"] = "load"
            _write_error(report_out, report_id, str(e), "load")
            manifest.append(entry)
            continue

        try:
            metadata_model = run_semantic(raw)
        except Exception as e:
            entry["error"] = str(e)
            entry["stage"] = "semantic"
            _write_error(report_out, report_id, str(e), "semantic")
            manifest.append(entry)
            continue

        try:
            out_file = report_out / "metadata_model.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(
                    metadata_model.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str,
                )
            entry["success"] = True
            entry["metadata_model"] = str(out_file.relative_to(out_dir))
        except Exception as e:
            entry["error"] = str(e)
            entry["stage"] = "semantic"
            _write_error(report_out, report_id, str(e), "semantic")
        manifest.append(entry)

    if write_manifest:
        manifest_file = out_dir / "_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    return manifest


def _write_error(report_out: Path, report_id: str, error: str, stage: str) -> None:
    err = {"success": False, "report_id": report_id, "error": error, "stage": stage}
    with open(report_out / "_error.json", "w", encoding="utf-8") as f:
        json.dump(err, f, indent=2)
