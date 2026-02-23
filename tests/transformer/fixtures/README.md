# Real-formula fixtures for formula converter

- **Input:** DAX formula string (in `real_formulas.json` as `dax`).
- **Output:** Each test/run shows **DAX → BQ** (or manual).

## Populate from canonical_output (recommended) or parsed_output

The fixture should be filled with **real DAX from your Power BI models**.

From repo root:

```bash
uv run python scripts/extract_formulas_from_parsed_output.py
```

**Primary source: canonical_output.** The script reads `canonical_output/<report_id>/metadata_model.json` and collects every `datasources[].fields[].formula`. **Fallback:** `parsed_output/` (each report’s `Model/database.json`), collects:
Output: `real_formulas.json` with `name` = `ReportId | TableName.FieldName`, `dax`, `resolution_map: {}`.

Options:

- `--canonical-output-dir` (default: canonical_output), `--parsed-output-dir`, `--output`

## Workflow: add templates or direct_mapping

1. Populate the fixture (see above; uses canonical_output by default).
2. Generate the conversion report: `uv run python scripts/show_formula_outputs.py`
   - Writes `tests/transformer/fixtures/formula_conversion_report.txt` with each DAX and its BQ output (or manual + message).
3. Open the report file; for each **manual** or wrong case, add a fix (templates or **direct_mapping** in `config/function_mapping.yaml`, or code handlers).
4. Re-run step 2 to refresh the report; repeat until most cases convert to BQ.

Optional: `pytest tests/transformer/test_formula_converter_real.py -v` to run tests. Use `--output` / `-o` to change the report path.

Optional: set `expected_bq` (exact) or `expected_bq_pattern` (substring) or `expected_status: "manual"` in the fixture to lock in behaviour.
