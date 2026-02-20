# Transformer & Generator – Implementation Plan

**Version:** 1.0  
**Status:** For review  
**Prerequisite:** Requirements approved (`plan/transformer_requirements.md`)

---

## 1. Overview

This plan defines **scope**, **contract**, and **implementation order** for the Power BI → Looker Transformer and Generator. The pipeline is:

```
metadata_model.json  →  [Transformer]  →  semantic_layer_artifact.json  →  [Generator]  →  LookML
```

- **Transformer:** All mapping and formula logic; outputs the artifact.
- **Generator:** Pure renderer (Jinja2); no business logic.
- **Source of truth for behavior:** `plan/transformer_requirements.md`.
- **Source of truth for metadata shape:** `canonical_output/*/metadata_model.json` (see §2).

---

## 2. Contract

### 2.1 Input (Transformer)

- **File:** `metadata_model.json` (canonical format from step 3).
- **Structure (single datasource):**
  - `datasources[0].id`, `datasources[0].name`
  - `datasources[0].connection.database`, `datasources[0].connection.schema`
  - `datasources[0].tables[]` — `id`, `name`, `schema`, `table_name`, `table_type` (`physical` | `calculated`), `formula` (for calculated)
  - `datasources[0].table_relationships[]` — `from_table`, `to_table`, `join_type`, `on_columns[]` (`from`, `to`)
  - `datasources[0].fields[]` — flat list; each has `id`, `name`, `field_type`, `data_type`, `source_table`, `source_column`, `aggregation`, `formula`, `formula_ast`, `formula_parse_error`, `is_calculated`, etc.
- **Transformer** groups fields by `source_table` to build one view per table. Uses first (or only) datasource.

### 2.2 Output (Transformer) = Artifact

- **File:** `semantic_layer_artifact.json`.
- **Schema:** As in requirements § "semantic_layer_artifact.json Schema".
- **Key fields:** `artifact_version`, `source`, `target`, `generated_at`, `project_name`, `database`, `schema`, `views[]`, `explores[]`, `conversion_summary`.
- **project_name:** Derived from datasource name (same cleanup rules as field names: lowercase, spaces/hyphens → underscores, etc.).
- **database / schema:** From `datasources[0].connection.database` and `.schema`.

### 2.3 Input (Generator)

- **Input:** The artifact (dict or loaded from `semantic_layer_artifact.json`).

### 2.4 Output (Generator)

- **Location:** Configurable output dir (e.g. `lookml_output/<report_name>/` or passed by script).
- **Files:**
  - **Views:** One file per view: `{view_name}.view.lkml` in `views/` subdir. **View name** = cleaned table name (same as artifact `view_name`).
  - **Model:** One model file. **Name:** `{project_name}.model.lkml` in `models/` subdir (single file for the whole project).
  - **Manifest:** `manifest.lkml` at output root. Content: minimal Looker manifest with `project_name` and include of the model file.
- **Measure two-step pattern:** For every artifact field with `field_type = measure`, the generator emits **two** LookML blocks in order: (1) **dimension** `{field_name}_measure` with the base sql (and type/value_format as needed); (2) **measure** `{field_name}` with the measure type and `sql: ${field_name}_measure ;;`. The artifact still has one field per measure; the generator implements the two-step pattern when rendering. See requirements §1 i.

### 2.5 Naming and deduplication

- **View name** = cleaned table name (lowercase, spaces/hyphens → underscores, strip special chars, leading digit → `_` prefix, reserved word → `_field` suffix).
- **Duplicate field names:** Resolved **within each view only**. First occurrence keeps clean name; subsequent get `_` + last 4 chars of field UUID.
- **Model file:** One file; name `{project_name}.model.lkml`.
- **Field name resolution (standard process):** Per view, final `field_name` is assigned only after cleanup + deduplication. A view-scoped resolution map (original name/id → final field_name) is built and used for formula conversion and any future references (dashboards, looks) so the same names are used everywhere. See requirements §a'.

---

## 3. Scope (in / out)

