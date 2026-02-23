# PowerBI → Looker Transformer & Generator Requirements

## Overview

Convert a Power BI metadata model (`metadata_model.json`) into LookML views and models via a two-stage pipeline:

```
metadata_model.json
        ↓
  [Transformer Module]
        ↓
  semantic_layer_artifact.json  (canonical intermediate)
        ↓
  [Generator Module]
        ↓
  views/*.view.lkml
  models/*.model.lkml
  manifest.lkml
```

---

## Guiding Principles

- Follow existing project code structure, patterns and conventions — do not invent new structure
- All configuration lives in YAML files — no hardcoded mappings in code
- Every field gets a `conversion_status`: `auto`, `partial`, or `manual`
- Every formula that cannot be auto-converted gets a human-readable `message` explaining why
- Original DAX formula always preserved as a comment in generated LookML
- Generator is purely a renderer — all logic lives in Transformer

---

## Stage 1 — Transformer Module

**Input:** `metadata_model.json`
**Output:** `semantic_layer_artifact.json`

### 1. View Generation

One view produced per table in the metadata model.

#### a. Field Name Cleanup

- Lowercase all characters
- Replace spaces and hyphens with underscores
- Strip all special characters except underscore
- If name starts with a digit → prefix with underscore
- If cleaned name matches a Looker reserved word → append `_field`
- If cleanup causes duplicate names within the same view:
  - Append last 4 characters of the field UUID to make it unique
  - e.g., `revenue` and `Revenue` both clean to `revenue` → `revenue_4492` and `revenue_dc3b`

#### a'. Field name resolution (standard process)

A single, view-scoped process ensures the same **final** field names are used in formulas, the artifact, LookML, and (later) dashboards and looks.

1. **Order of operations (per view):**  
   - Collect all fields for the view (grouped by `source_table`).  
   - Apply **cleanup** to each field’s original name → base clean name.  
   - Apply **within-view deduplication** so every field gets a **final unique** `field_name` (e.g. `total_revenue`, `total_revenue_4492`).  
   - No other code path assigns or changes these names; this is the only naming pipeline.

2. **Resolution map (per view):**  
   - Build a map from “how the field is identified in DAX / metadata” (e.g. original name, or original name + field id when disambiguating) to the **final** `field_name`.  
   - This map is the single source of truth for resolving any reference to a view field.

3. **Use of the map:**  
   - **Formula conversion:** When converting a calculated field’s DAX (e.g. unqualified `[Total Revenue]`), look up the reference in the view’s resolution map and emit the **final** `field_name` in Looker syntax (e.g. `${total_revenue_4492}`). Never emit a raw or only-cleaned name that might not match the view’s final name.  
   - **Artifact and Generator:** Everywhere else (artifact `field_name`, generated LookML, and future dashboard/look references) use only these same final names.  
   - This way, calculated fields, views, and future features (dashboards, looks) all reference the same stable `field_name` values.

#### b. Field Type Mapping

Mapping defined in `config/field_type_mapping.yaml`.

| Power BI data_type | Power BI aggregation | Looker field_type | Looker type |
|---|---|---|---|
| string | null | dimension | string |
| number | null | dimension | number |
| number | SUM | measure | sum |
| number | AVG | measure | average |
| number | COUNT | measure | count |
| number | DISTINCTCOUNT | measure | count_distinct |
| number | MIN | measure | min |
| number | MAX | measure | max |
| boolean | null | dimension | yesno |
| datetime | null | dimension_group | time |
| currency | SUM | measure | sum + value_format usd |
| percent | null | measure | number + value_format percent |

#### c. Label

- `label` = original field name from Power BI before any cleanup

#### d. Description

- `null` for all fields in this version — placeholder must exist in schema

#### e. Conversion Status and Message

Every field gets `conversion_status`: `auto`, `partial`, or `manual` and a `message` when not auto.

#### f. Formula Generation (DAX AST to BigQuery SQL)

**Target:** BigQuery only. All emitted SQL is valid BigQuery (e.g. `SAFE_DIVIDE`, `EXTRACT(unit FROM col)`). Multi-dialect support is out of scope for now.

