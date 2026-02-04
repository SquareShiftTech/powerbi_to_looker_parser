# YAML Rules and Mapping Config

Per architecture: YAML for rule/configuration definitions, Python for transformation logic. Canonical YAML holds **Power BI → canonical** only; **canonical → LookML** is transformer concern.

---

## 1. Canonical layer (Power BI → canonical)

**File:** e.g. `powerbi_to_looker/config/powerbi_canonical_mapping.yaml` or `rules/powerbi_canonical.yaml`.

| Section | Purpose |
|--------|----------|
| **data_types** | Power BI `dataType` → canonical `data_type` (string, number, datetime, date, boolean) |
| **column_types** | Power BI `columnType` → canonical `field_type` (dimension \| calculated_field) |
| **relationship.join_type** | Power BI relationship → canonical `join_type` (default LEFT; optional per cardinality) |
| **measure_aggregation** | DAX / Power BI measure → canonical `aggregation` (SUM, AVG, COUNT, MIN, MAX); default null when not inferrable |
| **defaults** | Fallbacks for missing/unknown (e.g. data_type: string, join_type: LEFT) |

**Do not include:** canonical → Looker/LookML mappings.

See [plan/canonical_builder.md](canonical_builder.md) §9.

---

## 2. Transformer layer (canonical → LookML)

**File:** `powerbi_to_looker/config/canonical_lookml_mapping.yaml` (see [plan/transformer_plan.md](transformer_plan.md)).

| Section | Purpose |
|--------|----------|
| **dimension_types** | Canonical data_type → LookML dimension type (string, number, time, yesno) |
| **measure_types** | Canonical aggregation → LookML measure type (sum, avg, count, etc.) |
| **join_types** | Canonical join_type → Looker join type (LEFT → left_outer, INNER → inner) |
| **date_handling** | datetype, timeframes, optional sql_wrapper |
| **measures** | value_format, format, reuse_base_dimension |
| **naming** | max_name_length, sanitize |

Transformer loads this via `config.load_lookml_mapping()` and uses it instead of hardcoded lookups.

---

## 3. Things to be added (implementation)

1. **Create** `powerbi_canonical_mapping.yaml` with: data_types, column_types, relationship.join_type, measure_aggregation, defaults.
2. **Canonical builder:** Load this YAML and use it for all enum/mapping lookups; no hardcoded Power BI or canonical enums in Python.
3. **Transformer:** Use `canonical_lookml_mapping.yaml` for canonical → LookML (dimension_types, measure_types, join_types, date_handling, measures, naming).
4. **Transformer code:** Load via `config.load_lookml_mapping()`; use in semantic_layer and submodules instead of hardcoded dicts.

See [plan/folder_structure.md](folder_structure.md) for package layout and where config lives.