| In scope (Phase 1) | Out of scope |
|--------------------|--------------|
| Transformer: view generation (field cleanup, type mapping, labels, conversion_status, DAX AST → BigQuery formula) | Dashboard / visualization migration |
| Transformer: model generation (one explore per physical table, joins from table_relationships) | Time intelligence (TOTALYTD, etc.) — flag manual |
| Generator: Jinja2 templates for view, model, manifest | CALCULATE / ALL / ALLEXCEPT — flag manual |
| Config: field_type_mapping.yaml, looker_reserved_words.yaml, function_mapping.yaml | RELATED / RELATEDTABLE — flag manual |
| Integration: Step 4 in run_integration.py, `--skip-transformer` | Row-level security, bookmarks, report-level filters |
| Unit tests per requirements; fixtures from conftest or minimal JSON | |

---

## 4. Implementation order

### Phase A – Config and shared helpers

| # | Task | Deps | Notes |
|---|------|------|--------|
| A.1 | **config/field_type_mapping.yaml** — data_type_map, aggregation_to_measure_type, join_type_map, value_format_map per requirements. | — | See requirements § Config Files. |
| A.2 | **config/looker_reserved_words.yaml** — reserved_words list. | — | Used for field name cleanup. |
| A.3 | **config/function_mapping.yaml** — direct_mapping, special_mapping, unsupported; extend as needed from formula tests. | — | DAX → BigQuery function resolution. |
| A.4 | **Artifact Pydantic models** — SemanticLayerArtifact, View, Field, Explore, Join, ConversionSummary in `models/` (or transformer-specific module). Schema matches requirements. | — | Typed artifact for transformer output and generator input. |

### Phase B – Transformer: field and view building blocks

| # | Task | Deps | Notes |
|---|------|------|--------|
| B.1 | **Field name cleanup** — `clean_field_name(name, reserved_words)` and `deduplicate_field_names(fields)` (within-view; UUID suffix). Module: e.g. `transformer/semantic/field_cleanup.py`. | A.2 | Lowercase, spaces/hyphens → `_`, strip special chars, leading digit → `_`, reserved → `_field`. |
| B.2 | **Field type mapping** — `map_field_type(data_type, aggregation)` from YAML; returns field_type, looker_type, timeframes (if dimension_group), value_format, conversion_status. | A.1 | dimension / dimension_group / measure + looker_type. |
| B.3 | **Formula converter (DAX AST → BigQuery)** — Recursive walk; direct_mapping / special_mapping / unsupported; VAR handling (inline vs CTE vs manual). **Accepts the view’s field name resolution map:** unqualified column refs are resolved via this map to the **final** field_name and emitted as `${field_name}` (e.g. `${total_revenue_4492}`); qualified refs use table + resolved column. Return formula + conversion_status + message. Module: e.g. `transformer/semantic/formula_converter.py`. | A.3, existing dax parser | Use AST from parser (e.g. FunctionCall, ColumnRef, BinOp). See requirements §a'. |
| B.4 | **View builder** — One view per table. **Standard process:** (1) Group metadata fields by source_table. (2) Apply cleanup then within-view deduplication to assign **final** field_name to each field. (3) Build **view-scoped field name resolution map** (original name / id → final field_name). (4) Run formula conversion with this map so calc field refs use final names. (5) Apply type mapping, field ordering (dimensions → dimension_groups → measures → calculated), datetime → dimension_group, calculated table handling. Measure fields remain a single artifact field each; two-step (dimension _measure + measure) is applied in Generator. Same final names used in artifact and (later) dashboards/looks. | B.1, B.2, B.3, A.4 | Output: list of View objects. Requirements §a'. |

### Phase C – Transformer: model (explores) and orchestrator

| # | Task | Deps | Notes |
|---|------|------|--------|
| C.1 | **Model/explore builder** — One explore per physical table; joins from table_relationships (join_type from YAML); sql_on using Looker `${view.field}` syntax; relationship default many_to_one, conversion_status partial. | A.1, A.4 | Exclude calculated tables from explores. |
| C.2 | **Conversion summary** — Count auto/partial/manual; list manual_fields (view_name, field_name, message). | B.4 | From all view fields. |
| C.3 | **Transformer orchestrator** — Load metadata_model (dict or path); take first datasource; build views (B.4), explores (C.1), conversion_summary (C.2); fill project_name, database, schema, generated_at; return SemanticLayerArtifact. Entry: `run(metadata_model: dict | Path) -> SemanticLayerArtifact`. | B.4, C.1, C.2, A.4 | `transformer/semantic/orchestrator.py` (or equivalent). |

