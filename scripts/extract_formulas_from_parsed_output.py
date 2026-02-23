"""Extract all DAX formulas into the real-formulas fixture.

Primary source: canonical_output (metadata_model.json). Each Field with a non-empty
formula is emitted. Fallback: parsed_output (Model/database.json) if canonical_output
is missing or has no reports.

Writes tests/transformer/fixtures/real_formulas.json for test_formula_converter_real
and show_formula_outputs.

Usage (from repo root):
  uv run python scripts/extract_formulas_from_parsed_output.py
  uv run python scripts/extract_formulas_from_parsed_output.py --canonical-output-dir canonical_output
  uv run python scripts/extract_formulas_from_parsed_output.py --parsed-output-dir parsed_output  # fallback only
"""

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from powerbi_to_looker.parser_normalizer.loader import discover_report_folders  # noqa: E402


def extract_from_canonical(metadata_model: dict, report_id: str) -> list[dict]:
    """From canonical metadata_model.json, return list of {name, dax, resolution_map}."""
    out: list[dict] = []
    for ds in metadata_model.get("datasources") or []:
        for field in ds.get("fields") or []:
            formula = (field.get("formula") or "").strip()
            if not formula:
                continue
            name = field.get("name") or field.get("id") or ""
            source_table = (field.get("source_table") or "").strip()
            if source_table:
                name = f"{report_id} | {source_table}.{name}"
            else:
                name = f"{report_id} | {name}"
            out.append({"name": name, "dax": formula, "resolution_map": {}})
    return out


def _normalize_expression(expression) -> str | None:
    """Same as calc_field: expression can be str or list of lines."""
    if not expression:
        return None
    if isinstance(expression, str):
        formula = expression.strip() or None
    else:
        formula = "\n".join(str(x) for x in expression).strip() or None
    return formula


def extract_from_parsed_model(model: dict, report_id: str) -> list[dict]:
    """From raw database.json, return list of {name, dax, resolution_map}."""
    model_data = (
        model
        if isinstance(model, dict) and "tables" in model
        else (model.get("model") if isinstance(model, dict) else {})
    )
    if not isinstance(model_data, dict):
        model_data = {}
    out: list[dict] = []
    for t in model_data.get("tables") or []:
        table_name = t.get("name") or ""
        for col in t.get("columns") or []:
            formula = _normalize_expression(col.get("expression"))
            if not formula:
                continue
            col_name = col.get("name") or ""
            out.append({"name": f"{report_id} | {table_name}.{col_name}", "dax": formula, "resolution_map": {}})
        for m in t.get("measures") or []:
            formula = _normalize_expression(m.get("expression"))
            if not formula:
                continue
            measure_name = m.get("name") or ""
            out.append({"name": f"{report_id} | {table_name}.{measure_name}", "dax": formula, "resolution_map": {}})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract DAX formulas into real_formulas.json")
    parser.add_argument(
        "--canonical-output-dir",
        type=Path,
        default=_REPO_ROOT / "canonical_output",
        help="Canonical output root (default: canonical_output); each subdir with metadata_model.json is a report",
    )
    parser.add_argument(
        "--parsed-output-dir",
        type=Path,
        default=_REPO_ROOT / "parsed_output",
        help="Fallback: parsed output root if canonical has no reports",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_REPO_ROOT / "tests" / "transformer" / "fixtures" / "real_formulas.json",
        help="Output JSON path for fixture",
    )
    args = parser.parse_args()

    all_entries: list[dict] = []
    canonical_dir = args.canonical_output_dir.resolve()

    if canonical_dir.is_dir():
        report_dirs = [p for p in canonical_dir.iterdir() if p.is_dir() and (p / "metadata_model.json").exists()]
        for report_dir in report_dirs:
            report_id = report_dir.name
            meta_file = report_dir / "metadata_model.json"
            with open(meta_file, encoding="utf-8") as f:
                metadata_model = json.load(f)
            all_entries.extend(extract_from_canonical(metadata_model, report_id))
        if all_entries:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(all_entries, f, indent=2)
            print(f"Extracted {len(all_entries)} formulas from canonical_output ({len(report_dirs)} report(s)) -> {args.output}")
            return 0

    # Fallback: parsed_output
    parsed_dir = args.parsed_output_dir.resolve()
    if not parsed_dir.is_dir():
        print(f"Canonical dir not found or empty; parsed_output not found: {parsed_dir}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        print(f"Wrote empty list to {args.output}")
        return 0

    report_folders = discover_report_folders(parsed_dir)
    if not report_folders:
        print(f"No report folders under {parsed_dir}; wrote empty list.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        return 0

    for report_id, folder in report_folders:
        model_file = folder / "Model" / "database.json"
        if not model_file.exists():
            continue
        with open(model_file, encoding="utf-8") as f:
            model = json.load(f)
        all_entries.extend(extract_from_parsed_model(model, report_id))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2)
    print(f"Extracted {len(all_entries)} formulas from parsed_output ({len(report_folders)} report(s)) -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
