"""
Extract original_formula, bq_formula, field_type, looker_type, label, and Report_name
from semantic_layer_artifact.json. Single file path = report for that file;
no args = report for all artifacts under transformer_output.
"""
import argparse
import csv
import json
from pathlib import Path


def get_report_name(artifact_path: Path) -> str:
    """Report_name = folder containing semantic_layer_artifact.json."""
    return artifact_path.parent.name


def extract_rows(artifact_path: Path) -> list[dict]:
    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    report_name = get_report_name(artifact_path)
    rows = []
    for view in data.get("views", []):
        view_name = view.get("view_name", "")
        for field in view.get("fields", []):
            original = field.get("original_formula") or ""
            if not original.strip():
                continue
            rows.append({
                "Report_name": report_name,
                "view_name": view_name,
                "field_name": field.get("field_name", ""),
                "original_formula": original,
                "bq_formula": field.get("bq_formula") or "",
                "field_type": field.get("field_type", ""),
                "looker_type": field.get("looker_type", ""),
                "label": field.get("label", ""),
            })
    return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    if not rows:
        return
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Extract formula report from semantic_layer_artifact.json"
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Single semantic_layer_artifact.json path; if omitted, process all under transformer_output",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output CSV path (default: formula_report.csv or formula_report_<Report_name>.csv)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    transformer_output = root / "transformer_output"

    if args.file:
        artifact_path = Path(args.file).resolve()
        if not artifact_path.is_file():
            raise SystemExit(f"File not found: {artifact_path}")
        artifact_paths = [artifact_path]
    else:
        artifact_paths = sorted(transformer_output.glob("*/semantic_layer_artifact.json"))
        if not artifact_paths:
            raise SystemExit(
                f"No semantic_layer_artifact.json found under {transformer_output}"
            )

    all_rows = []
    for ap in artifact_paths:
        all_rows.extend(extract_rows(ap))

    if not all_rows:
        print("No fields found.")
        return

    out_path = Path(args.output) if args.output else root / "formula_report.csv"
    if args.file and not args.output:
        report_name = get_report_name(artifact_paths[0])
        out_path = root / f"formula_report_{report_name}.csv"
    write_csv(all_rows, out_path)
    print(f"Wrote {len(all_rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
