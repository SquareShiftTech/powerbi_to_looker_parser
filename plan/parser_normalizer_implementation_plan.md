# Parser & Normalizer – Implementation Plan

**Version:** 1.0  
**Status:** For review  
**Prerequisite:** Requirements approved (`plan/parser_normalizer_requirements.md`)

---

## 1. Overview

This plan breaks implementation into **phases** and **tasks** so the team can review and then implement in order. Semantic layer is Phase 1; visualization/report is Phase 2.

---

## 2. Phase 1 – Semantic model → canonical

### 2.1 Deliverables

- Loader: path or dict → raw `{"model", "report"}` per report.
- Semantic mapping: raw["model"] → `MetadataModel` (one per report).
- Config: `semantic_mapping.yaml` (or extend `powerbi_canonical_mapping.yaml`) with all rules.
- Enums for field_type, data_type, aggregation, datasource_type (validate against YAML).
- Orchestrator: loop report folders → load → semantic run → write canonical_output per report; exception handling with error file/manifest.
- Documentation: `plan/semantic_model_canonical_mapping.md` (source → target, model changes, why).

### 2.2 Semantic handler interface and code flow

- **Interface:** All semantic handlers implement a common **protocol**: `can_handle(raw: dict) -> bool` and `run(raw: dict) -> T`. Orchestrator sends the **full raw** model to each handler; no pre-splitting.
- **Return types:** Tables handler returns a **TablesResult** (tables, table_relationships, connection). Dimension, measure, and calculated-field handlers each return **list[Field]** (own type); calculated-field output must include **formula**.
- **Code flow (single datasource):**
  1. Tables handler: `can_handle(raw)` then `run(raw)` → TablesResult (tables, table_relationships, connection).
  2. Dimension handler: `can_handle(raw)` then `run(raw)` → list[Field].
  3. Measure handler: `can_handle(raw)` then `run(raw)` → list[Field].
  4. Calculated-field handler: `can_handle(raw)` then `run(raw)` → list[Field].
  5. Orchestrator **merges** all field lists into one; builds **one** Datasource (tables, table_relationships, connection from TablesResult; fields = merged list); builds **one** MetadataModel with `datasources = [that Datasource]`.
- **Errors:** Handlers raise on failure; orchestrator catches and writes `_error.json` (success=false, error, stage). See §4 and requirements §8.

### 2.3 Task breakdown (Phase 1)

| # | Task | Owner | Deps | Notes |
|---|------|--------|------|--------|
| 1.1 | **Canonical model changes** — Add `Connection.connection_provider` (optional str) for datasource type (BigQuery, SQL Server, etc.). Use Table/Field `extended_properties` for hierarchy, format_string. Update `models/canonical.py`. | — | — | See `plan/semantic_model_canonical_mapping.md` §4. |
| 1.2 | **YAML semantic config** — Add/update `config/semantic_mapping.yaml` (or powerbi_canonical_mapping): data_types, column_types (incl. calculatedTableColumn), measure_aggregation, summarizeBy, relationship default, datasource_type detection keys. | — | — | Reuse existing powerbi_canonical_mapping.yaml or split. |
| 1.3 | **Enums** — Define enums (FieldType, DataType, Aggregation, JoinType, DatasourceType). Load YAML and validate keys against enums. Place in `parser_normalizer` or `common`. | — | 1.2 | Used by semantic handlers. |
| 1.4 | **Semantic handler protocol** — Define Protocol (e.g. `SemanticHandlerProtocol`) with `can_handle(raw)` and `run(raw)`. Define `TablesResult` (or equivalent) for tables handler return type. All handlers implement this protocol. | — | 1.1 | See requirements §3.2, §3.3. |
| 1.5 | **Loader** — Implement `load(path_or_metadata)`. If path: detect parsed_output root vs single report folder; read Model/database.json and Report/definition into raw. If dict: return as-is. Support GCS path if in scope. | — | — | `parser_normalizer/loader.py`. |
| 1.6 | **tables.py** — Implement handler: `can_handle(raw)` (model has tables); `run(raw)` → TablesResult(tables, table_relationships, connection). From raw["model"]; use YAML for defaults. | 1.1, 1.2, 1.3, 1.4 | Returns own type (TablesResult). |
| 1.7 | **dimension.py** — Implement handler: `can_handle(raw)` (model has tables with columns); `run(raw)` → list[Field] (dimension/calculated_field). data_type, field_type from YAML; formula/source when present. | 1.1, 1.2, 1.3, 1.4 | Returns list[Field]. |
| 1.8 | **measure.py** — Implement handler: `can_handle(raw)` (model has measures); `run(raw)` → list[Field] (measure). aggregation from DAX via YAML; formula stored; is_calculated when expression present. | 1.2, 1.3, 1.4 | Returns list[Field]. |
| 1.9 | **calc_field.py** — Implement handler: `can_handle(raw)` (model has calculated columns/measures); `run(raw)` → list[Field] (calculated fields **with formula**). Ensure field_type and is_calculated set. | 1.7, 1.8 | Returns list[Field]; formula required. |
| 1.10 | **orchestrator (semantic)** — For each handler: if `can_handle(raw)` then `run(raw)`; merge dimension + measure + calc_field lists; build one Datasource (tables, table_relationships, connection from tables handler; fields = merged); return one MetadataModel. Catch handler errors; propagate with stage. | 1.6–1.9 | `parser_normalizer/semantic/orchestrator.py`. |
| 1.11 | **Orchestrator (top-level)** — Loop: for each report folder in parsed_output, load(raw) → semantic.run(raw) → write canonical_output/<report_id>/metadata_model.json. On exception: write canonical_output/<report_id>/_error.json with success=false, error, stage. Continue with next report. Optional: _manifest.json. | 1.5, 1.10 | Entry in parser_normalizer/__init__.py or separate run script. Output shape: requirements §8. |
| 1.12 | **Tests** — Unit tests for loader (path detection, read model/report); each handler (can_handle, run) with minimal raw snippets. One integration test: one full report folder → canonical MetadataModel shape and key fields. | 1.5–1.11 | pytest; use fixtures from parsed_output or minimal JSON. |
| 1.13 | **Documentation** — Finalize `plan/semantic_model_canonical_mapping.md` (mapping table, model changes, why). | 1.1 | For maintainability. |

