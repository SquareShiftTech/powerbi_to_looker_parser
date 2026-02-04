# Transformer Plan: Canonical → LookML Terms

Canonical `MetadataModel` → LookML-ready dict for **view generator** and **model generator**. All configurable behaviour via YAML; code split into small modules for maintainability.

---

## 1. Output contract (for generators)

Transformer returns a single dict consumed by both generators:

```yaml
views:                    # list of view objects → one .view.lkml per view
  - view_name: order_details
    sql_table_name: "order_details"   # or from connection
    dimensions: [ ... ]
    measures: [ ... ]
  - view_name: orders
    ...

model:                    # → model.model.lkml
  connection: "powerbi_connection"
  explores:
    - name: order_details
      view: order_details
      label: "Order Details"
      joins:
        - name: orders
          view: orders
          type: left_outer
          sql_on: "${order_details.order_id} = ${orders.order_id}"
          relationship: many_to_one
    - name: orders
      view: orders
      joins: [ ... ]
```

- **View generator:** iterates `views`, renders `view.lkml.j2` per view.
- **Model generator:** uses `model`, renders `model.lkml.j2` with connection and explores (including joins).

---

## 2. View structure (per table)

One **view** per canonical **table**. Fields are grouped by `Field.source_table`; each view has:

### 2.1 Dimensions

| Key       | Source                    | Notes |
|----------|----------------------------|--------|
| `name`   | Sanitized field name       | Lowercase, underscores, no spaces (e.g. `order_date`) |
| `label`  | Original display name      | From `Field.name` (e.g. "Order Date") |
| `type`   | LookML dimension type      | From YAML: canonical `data_type` → LookML type |
| `sql`    | Expression                 | `${TABLE}.column_name` or `DATE(${TABLE}.column_name)` for dates |
| `primary_key` | Optional               | Yes for primary key dimension if identified |
| `date_info`   | Optional (dates only) | `datetype`, `timeframes` for drill-down |

### 2.2 Measures

| Key            | Source / rule |
|----------------|----------------|
| `name`         | Sanitized measure name |
| `label`        | Original `Field.name` |
| `type`         | LookML measure type: `count`, `count_distinct`, `sum`, `avg`, `min`, `max`, or `number` (custom SQL) |
| `sql`          | For simple: `${dimension_name}` (reuse base dimension). For calculated: SQL expression from formula conversion. |
| `value_format` | From YAML defaults or per measure |
| `format`       | Optional (e.g. decimal_2) |
| `description`  | Optional; fallback for unconverted DAX |

### 2.3 Field name and label

- **name:** Used in LookML (dimension/measure key). Sanitize: `name.replace(" ", "_").lower()` and truncate if needed; ensure uniqueness per view.
- **label:** Human-readable; use `Field.name` as-is or from YAML label overrides. Generator/template must support `label` in view output.

All mappings (canonical type → LookML type, aggregation → measure type, etc.) come from **YAML** (see §6).

---

## 3. Date special handling

- Canonical `data_type` in `date` | `datetime` → LookML dimension `type: time`.
- **SQL:** Start with `${TABLE}.column_name`; optional wrapper (e.g. `DATE(...)`) from YAML or dialect later.
- **Extra LookML (optional):** `datetype: date` | `datetime`, `timeframes: [day, week, month, quarter, year]` for drill. Configure in YAML (e.g. `date_handling.timeframes`, `date_handling.datetype_by_canonical`).
- Transformer module dedicated to date handling keeps logic in one place.

---

## 4. Measure strategy: base dimension + measure reuse

- **Simple measure** (single-column aggregation): Ensure a **dimension** exists for the base column (e.g. `sales` with `sql: ${TABLE}.sales`). Measure then uses `type: sum`, `sql: ${sales}`.
- **No duplicate SQL:** Base dimension defined once; measure references it by name.
- **Config:** Which aggregations get a base dimension can be default (always) or driven by YAML (e.g. `measures.reuse_base_dimension: true`).

---

## 5. Calculated field handling

- **Input:** `Field.formula` (DAX), `Field.is_calculated: true`.
- **Output:** LookML measure with `type: number` and `sql: <expression>`.
- **Reference resolution:** Formula references like `[Total Sales]`, `[Order_Date]` must become LookML refs: `${total_sales}`, `${order_date}`. Transformer builds a **name map** per view (Power BI / display name → LookML field name) from dimensions + measures in that view (and optionally from joined views).
- **Conversion:** Pattern-based (Option 1/2) or later DAX parser. Result is a SQL string using `${field_name}` refs. Unconvertible formulas: put DAX in `description`, set `sql: NULL` or a safe placeholder.
- **Dependencies:** Use canonical `depends_on` or formula parse to order measures so dependencies are defined before use.

