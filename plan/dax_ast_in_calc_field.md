# DAX AST in calc_field and canonical Field

**Purpose:** Parse each formula in calc_field with the DAX parser, attach AST or parse error to the canonical Field. Grammar and parser live under `src/powerbi_to_looker/dax/`.

---

## 1. Scope

- **Where:** Only in **calc_field** (calculated columns + model measures). Dimension and measure handlers do not parse DAX.
- **Contract:** For every field with a `formula`:
  - On parse success: `formula_ast` = serialized AST (dict), `formula_parse_error` = None.
  - On parse failure: `formula_ast` = None, `formula_parse_error` = short error message (string).
- **Canonical:** Two new optional fields on `Field`: `formula_ast`, `formula_parse_error`.

---

## 2. Architecture

```
Raw (expression) → calc_field.run()
       ↓
  For each formula:
    formula_ast, formula_parse_error = parse_formula(formula)
    Field(..., formula=formula, formula_ast=..., formula_parse_error=...)
```

- **Parser location:** `src/powerbi_to_looker/dax/` (parser + grammar `dax.lark`).
- **API:** `parse_formula(formula: str) -> tuple[dict | None, str | None]` → (ast_dict, error_message). Empty formula → (None, None).
- **Serialization:** AST is Pydantic models; we serialize to dict via `model_dump()` so canonical JSON (e.g. metadata_model.json) stays valid.

---

## 3. Error handling

- Catch all parser/transformer exceptions (Lark, Transformer, generic Exception).
- On any exception: return `(None, str(e))`; normalize to a short message (e.g. first line).
- Never set a partial AST; on failure only `formula_parse_error` is set.

---

## 4. Canonical Field changes

| Field                 | Type               | When set |
|-----------------------|--------------------|----------|
| formula_ast           | Optional[dict]     | Parse success; JSON-serializable AST. |
| formula_parse_error   | Optional[str]      | Parse failure; short message. |

Rule: if `formula` is set, exactly one of `formula_ast` or `formula_parse_error` is set (or both None if formula is empty after trim).

---

## 5. Files

- `src/powerbi_to_looker/dax/` — parser package (grammar + parser + `parse_formula`).
- `src/powerbi_to_looker/models/canonical.py` — add `formula_ast`, `formula_parse_error` to Field.
- `src/powerbi_to_looker/parser_normalizer/semantic/calc_field.py` — call `parse_formula`, set the two fields on each Field.

**Grammar extensions (for real-world PBI formulas):**
- **Case-insensitive function names:** `func_name` accepts FUNC_NAME or UNQUOTED_NAME so lowercase (e.g. `sum`) parses; AST normalizes to uppercase.
- **Hierarchy syntax:** `[Column].[Level]` or `Table[Column].[Level]` via optional `hierarchy_suffix`; `ColumnRef` has `hierarchy_level`.

See also: `plan/dimension_measure_classification.md`, `lark_test/dax_parser.py` (source of moved parser).