### 2.4 Dependencies (Phase 1)

```
1.1 Canonical model
1.2 YAML config    1.3 Enums    1.4 Protocol + TablesResult
     \    \          /                  /
      \    \        /                  /
1.5 Loader ────────+──────────────────+──> 1.6 tables
                                             1.7 dimension
                                             1.8 measure
                                             1.9 calc_field
                                                    |
                                                    v
                                             1.10 semantic orchestrator (can_handle → run; merge fields)
                                                    |
                                                    v
                                             1.11 top-level orchestrator (loop + output + errors)
1.12 Tests (parallel to 1.6–1.11)
1.13 Docs (after 1.1)
```

### 2.5 Output structure (canonical_output)

```
canonical_output/
  <report_folder_name_1>/
    metadata_model.json      # MetadataModel (semantic)
    # later: report_metadata.json
  <report_folder_name_2>/
    metadata_model.json
  <report_folder_name_3>/
    _error.json              # {"success": false, "report_id": "...", "error": "...", "stage": "semantic"}
  _manifest.json             # optional: list of report_id, success, path, error (if failed)
```

**Output JSON contract:** Final shapes for `metadata_model.json`, `_error.json`, and optional `_manifest.json` are defined in **requirements §8** (Output JSON contract). Implementation must conform so tests and consumers have a single contract.

---

## 3. Phase 2 – Visualization / report mapping

### 3.1 Deliverables

- Map raw["report"] to ReportMetadata or DashboardMetadata (report = dashboard).
- Config: `visualization_mapping.yaml` (visual types, query roles).
- visualization.py and dashboard.py implemented; orchestrator calls them and adds to canonical bundle.
- Write report_metadata.json (or dashboard_metadata.json) per report in canonical_output.

### 3.2 Task breakdown (Phase 2) — high level

| # | Task | Deps |
|---|------|------|
| 2.1 | visualization_mapping.yaml: visualType → canonical type; queryState roles → mapping_role. | — |
| 2.2 | visualization.py: raw["report"] → list of Visualization/Chart (id, type, position, data_mappings, filters). | 2.1 |
| 2.3 | dashboard.py: raw["report"] → ReportMetadata or DashboardMetadata (pages, components). | 2.2 |
| 2.4 | Orchestrator: after semantic, run visualization + dashboard; add to bundle; write report_metadata.json. | 1.10, 2.2, 2.3 |
| 2.5 | Tests and docs for visualization mapping. | 2.1–2.4 |

*(Detailed Phase 2 tasks can be broken down after Phase 1 review.)*

---

## 4. Exception handling (detailed)

- **Loader failure** (missing file, invalid JSON): catch in orchestrator; write `_error.json` with `stage: "load"`, message in `error`.
- **Semantic mapping failure** (missing required key, validation error): catch in orchestrator; write `_error.json` with `stage: "semantic"`, message in `error`.
- **Optional:** `_manifest.json` at canonical_output root: `[{ "report_id": "...", "success": true, "metadata_model": "path" }, { "report_id": "...", "success": false, "error": "...", "stage": "semantic" }]` for easy inspection.
- Do not re-raise; log and continue to next report.

---

## 5. Definition of done (Phase 1)

- [ ] All Phase 1 tasks 1.1–1.13 implemented and reviewed.
- [ ] Requirements (parser_normalizer_requirements.md) semantic section and interface/single-datasource flow satisfied.
- [ ] Semantic handler protocol (can_handle, run; each returns own type) implemented; orchestrator sends full raw and merges fields.
- [ ] Semantic mapping doc (semantic_model_canonical_mapping.md) complete and model changes applied.
- [ ] Unit tests for loader and each handler (can_handle, run); one integration test for full report → MetadataModel.
- [ ] Orchestrator loops parsed_output and writes canonical_output per report; failures recorded in _error.json; output JSON conforms to requirements §8.

---

## 6. References

- `plan/parser_normalizer_requirements.md`
- `plan/semantic_model_canonical_mapping.md`
- `docs/code_layout.md`
- `.cursor/rules/pipeline-and-layout.mdc`