### Phase D – Integration script (Step 4)

| # | Task | Deps | Notes |
|---|------|------|--------|
| D.1 | **process_one_report_transformer(report_out: Path)** — Read report_out / metadata_model.json; call run_transformer(metadata_model); write report_out / semantic_layer_artifact.json; on failure call _write_canonical_error(report_out, report_id, error, "transformer"). Return manifest entry dict. | C.3 | Same pattern as process_one_report_canonical; stage = "transformer". |
| D.2 | **step4_transformer(canonical_output_dir: Path) -> (ok_count, fail_count)** — Glob canonical_output_dir/*/metadata_model.json; for each report folder run process_one_report_transformer; collect manifest entries; write canonical_output_dir / _manifest.json; return counts. | D.1 | Can merge with existing manifest or overwrite; plan: write manifest with entries that include artifact path on success. |
| D.3 | **CLI and main()** — Add --skip-transformer; after step 3, if not skip: run step4_transformer(canonical_dir), print counts. | D.2 | Do not change steps 1–3. |

### Phase E – Generator

| # | Task | Deps | Notes |
|---|------|------|--------|
| E.1 | **Templates** — Jinja2: view template (dimension, dimension_group, measure blocks; comments for DAX and manual review); model template (explore, join blocks); manifest template (project_name, include). **Two-step measure pattern:** for each field with field_type=measure, emit (1) dimension `{field_name}_measure` with base sql/type/value_format, then (2) measure `{field_name}` with type and `sql: ${field_name}_measure`. Location: e.g. `generator/templates/` under package. | A.4 | Generator is renderer only; two-step is a fixed rendering rule. |
| E.2 | **Generator entry** — `write(artifact: SemanticLayerArtifact, output_dir: Path) -> list[str]` (paths written). Render views to views/{view_name}.view.lkml, model to models/{project_name}.model.lkml, manifest to manifest.lkml. | E.1 | No business logic; pass artifact to templates. |

### Phase F – Tests

| # | Task | Deps | Notes |
|---|------|------|--------|
| F.1 | **tests/transformer/** — test_field_name_cleanup.py, test_field_type_mapping.py, test_formula_converter.py, test_view_builder.py, test_model_builder.py, test_integration_transformer.py. Cases per requirements § Unit Tests. | B.1–C.3 | Use conftest/fixtures for shared metadata and artifact snippets. |
| F.2 | **tests/generator/** — test_view_generator.py, test_model_generator.py, test_integration_generator.py. Assert file count, content snippets (view name, DAX comment, manual review comment, timeframes, join block, manifest project_name). **Two-step measure:** for measure fields, assert both dimension `{field_name}_measure` and measure `{field_name}` with `sql: ${field_name}_measure` appear in view. | E.2 | Fixture: minimal artifact. |

---

## 5. Dependency summary

```
A.1–A.4 (config + artifact models)
    → B.1, B.2, B.3
    → B.4 (view builder)
    → C.1 (explore builder), C.2 (summary)
    → C.3 (orchestrator)
    → D.1 → D.2 → D.3 (integration)
B.4, C.1, C.2, C.3
    → F.1 (transformer tests)
E.1 → E.2
    → F.2 (generator tests)
```

---

## 6. Output locations (reminder)

- **Transformer (step 4):** Writes into existing report folder:
  - `canonical_output/<report_name>/semantic_layer_artifact.json`
  - On failure: `canonical_output/<report_name>/_error.json` (stage = "transformer").
- **Generator:** Not wired to run_integration in this plan; can be called by a separate script or later step that reads artifact and calls `write(artifact, output_dir)`. Output dir could be e.g. `canonical_output/<report_name>/lookml/` or a single combined LookML project.

---

## 7. Open point (optional)

- **manifest.lkml content:** Minimal definition: `project_name`, `manifest_version`, `application`, and include of the single model file. Can be tightened when Looker project layout is fixed.

---

**Approval:** Once this plan is approved, implementation should follow the task order above and keep `plan/transformer_requirements.md` as the behavioral spec.