**Config:** `config/function_mapping.yaml` with:
- **direct_mapping** — Function name → BigQuery expression. Either a simple name (args passed through as `FUNC(arg1, arg2)`) or a template string with `{0}`, `{1}`, … for positional args. Recursively convert each arg and substitute.
- **extract_mapping** — DAX functions that become `EXTRACT(unit FROM col)` in BigQuery (e.g. YEAR, MONTH, DAY).
- **rewrite_templates** (optional) — Same as direct_mapping but for formulas that need a structural rewrite (e.g. DIVIDE → `IFNULL(SAFE_DIVIDE({0}, {1}), {2})`, IF → `CASE WHEN {0} THEN {1} ELSE {2} END`). Implemented either as entries in direct_mapping or a separate section; converter substitutes converted args into the template.
- **special_mapping** — Named handler in code for variable arity or non-template rewrites (e.g. SWITCH with N WHEN clauses). Call handler with (args, resolution_map, config).
- **unsupported** — List of DAX functions that cannot be auto-converted; set conversion_status = manual and message from config.

**Function resolution order (per FunctionCall node):**
1. **unsupported** — if function in list → conversion_status = manual, message from config.
2. **extract_mapping** — if present → emit `EXTRACT(unit FROM converted_arg)`.
3. **direct_mapping** — if present → apply template or `FUNC(args)`; recurse on args.
4. **rewrite_templates** — if used as separate section, same as direct (template + args).
5. **special_mapping** — if present → call named handler in code.
6. **Not found** — conversion_status = manual, message = "Unknown function: X".

**VAR/RETURN:** Inline if scalar; CTE if one VAR references another; manual if contains CALCULATE/FILTER/SUMMARIZE. (Implementation may follow in a later phase.)

