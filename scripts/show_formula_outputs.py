"""Run formula conversion and write results to a report file for iterative fixing.

Reads real_formulas.json, converts each DAX to BQ (or marks manual), and writes
a report file. Re-run after adding templates/direct_mapping to refresh the report.

Usage:
  uv run python scripts/show_formula_outputs.py
  uv run python scripts/show_formula_outputs.py --input path/to/formulas.json --output path/to/report.txt
"""

import argparse
import json
import sys
from pathlib import Path

# repo root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from powerbi_to_looker.dax.parser import parse_formula
from powerbi_to_looker.transformer.views.formula_converter import convert_with_status

DEFAULT_INPUT = ROOT / "tests" / "transformer" / "fixtures" / "real_formulas.json"
DEFAULT_OUTPUT = ROOT / "tests" / "transformer" / "fixtures" / "formula_conversion_report.txt"


def main():
    parser = argparse.ArgumentParser(description="Convert formulas and write report file for iterative fixing")
    parser.add_argument("--input", "-i", type=Path, default=DEFAULT_INPUT, help="Input real_formulas.json path")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT, help="Output report file path")
    args = parser.parse_args()

    path = args.input.resolve()
    out_path = args.output.resolve()
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        cases = json.load(f)

    if not isinstance(cases, list):
        cases = []

    lines: list[str] = []
    manual_count = 0
    parse_error_count = 0

    for case in cases:
        name = case.get("name", "?")
        dax = case.get("dax", "")
        resolution_map = case.get("resolution_map") or {}

        ast, parse_error = parse_formula(dax)
        if parse_error:
            lines.append(f"--- {name} ---")
            lines.append(f"  DAX: {dax}")
            lines.append(f"  Parse error: {parse_error}")
            lines.append("")
            parse_error_count += 1
            continue

        result = convert_with_status(ast, resolution_map)
        status = result.get("conversion_status", "")
        bq = result.get("bq_formula")
        message = result.get("message") or ""

        lines.append(f"--- {name} ---")
        lines.append(f"  DAX:   {dax}")
        if status == "manual":
            lines.append("  Output: manual")
            if message:
                lines.append(f"  Message: {message}")
            manual_count += 1
        else:
            lines.append(f"  Output: {bq}")
        lines.append("")

    lines.append(f"(Total: {len(cases)} formulas | manual: {manual_count} | parse errors: {parse_error_count})")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report written to {out_path} ({len(cases)} formulas, {manual_count} manual, {parse_error_count} parse errors)")


if __name__ == "__main__":
    main()
