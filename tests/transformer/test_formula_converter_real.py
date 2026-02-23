"""Tests for formula converter: input = DAX formula, output = DAX + BQ (or manual).

- Input: DAX formula string (AST is built internally via parse_formula).
- Output: For each case we get BQ SQL or conversion_status=manual.
- Use failing/manual cases to add templates or direct_mapping in function_mapping.yaml
  until most formulas convert. Fixture: tests/transformer/fixtures/real_formulas.json.
"""

import json
from pathlib import Path

import pytest

from powerbi_to_looker.dax.parser import parse_formula
from powerbi_to_looker.transformer.views.formula_converter import convert_with_status

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
REAL_FORMULAS_PATH = FIXTURE_DIR / "real_formulas.json"


def _load_real_formulas():
    if not REAL_FORMULAS_PATH.exists():
        return []
    with open(REAL_FORMULAS_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("case", _load_real_formulas(), ids=lambda c: c.get("name", ""))
def test_real_formula_conversion(case):
    """Input: DAX formula string. Output: BQ SQL or manual. Parse to AST internally."""
    dax = case["dax"]
    resolution_map = case.get("resolution_map") or {}

    ast, parse_error = parse_formula(dax)
    assert parse_error is None, f"Parse failed for '{dax}': {parse_error}"
    assert ast is not None

    result = convert_with_status(ast, resolution_map)

    if case.get("expected_status") == "manual":
        assert result["conversion_status"] == "manual", result.get("message")
        return

    bq = result.get("bq_formula")
    assert bq is not None, f"Expected BQ output for '{dax}', got status={result.get('conversion_status')} message={result.get('message')}"

    if "expected_bq" in case:
        assert bq == case["expected_bq"], f"got: {bq}"
        return

    if "expected_bq_pattern" in case:
        pattern = case["expected_bq_pattern"]
        assert pattern in bq, f"expected '{pattern}' in: {bq}"
        return

    assert len(bq) > 0
