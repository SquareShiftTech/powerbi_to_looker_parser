# Formula Converter: Refactor + Template-Based Support Plan

**Status:** For review and approval.  
**Requirements reference:** `plan/transformer_requirements.md` §f and §f.1.

---

## Part 1 — Refactoring (readability)

**Goal:** Same behavior, clearer structure. One entry point that dispatches by node type; no single 90-line function.

### 1.1 Target structure (same file: `transformer/views/formula_converter.py`)

| Function | Responsibility |
|----------|----------------|
| `convert(ast, resolution_map, config)` | Top-level only: null check → normalize node type → dispatch to one of the helpers below. No inline logic for column_ref/literal/binop/func. |
| `_normalize_node_type(ast)` | Return one of: `column_ref`, `literal`, `blank`, `binop`, `func`. Handles Pydantic vs test AST shape. |
| `_convert_column_ref(ast, res_map)` | Unqualified → `${field_name}` via res_map; qualified → `table.column`. |
| `_convert_literal(ast)` | Number, string, boolean, blank → BQ literal or NULL. |
| `_convert_binop(ast, res_map, cfg)` | Left/right via `convert()`; op via operator_mapping; return `(left op right)` or POW(left, right). |
| `_convert_function(ast, res_map, cfg)` | Resolution order: unsupported → extract_mapping → direct_mapping → (future: rewrite_templates, special_mapping) → unknown. Uses a small helper for template substitution. |
| `_apply_direct_template(template, args, res_map, cfg)` | Convert each arg with `convert()`, substitute `{0}`, `{1}`, … in template; return string. (Used by _convert_function.) |
| `_get_config()`, `_unsupported_list(cfg)` | Unchanged. |
| `clean_ref_name(name)` | Unchanged (used by column_ref). |
| `convert_with_status(ast, resolution_map)` | Unchanged; still calls `convert()` and catches exceptions. |

### 1.2 Steps

1. Add `_normalize_node_type(ast)` and move the normalization block from `convert` into it.
2. Add `_convert_column_ref`, `_convert_literal`, `_convert_binop`, `_convert_function` and move the corresponding branches from `convert` into them. Each helper calls `convert(..., res_map, cfg)` for child nodes where needed.
3. Add `_apply_direct_template(template, args, res_map, cfg)` and use it inside `_convert_function` for direct_mapping template substitution.
4. Reduce `convert()` to: if ast is None → "NULL"; cfg = config or _get_config(); node_type = _normalize_node_type(ast); then if node_type == "column_ref": return _convert_column_ref(...), elif "literal" or "blank": return _convert_literal(...), elif "binop": return _convert_binop(...), elif "func": return _convert_function(...); else return "NULL".
5. Run existing tests: `pytest tests/transformer/test_formula_converter.py -v`. All must pass with no behavior change.

### 1.3 Out of scope for refactor

- VAR/RETURN handling (not implemented yet).
- special_mapping / handler dispatch (optional later).
- New YAML sections or new tests in this step.

---

## Part 2 — Template-based support (majority of formulas)

**Goal:** Use only `direct_mapping` (and optionally a `rewrite_templates` section) so most real-report formulas convert without code handlers. Add templates for every function that currently appears as "Unknown" or manual and fits a fixed template.

### 2.1 Where templates live

- **Primary:** `config/function_mapping.yaml` → `direct_mapping` only for this plan. Template syntax: `"BQ_EXPR({0}, {1})"` with args converted and substituted.
- **Optional:** Add a `rewrite_templates` key in the same YAML and, in code, check it in `_convert_function` after `direct_mapping` (same substitution logic). If we add it, we can move “rewrite-style” entries (e.g. DIVIDE, IF) there for clarity; behavior unchanged.

### 2.2 Functions to add or confirm in direct_mapping

Already present (no change): COUNT, DISTINCTCOUNT, DIVIDE, IF, RANK, plus existing aggregation/math/text/logical.

Add the following so they no longer fall through to "Unknown function":

| DAX function | BigQuery template | Note |
|--------------|-------------------|------|
| BLANK | `NULL` | 0 args; already handled in code, add to YAML for consistency. |
| NULLIF | `NULLIF({0}, {1})` | |
| COALESCE | `COALESCE({0}, {1})` | 2-arg minimum; more args = more placeholders or leave to handler. |
| IFERROR | `IFNULL({0}, {1})` | |
| CONCATENATE | `CONCAT({0}, {1})` | |
| ROUND | `ROUND({0}, {1})` | DAX ROUND(number, decimals). |
| SELECTEDVALUE | `COALESCE(MAX({0}), {1})` | 2-arg approximation; document as partial. |
| ISBLANK | `({0} IS NULL OR {0} = '')` | |
| FORMAT | (optional) Simple case only, e.g. `FORMAT_DATE('%Y-%m-%d', {0})` for single date arg; else leave manual. |

**Not in direct_mapping (variable arity or context-dependent):**

- SWITCH — N WHEN clauses; keep for future special_mapping handler or document a single fixed-arity template if we add one.
- COUNTROWS — table context; handler or manual.
- AVERAGEX, SUMX, etc. — iterator semantics; handler or manual.
- FORMAT (complex) — format string mapping; leave manual or minimal template.

### 2.3 Code change for template-based support

- In `_convert_function`: resolution order remains **unsupported → extract_mapping → direct_mapping**.
- If we introduce `rewrite_templates`: after `direct_mapping`, if `name in cfg.get("rewrite_templates") or {}`, use same substitute-args-into-template logic and return. No new file; one extra lookup and the same `_apply_direct_template` (or inline substitution).
- Add the new entries above to `direct_mapping` in `function_mapping.yaml`. No new sections required unless we add `rewrite_templates`.

### 2.4 Validation

- Run `pytest tests/transformer/ -v`.
- After full pipeline run, spot-check generator output: fewer "Unknown function" for DIVIDE, IF, COUNT, DISTINCTCOUNT, RANK, NULLIF, COALESCE, IFERROR, CONCATENATE, ROUND, SELECTEDVALUE, ISBLANK (and FORMAT only where we add a simple template).

---

## Part 3 — Test cases from real formulas (reference)

- **Fixture:** Build a list of real DAX formulas (and `formula_ast` where available) from `canonical_output/**/metadata_model.json` (and optionally parsed_output).
- **Tests:** Load fixture; for each case call `convert(ast, resolution_map)` or `convert_with_status`; assert result matches expected BQ or a pattern (e.g. `"SAFE_DIVIDE" in result`).
- **Placement:** Either extend `tests/transformer/test_formula_converter.py` or add `tests/transformer/test_formula_converter_real.py` plus a fixture file under `tests/transformer/fixtures/`.

This part is specified in §f.1 (3) and will be implemented after Part 1 and Part 2.

---

## Implementation order

| Step | Task | Validation |
|------|------|------------|
| 1 | Refactor: add _normalize_node_type, _convert_* helpers, _apply_direct_template; slim convert() to dispatch only. | All existing formula_converter tests pass. |
| 2 | Add new direct_mapping entries (NULLIF, COALESCE, IFERROR, CONCATENATE, ROUND, SELECTEDVALUE, ISBLANK, BLANK; optional FORMAT). Optionally add rewrite_templates section and use it in _convert_function. | pytest; spot-check generator output. |
| 3 | Add real-formula fixture and tests per §f.1 (3). | New tests pass; refactor/template behavior locked in. |

---

## Approval

If you approve this plan, implementation will follow the order above. Requirements in `transformer_requirements.md` §f and §f.1 remain the source of truth; this document is the implementation plan for refactor and template-based support.