---

## 6. Model file: explores and joins

- **Explores:** One explore per view (1:1 with view name) as the primary entry; or one “main” explore with all others as joins. Start with **one explore per view** and add joins from that view to related tables.
- **Joins from canonical:** `TableRelationship` → LookML join:
  - `from_table` = view that “owns” the join (base view for that explore).
  - `to_table` = joined view.
  - `on_columns` → `sql_on: ${from_view.from_col} = ${to_view.to_col}` (and repeat for multiple columns if needed).
  - `join_type` → Looker join type from YAML (e.g. LEFT → `left_outer`, INNER → `inner`).
  - Optional: `relationship: many_to_one` / `one_to_many` from YAML or heuristic.

All join type and relationship mappings in **YAML**.

---

## 7. YAML config (transformer)

**File:** `powerbi_to_looker/config/canonical_lookml_mapping.yaml`

Single place for all canonical → LookML configurable behaviour.

| Section | Purpose |
|---------|---------|
| **dimension_types** | canonical `data_type` → LookML dimension type (string, number, time, yesno) |
| **measure_types** | canonical `aggregation` → LookML measure type (sum, count, count_distinct, avg, min, max) |
| **join_types** | canonical `join_type` (LEFT, INNER, …) → Looker join type (left_outer, inner, …) |
| **date_handling** | datetype (date vs datetime), timeframes list, optional SQL wrapper |
| **measures** | defaults: value_format, format; reuse_base_dimension flag |
| **naming** | sanitization rules (max length, allowed chars); optional label overrides |
| **dax_to_sql** (optional) | Pattern list or regex → measure type + sql template for formula conversion (Option 2) |

See `canonical_lookml_mapping.yaml` in config for the exact keys. Transformer code **only** reads this (and env overrides if needed); no hardcoded type or join mappings.

---

## 8. Module structure (transformer)

Keep one entry point (`to_lookml_terms`), but split logic into small modules so no single file becomes huge.

```
transformer/
  __init__.py           # re-export to_lookml_terms, optionally submodules
  semantic_layer.py     # orchestrator: load config, group fields by table, call builders, return views + model
  view_builder.py       # build one view dict (dimensions + measures) from a table + its fields
  dimensions.py         # canonical Field → LookML dimension entry (name, label, type, sql, date_info)
  measures.py           # canonical Field → LookML measure entry (name, label, type, sql; base-dimension reuse)
  dates.py              # date/datetime handling: type, sql, date_info from YAML
  formula_to_sql.py     # DAX formula → LookML sql (pattern-based); resolve [Ref] to ${ref}
  model_builder.py      # from tables + table_relationships → model.explores with joins
  config.py             # load canonical_lookml_mapping.yaml (or delegate to config.load_lookml_mapping)
```

- **semantic_layer.py:** Load YAML; for each table get fields; call `view_builder.build_view(table, fields, config)`; collect views; call `model_builder.build_model(datasource, config)`; return `{ views, model }`.
- **view_builder.py:** For each field, dispatch to dimensions/measures; for measures with formula call formula_to_sql; assemble dimensions list and measures list; return view dict.
- **config.py:** Thin wrapper around `config.load_lookml_mapping()` so transformer does not depend on config package internals, or use `config.load_lookml_mapping` directly if preferred.

This keeps each file focused and testable.

---

## 9. Implementation plan (phases)

### Phase 1: Config and wiring
- Add `canonical_lookml_mapping.yaml` with dimension_types, measure_types, join_types, date_handling, measures defaults.
- Add `config.load_lookml_mapping()` (and optional `config.get_transformer_config()`); ensure YAML is bundled (MANIFEST.in).
- In transformer, load this config and pass it through (semantic_layer still returns stub views/model but reads config).

### Phase 2: View structure and types
- Implement **dimensions** and **dates** modules: canonical Field → dimension entry using YAML (name, label, type, sql; date_info for time).
- Implement **view_builder**: group fields by table, build dimensions + measures lists (measures still simple: type from aggregation, sql from `${TABLE}.column` or placeholder).
- **semantic_layer:** One view per table; no more stub dimensions/measures; use real fields and YAML types.
- Update **view.lkml.j2** to output `label` when present and `sql_table_name` from view.

### Phase 3: Model and joins
- Implement **model_builder**: from datasource.tables + table_relationships build explores with joins; join type and sql_on from YAML.
- **semantic_layer:** Call model_builder, attach connection; return full model dict.
- Update **model.lkml.j2** to output joins (join name, view, type, sql_on, relationship).