**Unqualified column refs** (e.g. `[Total Revenue]`) are resolved via the **view’s field name resolution map** (§a') to the **final** `field_name`. Emit in Looker syntax, e.g. `${total_revenue}` or `${total_revenue_4492}`. Never emit raw or only-cleaned names that might not match the view.

---

#### f.1 Formula converter improvements (pending approval)

The following requirements are proposed for implementation. **Approval is requested** before coding.

**1. Refactor formula converter for readability**

- The formula converter module (`transformer/views/formula_converter.py`) shall be refactored so that:
  - A single top-level `convert(ast, resolution_map, config)` only normalizes node type and dispatches to small helper functions.
  - One helper per AST node kind: e.g. `_convert_column_ref`, `_convert_literal`, `_convert_binop`, `_convert_function`.
  - Function-call resolution (unsupported → extract → direct → special → unknown) lives inside `_convert_function`; template substitution may be in a small `_apply_direct_template` (or equivalent).
- No new frameworks or visitor pattern; same file, same config, clearer control flow.

**2. Template-based support for majority of formulas**

- Template-based rewrites (via `direct_mapping` and optionally a dedicated `rewrite_templates` section in `function_mapping.yaml`) shall be the **primary** mechanism for DAX → BigQuery.
- Extend `direct_mapping` (and implement `rewrite_templates` in code if used) so that the **majority** of formulas seen in real reports convert automatically. Add templates for common functions that are currently "Unknown" or manual where a fixed template fits (e.g. NULLIF, COALESCE, IFERROR, CONCATENATE, SELECTEDVALUE approximation, ROUND; SWITCH only where a fixed-arity pattern is documented).
- Code handlers (`special_mapping`) remain only for variable arity or non-template cases (e.g. SWITCH with N WHENs, COUNTROWS with table context).

**3. Test cases from real source formulas**

- Add a test dataset and tests that use **real DAX formulas** from the repo to assert conversion to BigQuery:
  - **Source:** Formulas (and when available `formula_ast`) from `canonical_output/<report_id>/metadata_model.json` and/or `parsed_output/...` (e.g. Model/database.json). Collect a representative list (e.g. 10–20 cases) covering DIVIDE, IF, COUNT, DISTINCTCOUNT, SWITCH, FORMAT, CALCULATE (expect manual), etc.
  - **Fixture:** A structured fixture (e.g. `tests/transformer/fixtures/real_formulas.json` or YAML) listing: report/source, field identifier, original formula or AST reference, optional `resolution_map`, and expected BigQuery SQL (or a pattern to assert, e.g. `"SAFE_DIVIDE" in result`).
  - **Tests:** In `tests/transformer/test_formula_converter.py` (or a dedicated `test_formula_converter_real.py`): load fixture, for each case call `convert(ast, resolution_map)` (or `convert_with_status`), assert result matches expected BQ or pattern. Ensures refactor and template additions do not regress real-world formulas.

**Implementation order (after approval):** (1) Refactor converter for readability; (2) extend templates to support majority of formulas; (3) add real-formula fixture and tests.

---

#### g. Datetime Field to dimension_group

Fields with data_type = datetime or name containing date/time/timestamp/created/updated/modified become dimension_group with timeframes: [raw, time, date, week, month, quarter, year].

#### h. Calculated Table Handling

table_type = "calculated" generates derived_table block. Flag manual if formula uses CALCULATE/FILTER.

#### i. Measure two-step pattern (LookML)

For every field with **field_type = measure**, generate **two** LookML blocks in the view (two-step pattern):

1. **Dimension** named `{field_name}_measure`  
   - Holds the base expression (same `sql` as the measure’s underlying expression, e.g. `${TABLE}.column` or the converted formula).  
   - Used as the base for aggregation and reusable as a dimension elsewhere.

2. **Measure** named `field_name`  
   - Has the measure **type** (sum, average, count, count_distinct, min, max, etc.) and **value_format** as mapped.  
   - **sql:** `${field_name}_measure` (references the dimension above).

**Example (auto-converted):**
```lookml
# Original DAX: SUM(marketing_campaign_data[Revenue])
# Converted: auto
dimension: total_revenue_measure {
  sql: ${TABLE}.Revenue ;;
  type: number
  value_format_name: usd
}

measure: total_revenue {
  type: sum
  sql: ${total_revenue_measure} ;;
  value_format_name: usd
}
```

**Example (manual):**
```lookml
# [MANUAL REVIEW REQUIRED]
# Original DAX: CALCULATE(DISTINCTCOUNT(...), FILTER(...))
dimension: customers_who_converted_measure {
  sql: "" ;;
}

measure: customers_who_converted {
  type: count_distinct
  sql: ${customers_who_converted_measure} ;;
}
```

The artifact still has **one** field per Power BI measure; the **Generator** is responsible for emitting the two blocks (dimension `{field_name}_measure`, then measure `field_name`) when rendering.

---

### 2. Model Generation

#### a. Explore Generation

One explore per physical table. Joins from table_relationships. Relationship defaults to many_to_one with partial status.

#### b. Field Ordering

Sequence: dimensions → dimension_groups → measures → calculated dimensions → calculated measures. Alphabetical within each group.

#### c. Duplicate Field Name Handling

First occurrence keeps clean name. Subsequent occurrences append _ + last 4 chars of UUID.

---

## semantic_layer_artifact.json Schema

```json
{
  "artifact_version": "1.0",
  "source": "powerbi",
  "target": "looker",
  "generated_at": "<iso timestamp>",
  "project_name": "<derived from datasource name>",
  "database": "<from connection.database>",
  "schema": "<from connection.schema>",
  "views": [
    {
      "view_name": "marketing_campaign_data",
      "label": "Marketing Campaign Data",
      "source_table": "marketing_campaign_data",
      "view_type": "physical",
      "sql_table_name": "`project.schema.table`",
      "derived_table_sql": null,
      "conversion_status": "auto",
      "message": null,
      "fields": [
        {
          "field_name": "customer_id",
          "original_name": "CustomerID",
          "field_type": "dimension",
          "looker_type": "number",
          "label": "Customer ID",
          "description": null,
          "sql": "${TABLE}.CustomerID",
          "value_format": null,
          "timeframes": null,
          "hidden": false,
          "tags": [],
          "conversion_status": "auto",
          "message": null,
          "original_formula": null,
          "bq_formula": null
        },
        {
          "field_name": "date",
          "original_name": "Date",
          "field_type": "dimension_group",
          "looker_type": "time",
          "label": "Date",
          "description": null,
          "sql": "${TABLE}.Date",
          "value_format": null,
          "timeframes": ["raw", "time", "date", "week", "month", "quarter", "year"],
          "hidden": false,
          "tags": [],
          "conversion_status": "auto",
          "message": null,
          "original_formula": null,
          "bq_formula": null
        },
        {
          "field_name": "total_revenue",
          "original_name": "Total Revenue",
          "field_type": "measure",
          "looker_type": "sum",
          "label": "Total Revenue",
          "description": null,
          "sql": "${TABLE}.Revenue",
          "value_format": "usd",
          "timeframes": null,
          "hidden": false,
          "tags": [],
          "conversion_status": "auto",
          "message": null,
          "original_formula": "SUM(marketing_campaign_data[Revenue])",
          "bq_formula": "SUM(marketing_campaign_data.revenue)"
        },
        {
          "field_name": "customers_who_converted",
          "original_name": "Customers Who Converted",
          "field_type": "measure",
          "looker_type": "count_distinct",
          "label": "Customers Who Converted",
          "description": null,
          "sql": "",
          "value_format": null,
          "timeframes": null,
          "hidden": false,
          "tags": [],
          "conversion_status": "manual",
          "message": "CALCULATE with FILTER cannot be auto-converted. Suggested: COUNT(DISTINCT CASE WHEN conversions > 0 THEN customer_id END)",
          "original_formula": "CALCULATE(DISTINCTCOUNT(...), FILTER(...))",
          "bq_formula": null
        }
      ]
    }
  ],
  "explores": [
    {
      "explore_name": "marketing_campaign_data",
      "label": "Marketing Campaign Data",
      "description": null,
      "joins": [
        {
          "join_name": "customers",
          "join_type": "left_outer",
          "relationship": "many_to_one",
          "sql_on": "${marketing_campaign_data.customer_id} = ${customers.customer_id}",
          "conversion_status": "partial",
          "message": "Relationship type defaulted to many_to_one - verify cardinality"
        }
      ]
    }
  ],
  "conversion_summary": {
    "total_fields": 0,
    "auto": 0,
    "partial": 0,
    "manual": 0,
    "manual_fields": []
  }
}
```

---

## Stage 2 — Generator Module

**Input:** `semantic_layer_artifact.json`
**Output:** LookML files

Use Jinja2 templates in `generator/templates/`. One template per file type. Generator is a pure renderer — no logic, no decisions.

### Inline Comments in Generated LookML

Measures use the **two-step pattern** (dimension `{field_name}_measure` then measure `field_name`). See §1 View Generation, **i. Measure two-step pattern**.

Auto measure (two blocks):
```
# Original DAX: SUM(marketing_campaign_data[Revenue])
# Converted: auto
dimension: total_revenue_measure {
  sql: ${TABLE}.Revenue ;;
  type: number
  value_format_name: usd
}

measure: total_revenue {
  type: sum
  sql: ${total_revenue_measure} ;;
  value_format_name: usd
}
```

Manual measure (two blocks):
```
# [MANUAL REVIEW REQUIRED]
# Original DAX: CALCULATE(DISTINCTCOUNT(...), FILTER(...))
# Reason: CALCULATE with FILTER cannot be auto-converted
# Suggested: COUNT(DISTINCT CASE WHEN conversions > 0 THEN customer_id END)
dimension: customers_who_converted_measure {
  sql: "" ;;
}

measure: customers_who_converted {
  type: count_distinct
  sql: ${customers_who_converted_measure} ;;
}
```

---

## Integration Script Updates (run_integration.py)

Follow exact same patterns already in run_integration.py. Do not change existing steps 1-3.

### Output location

Same canonical_output_dir, same report_name subfolder. No new folder.

```
canonical_output/
  <report_name>/
    metadata_model.json              <- step 3 (existing)
    dashboard_metadata.json          <- step 3 (existing)
    semantic_layer_artifact.json     <- step 4 (new)
    _error.json                      <- if step 4 failed
  _manifest.json
```

### New import

```python
from powerbi_to_looker.transformer.semantic.orchestrator import run as run_transformer
```

### New function — process_one_report_transformer

Same pattern as process_one_report_canonical:
- Reads: report_out / metadata_model.json
- Calls: run_transformer(metadata_model)
- Writes: report_out / semantic_layer_artifact.json
- On failure: calls _write_canonical_error (existing helper)
- Returns: manifest entry dict {report_id, success, error?, stage?, artifact?}

### New function — step4_transformer

```python
def step4_transformer(canonical_output_dir: Path) -> tuple[int, int]:
    # Glob canonical_output_dir/*/metadata_model.json
    # For each: run process_one_report_transformer
    # Write _manifest.json
    # Return (ok_count, fail_count)
```

### New CLI argument

```
--skip-transformer    Stop after step 3 (skip transformer)
```

### main() step 4 block

```python
# Step 4 - Transformer
if args.skip_transformer:
    print("Step 4: Skipped (--skip-transformer).")
    return
print("Step 4: Transformer - metadata_model.json -> semantic_layer_artifact.json ...")
ok4, fail4 = step4_transformer(canonical_dir)
print(f"  Transformer: {ok4} ok, {fail4} failed")
```

---

## Unit Tests

Follow the exact same test patterns and conventions already used in the project.

### Test File Structure

```
tests/
  transformer/
    test_field_name_cleanup.py
    test_field_type_mapping.py
    test_formula_converter.py
    test_view_builder.py
    test_model_builder.py
    test_integration_transformer.py
  generator/
    test_view_generator.py
    test_model_generator.py
    test_integration_generator.py
```

---

### test_field_name_cleanup.py

```python
def test_spaces_to_underscores():
    assert clean_field_name("Sales Amount") == "sales_amount"

def test_hyphens_to_underscores():
    assert clean_field_name("Sales-Amount") == "sales_amount"

def test_uppercase_to_lowercase():
    assert clean_field_name("CustomerID") == "customerid"

def test_special_chars_stripped():
    assert clean_field_name("Revenue ($)") == "revenue_"

def test_leading_digit_prefixed():
    assert clean_field_name("2024_sales") == "_2024_sales"

def test_reserved_word_appended():
    assert clean_field_name("date") == "date_field"
    assert clean_field_name("count") == "count_field"
    assert clean_field_name("sum") == "sum_field"

def test_already_clean_passes_through():
    assert clean_field_name("customer_id") == "customer_id"

def test_duplicate_names_get_uuid_suffix():
    fields = [
        {"name": "Revenue", "id": "aaa-bbb-ccc-4492"},
        {"name": "revenue", "id": "xxx-yyy-zzz-dc3b"},
    ]
    result = deduplicate_field_names(fields)
    assert result[0]["field_name"] == "revenue_4492"
    assert result[1]["field_name"] == "revenue_dc3b"
```

---

### test_field_type_mapping.py

```python
def test_string_maps_to_dimension():
    result = map_field_type(data_type="string", aggregation=None)
    assert result.field_type == "dimension"
    assert result.looker_type == "string"

def test_number_with_sum_maps_to_measure():
    result = map_field_type(data_type="number", aggregation="SUM")
    assert result.field_type == "measure"
    assert result.looker_type == "sum"

def test_number_with_distinctcount_maps_to_count_distinct():
    result = map_field_type(data_type="number", aggregation="DISTINCTCOUNT")
    assert result.field_type == "measure"
    assert result.looker_type == "count_distinct"

def test_datetime_maps_to_dimension_group():
    result = map_field_type(data_type="datetime", aggregation=None)
    assert result.field_type == "dimension_group"
    assert result.looker_type == "time"
    assert result.timeframes == ["raw", "time", "date", "week", "month", "quarter", "year"]

def test_boolean_maps_to_yesno():
    result = map_field_type(data_type="boolean", aggregation=None)
    assert result.looker_type == "yesno"

def test_unknown_data_type_falls_back_to_string():
    result = map_field_type(data_type="exotic_type", aggregation=None)
    assert result.looker_type == "string"
    assert result.conversion_status == "partial"
```

---

### test_formula_converter.py

```python
def test_sum_direct_mapping():
    ast = {"type": "func", "name": "SUM",
           "args": [{"type": "column_ref", "table": "sales", "column": "Revenue"}]}
    assert convert(ast) == "SUM(sales.revenue)"

def test_divide_maps_to_safe_divide():
    result = convert(divide_ast_fixture)
    assert "SAFE_DIVIDE" in result
    assert "IFNULL" in result

def test_if_maps_to_case_when():
    result = convert(if_ast_fixture)
    assert "CASE WHEN" in result
    assert "THEN" in result
    assert "ELSE" in result
    assert "END" in result

def test_switch_true_maps_to_multi_case_when():
    result = convert(switch_true_ast_fixture)
    assert result.count("WHEN") >= 2
    assert "ELSE" in result

def test_year_maps_to_extract():
    ast = {"type": "func", "name": "YEAR",
           "args": [{"type": "column_ref", "table": "sales", "column": "Date"}]}
    assert convert(ast) == "EXTRACT(YEAR FROM sales.date)"

def test_month_maps_to_extract():
    ast = {"type": "func", "name": "MONTH",
           "args": [{"type": "column_ref", "table": "sales", "column": "Date"}]}
    assert convert(ast) == "EXTRACT(MONTH FROM sales.date)"

def test_concatenate_maps_to_concat():
    ast = {"type": "func", "name": "CONCATENATE",
           "args": [
               {"type": "column_ref", "table": None, "column": "First"},
               {"type": "column_ref", "table": None, "column": "Last"}
           ]}
    assert convert(ast) == "CONCAT(first, last)"

def test_calculate_is_unsupported():
    ast = {"type": "func", "name": "CALCULATE", "args": []}
    result = convert_with_status(ast)
    assert result.conversion_status == "manual"
    assert result.bq_formula is None
    assert "CALCULATE" in result.message

def test_unknown_function_is_manual():
    ast = {"type": "func", "name": "MADEUPFUNC", "args": []}
    result = convert_with_status(ast)
    assert result.conversion_status == "manual"
    assert "MADEUPFUNC" in result.message

def test_binop_ampersand_maps_to_pipe_concat():
    ast = {"type": "binop", "op": "&",
           "left": {"type": "literal", "value": "Hello"},
           "right": {"type": "literal", "value": " World"}}
    assert convert(ast) == "('Hello' || ' World')"

def test_binop_not_equal_maps_to_bang_equal():
    ast = {"type": "binop", "op": "<>",
           "left": {"type": "column_ref", "table": None, "column": "Status"},
           "right": {"type": "literal", "value": "Deleted"}}
    assert "!=" in convert(ast)

def test_binop_always_wrapped_in_parens():
    ast = {"type": "binop", "op": "+",
           "left": {"type": "literal", "value": 1},
           "right": {"type": "literal", "value": 2}}
    assert convert(ast) == "(1 + 2)"

def test_var_scalar_is_inlined_no_cte():
    result = convert(scalar_var_ast_fixture)
    assert "WITH" not in result

def test_var_referencing_var_produces_cte():
    result = convert(chained_var_ast_fixture)
    assert "WITH" in result

def test_var_with_calculate_is_manual():
    result = convert_with_status(var_with_calculate_ast_fixture)
    assert result.conversion_status == "manual"

def test_unqualified_column_ref_uses_looker_syntax():
    ast = {"type": "column_ref", "table": None, "column": "Total Revenue"}
    result = convert(ast, view_fields=["total_revenue"])
    assert result == "${total_revenue}"

def test_qualified_column_ref_uses_table_dot_column():
    ast = {"type": "column_ref", "table": "marketing_campaign_data", "column": "Revenue"}
    assert convert(ast) == "marketing_campaign_data.revenue"

def test_nested_functions_recurse_correctly():
    ast = {"type": "func", "name": "DIVIDE", "args": [
        {"type": "func", "name": "SUM",
         "args": [{"type": "column_ref", "table": "sales", "column": "Revenue"}]},
        {"type": "func", "name": "COUNT",
         "args": [{"type": "column_ref", "table": "sales", "column": "OrderID"}]},
        {"type": "literal", "value": 0}
    ]}
    result = convert(ast)
    assert "SAFE_DIVIDE" in result
    assert "SUM" in result
    assert "COUNT" in result

def test_literal_number_emitted_correctly():
    assert convert({"type": "literal", "value": 42.0}) == "42"

def test_literal_string_single_quoted():
    assert convert({"type": "literal", "value": "Hello"}) == "'Hello'"

def test_blank_maps_to_null():
    assert convert({"type": "func", "name": "BLANK", "args": []}) == "NULL"
```

---

### test_view_builder.py

```python
def test_physical_table_has_sql_table_name():
    view = build_view(physical_table_fixture)
    assert view.sql_table_name is not None
    assert view.derived_table_sql is None

def test_calculated_table_has_derived_table_sql():
    view = build_view(calculated_table_fixture)
    assert view.derived_table_sql is not None
    assert view.sql_table_name is None

def test_field_ordering_dimensions_before_measures():
    view = build_view(mixed_fields_fixture)
    types = [f.field_type for f in view.fields]
    last_dim = max((i for i, t in enumerate(types) if t == "dimension"), default=-1)
    first_measure = min((i for i, t in enumerate(types) if t == "measure"), default=9999)
    assert last_dim < first_measure

def test_datetime_field_becomes_dimension_group():
    view = build_view(datetime_field_fixture)
    date_field = next(f for f in view.fields if f.original_name == "Date")
    assert date_field.field_type == "dimension_group"
    assert "year" in date_field.timeframes
    assert "month" in date_field.timeframes

def test_auto_converted_field_has_bq_formula():
    view = build_view(simple_sum_fixture)
    field = next(f for f in view.fields if f.original_name == "Total Revenue")
    assert field.conversion_status == "auto"
    assert field.bq_formula is not None

def test_unsupported_formula_field_has_manual_status():
    view = build_view(calculate_field_fixture)
    field = next(f for f in view.fields if "CALCULATE" in (f.original_formula or ""))
    assert field.conversion_status == "manual"
    assert field.bq_formula is None
    assert field.message is not None

def test_field_label_is_original_name():
    view = build_view(physical_table_fixture)
    field = next(f for f in view.fields if f.field_name == "customer_id")
    assert field.label == "CustomerID"

def test_duplicate_field_names_deduplicated():
    view = build_view(duplicate_field_name_fixture)
    names = [f.field_name for f in view.fields]
    assert len(names) == len(set(names))
```

---

### test_model_builder.py

```python
def test_one_explore_per_physical_table():
    explores = build_explores(metadata_fixture)
    physical_count = sum(1 for t in metadata_fixture.tables if t.table_type == "physical")
    assert len(explores) == physical_count

def test_calculated_table_excluded_from_explores():
    explores = build_explores(metadata_with_calculated_table_fixture)
    names = [e.explore_name for e in explores]
    assert "customer_exposure_summary" not in names

def test_left_join_maps_to_left_outer():
    explores = build_explores(metadata_with_left_join_fixture)
    assert explores[0].joins[0].join_type == "left_outer"

def test_inner_join_maps_to_inner():
    explores = build_explores(metadata_with_inner_join_fixture)
    assert explores[0].joins[0].join_type == "inner"

def test_join_sql_on_uses_looker_field_syntax():
    explores = build_explores(metadata_with_join_fixture)
    sql_on = explores[0].joins[0].sql_on
    assert sql_on.startswith("${")
    assert "} = ${" in sql_on

def test_relationship_defaults_to_many_to_one_with_partial():
    explores = build_explores(metadata_with_join_fixture)
    join = explores[0].joins[0]
    assert join.relationship == "many_to_one"
    assert join.conversion_status == "partial"
```

---

### test_integration_transformer.py

End-to-end: metadata_model.json to semantic_layer_artifact.json

```python
def test_transformer_runs_without_error(metadata_model_fixture):
    artifact = run_transformer(metadata_model_fixture)
    assert artifact is not None

def test_all_views_present(metadata_model_fixture):
    artifact = run_transformer(metadata_model_fixture)
    metadata_table_names = {t.table_name for t in metadata_model_fixture.datasources[0].tables}
    artifact_view_names = {v.view_name for v in artifact.views}
    assert metadata_table_names == artifact_view_names

def test_every_field_has_conversion_status(metadata_model_fixture):
    artifact = run_transformer(metadata_model_fixture)
    for view in artifact.views:
        for field in view.fields:
            assert field.conversion_status in ("auto", "partial", "manual")

def test_every_calculated_field_has_original_formula(metadata_model_fixture):
    artifact = run_transformer(metadata_model_fixture)
    for view in artifact.views:
        for field in view.fields:
            if field.bq_formula or field.conversion_status == "manual":
                assert field.original_formula is not None

def test_manual_field_has_no_bq_formula(metadata_model_fixture):
    artifact = run_transformer(metadata_model_fixture)
    for view in artifact.views:
        for field in view.fields:
            if field.conversion_status == "manual":
                assert field.bq_formula is None
                assert field.message is not None

def test_conversion_summary_totals_correct(metadata_model_fixture):
    artifact = run_transformer(metadata_model_fixture)
    s = artifact.conversion_summary
    assert s.auto + s.partial + s.manual == s.total_fields

def test_artifact_written_to_correct_path(tmp_path):
    report_out = tmp_path / "some_report"
    report_out.mkdir()
    (report_out / "metadata_model.json").write_text(valid_metadata_json)
    process_one_report_transformer(report_out)
    assert (report_out / "semantic_layer_artifact.json").exists()

def test_error_json_written_on_bad_input(tmp_path):
    report_out = tmp_path / "bad_report"
    report_out.mkdir()
    (report_out / "metadata_model.json").write_text("not valid json {{{{")
    process_one_report_transformer(report_out)
    assert (report_out / "_error.json").exists()
```

---

### test_view_generator.py

```python
def test_one_view_file_per_view(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    view_files = list((tmp_path / "views").glob("*.view.lkml"))
    assert len(view_files) == len(artifact_fixture.views)

def test_view_file_contains_correct_view_name(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    content = (tmp_path / "views" / "marketing_campaign_data.view.lkml").read_text()
    assert "view: marketing_campaign_data" in content

def test_calculated_field_has_dax_comment(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    content = (tmp_path / "views" / "marketing_campaign_data.view.lkml").read_text()
    assert "# Original DAX:" in content

def test_manual_field_has_manual_review_comment(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    content = (tmp_path / "views" / "marketing_campaign_data.view.lkml").read_text()
    assert "# [MANUAL REVIEW REQUIRED]" in content

def test_dimension_group_has_timeframes_block(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    content = (tmp_path / "views" / "marketing_campaign_data.view.lkml").read_text()
    assert "timeframes:" in content
    assert "year" in content
    assert "month" in content

def test_auto_field_sql_is_not_empty(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    content = (tmp_path / "views" / "marketing_campaign_data.view.lkml").read_text()
    # manual fields have empty sql, auto fields should not
    assert content.count('sql: "" ;;') == content.count("# [MANUAL REVIEW REQUIRED]")
```

---

### test_model_generator.py

```python
def test_model_file_produced(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    model_files = list((tmp_path / "models").glob("*.model.lkml"))
    assert len(model_files) == 1

def test_manifest_produced(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    assert (tmp_path / "manifest.lkml").exists()

def test_manifest_contains_project_name(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    content = (tmp_path / "manifest.lkml").read_text()
    assert "project_name:" in content
    assert artifact_fixture.project_name in content

def test_explore_present_in_model(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    content = list((tmp_path / "models").glob("*.model.lkml"))[0].read_text()
    assert "explore:" in content

def test_join_block_present_in_model(artifact_fixture, tmp_path):
    generate(artifact_fixture, output_dir=tmp_path)
    content = list((tmp_path / "models").glob("*.model.lkml"))[0].read_text()
    assert "join:" in content
    assert "sql_on:" in content
    assert "type:" in content
    assert "relationship:" in content
```

---

## Config Files

### config/field_type_mapping.yaml

```yaml
data_type_map:
  string: string
  number: number
  datetime: time
  boolean: yesno
  currency: sum
  percent: number
  integer: number
  decimal: number
  binary: string

aggregation_to_measure_type:
  SUM: sum
  AVG: average
  AVERAGE: average
  COUNT: count
  COUNTA: count
  COUNTROWS: count
  DISTINCTCOUNT: count_distinct
  MIN: min
  MAX: max

join_type_map:
  LEFT: left_outer
  INNER: inner
  FULL: full_outer
  RIGHT: right_outer

value_format_map:
  currency: usd
  percent: percent_2
  decimal_2: "0.00"
  integer: "0"
```

### config/looker_reserved_words.yaml

```yaml
reserved_words:
  - date
  - time
  - count
  - sum
  - max
  - min
  - average
  - number
  - string
  - type
  - label
  - group
  - order
  - filter
  - view
  - model
  - explore
  - join
  - measure
  - dimension
  - sql
  - hidden
  - primary_key
  - foreign_key
  - all
  - select
  - from
  - where
  - having
  - by
  - as
  - on
  - in
  - not
  - and
  - or
  - is
  - null
  - true
  - false
```

---

## Conversion Summary Report

```
==================================================
TRANSFORMER SUMMARY
==================================================
Total views:      4
Total fields:     47

Conversion status:
  Auto:           38  (80.9%)
  Partial:         4  ( 8.5%)
  Manual:          5  (10.6%)

Manual review required:
  [marketing_campaign_data] customers_who_converted
    -> CALCULATE with FILTER cannot be auto-converted
  [campaign_products] conversion_rate_by_exposure
    -> SUMMARIZE produces virtual table - needs derived table
==================================================
```

---

## Out of Scope (Phase 1)

- Dashboard and visualization migration (Phase 2)
- Time intelligence functions (TOTALYTD, SAMEPERIODLASTYEAR etc.) — flag as manual
- CALCULATE / ALL / ALLEXCEPT — flag as manual
- RELATED / RELATEDTABLE — flag as manual
- Row-level security migration
- Power BI bookmarks and report-level filters