### Phase 4: Measures and base dimension
- Implement **measures** module: simple measures use aggregation → measure type from YAML; ensure base dimension exists and measure sql references it (`${base_dim}`).
- view_builder: create base dimensions for measure columns when not already present; measures reference them.

### Phase 5: Calculated fields (formula → SQL)
- Implement **formula_to_sql** (pattern-based): SUM(Table[Col]), COUNT/DISTINCTCOUNT, DIVIDE([A],[B],0), etc.; resolve [Name] to `${lookml_name}` via name map.
- view_builder: build name map per view; for calculated measures call formula_to_sql; on failure set description to DAX and sql to placeholder.
- Optional: add **dax_to_sql** section in YAML for pattern list (Option 2).

### Phase 6: Polish
- Labels everywhere; primary_key detection if needed; value_format/format from YAML.
- Tests per module (dimensions, measures, dates, formula_to_sql, model_builder, semantic_layer integration).

---

## 10. Dependencies and entry points

- **Transformer depends on:** `models.canonical` (MetadataModel, Datasource, Field, Table, TableRelationship), `config` (load_lookml_mapping).
- **Generator depends on:** nothing from transformer except the **output shape** (views + model dict). No change to generator beyond template updates for label, sql_table_name, joins.
- **migration_engine:** Already calls `to_lookml_terms(metadata)` then `generate(lookml_terms, output_dir)`. No change once output shape is stable.

---

## 11. Summary

| Topic | Decision |
|-------|----------|
| Output | Single dict: `views` (list of view dicts), `model` (connection + explores with joins). |
| Config | All configurable behaviour in `canonical_lookml_mapping.yaml`; loader in config. |
| Modules | semantic_layer (orchestrator), view_builder, dimensions, measures, dates, formula_to_sql, model_builder, config. |
| Field naming | name = sanitized; label = original name (or YAML override). |
| Dates | type: time; optional date_info (datetype, timeframes); SQL from YAML/dialect. |
| Measures | Base dimension + measure sql referencing it; calculated → formula_to_sql with name map. |
| Model | One explore per view; joins from table_relationships; join type/sql_on from YAML. |

Implementation order: Phase 1 (YAML + loader) → Phase 2 (views, dimensions, dates) → Phase 3 (model, explores, joins) → Phase 4 (measures, base dim) → Phase 5 (formula_to_sql) → Phase 6 (polish, tests) → Phase 7 (SQL dialect / BigQuery).

---

## 12. SQL dialect (BigQuery target)

Even when the **source** is a different type (e.g. SQL Server), the generated LookML may target a **BigQuery** connection. Formulas and any raw SQL we emit should be in BigQuery format so the LookML runs correctly against BigQuery.

### 12.1 Config: sql_dialect

- **YAML:** Add `sql_dialect: bigquery` (or `generic`) in `canonical_lookml_mapping.yaml`. Default `generic` for backward compatibility.
- **Formulas:** When `sql_dialect: bigquery`, use BigQuery-native functions (e.g. `SAFE_DIVIDE`, `IFNULL`) in formula_to_sql output.
- **Dates:** When BigQuery, set `date_handling.sql_wrapper: "DATE(%s)"` (or `SAFE_CAST(%s AS DATE)`) so dimension SQL for date columns is BigQuery-compatible.
- **Joins:** Join `sql_on` we emit is LookML `${view.dim} = ${view.dim}`; Looker compiles this to the connection’s dialect. No change needed for join text.
- **sql_table_name:** Sent to the DB. For BigQuery we may want `dataset.table` or `project.dataset.table` instead of `schema.table`. Optional: when `sql_dialect: bigquery`, build from `bigquery.dataset` (and optional `bigquery.project`) in YAML, e.g. `{dataset}.{table_name}`.

### 12.2 formula_to_sql (BigQuery)

- **DIVIDE(A, B, 0):** Generic: `${a} / NULLIF(${b}, 0)`. BigQuery: `IFNULL(SAFE_DIVIDE(${a}, ${b}), 0)` (or `SAFE_DIVIDE(${a}, ${b})` if NULL is acceptable).
- Future date/string/conditional patterns: use BigQuery function names when dialect is bigquery.

### 12.3 Summary

| Item | generic | bigquery |
|------|---------|----------|
| DIVIDE | `${a} / NULLIF(${b}, 0)` | `IFNULL(SAFE_DIVIDE(${a}, ${b}), 0)` |
| date_handling.sql_wrapper | null | `DATE(%s)` (or SAFE_CAST) |
| sql_table_name | schema.table from connection | optional: dataset.table from config |

Implementation: Phase 7 — add `sql_dialect` and optional `bigquery` section to YAML; formula_to_sql branches on dialect; semantic_layer (or view_builder) uses dialect for sql_table_name when configured.
