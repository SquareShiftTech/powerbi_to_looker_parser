# Parser & Normalizer – Requirements Document

**Version:** 1.0  
**Status:** For review  
**Input:** `parsed_output` (collector output)  
**Output:** Canonical model (semantic + visualization/dashboard)

---

## 1. Objective

Parse and map the **parsed_output** (Power BI metadata from collector) into the **Canonical Model** with no transformation logic. This layer only maps raw metadata to canonical structures. Transformation (e.g. formula-to-SQL, hierarchy expansion) is handled in a separate **Transformer** layer.

- **Semantic layer model** → canonical `MetadataModel` (datasources, tables, relationships, fields).
- **Dashboard/visualization model** → canonical `ReportMetadata` / `DashboardMetadata` (report = dashboard in other BI tools; Power BI Report maps to this).

---

## 2. Scope

### 2.1 In scope

- **Input:** `parsed_output` — folder per report containing:
  - `Model/database.json` (semantic model: tables, columns, measures, relationships, partitions).
  - `Report/definition/` (report definition, pages, visuals).
- **Output:** Canonical model(s) per report, written to **canonical_output** (one subfolder or file set per report).
- **Configuration:** All mapping rules in YAML (multiple files allowed: e.g. `semantic_mapping.yaml`, `visualization_mapping.yaml`). Enums in code validate mappings against YAML.
- **Orchestrator:** Loop over each report folder in `parsed_output`; for each report, parse metadata → generate canonical model → store in **canonical_output** for that report.
- **Exception handling:** If parsing/mapping fails for a report, record the failure in **canonical_output** so it is visible (e.g. error manifest or per-report error file with reason).

### 2.2 Out of scope

- No processing beyond mapping (no DAX evaluation, no SQL generation, no business logic).
- No transformation logic (that belongs in Transformer).
- Canonical models remain BI-source agnostic (no Power BI–specific fields in canonical; use `extended_properties` for source-specific details).

---

## 3. Functional Requirements

### 3.1 Loader

| ID | Requirement | Priority |
|----|-------------|----------|
| L1 | Accept input as **dict** (in-memory raw) or **path** (local directory or GCS). | Must |
| L2 | When path points to **parsed_output root** (multiple report folders): discover each report subfolder. | Must |
| L3 | When path points to **single report folder** (e.g. `parsed_output/ReportName_id/`): load that report only. | Must |
| L4 | Load `Model/database.json` into raw structure (e.g. `raw["model"]`). | Must |
| L5 | Load Report definition (report.json, pages.json, page.json, visual.json per page/visual) into raw structure (e.g. `raw["report"]`). | Must |
| L6 | Return a single **raw** dict per report: `{"model": <object>, "report": <object>}`. No transformation. | Must |

### 3.2 Semantic handler interface

All semantic handlers (tables, dimension, measure, calculated field) **implement a common interface**. The orchestrator sends the **full raw data model** to each handler; no pre-splitting.

| ID | Requirement | Priority |
|----|-------------|----------|
| I1 | **Protocol:** Each handler implements `can_handle(raw: dict) -> bool` and `run(raw: dict) -> T` where `T` is that handler’s own return type. | Must |
| I2 | **Full raw:** Orchestrator passes the **same full raw** (e.g. `raw["model"]` or full `raw`) to every handler. Handlers decide via `can_handle(raw)` whether they can process it (e.g. “model has tables”, “model has columns”, “model has measures”). | Must |
| I3 | **Own return type:** Tables handler returns a **TablesResult** (or equivalent): `tables`, `table_relationships`, `connection`. Dimension handler returns `list[Field]` (dimensions). Measure handler returns `list[Field]` (measures). Calculated-field handler returns `list[Field]` (calculated fields); **calculated-field metadata must include `formula`**. | Must |
| I4 | **Errors:** Handlers must not swallow failures. On unexpected data or mapping failure, **raise** an exception (with clear message and optionally stage) or return a structured error. Orchestrator **catches** and writes `_error.json` so every failure is visible in canonical_output. | Must |

### 3.3 Single datasource structure and code flow

We support **single datasource** per Power BI model (one .pbix → one Datasource). The **canonical structure** and **code flow** must match.

| ID | Requirement | Priority |
|----|-------------|----------|
| D1 | **Single Datasource:** One `Datasource` contains: `tables`, `table_relationships`, `connection`, and `fields` (one flat list). Relationships are maintained at **Datasource** level in `table_relationships` (table-to-table; `from_table`, `to_table`, `on_columns`). | Must |
| D2 | **Fields:** All dimensions, measures, and calculated fields live in **one list** `Datasource.fields`. Each `Field` has `field_type` (dimension | measure | calculated_field), `source_table`, and when applicable `formula`, `is_calculated`, `aggregation`. Filter by `field_type` when only dimensions, only measures, or only calculated fields are needed. | Must |
| D3 | **Code flow:** Implementation must follow the same flow: (1) Tables handler `run(raw)` → tables, table_relationships, connection. (2) Dimension handler `run(raw)` → list[Field]. (3) Measure handler `run(raw)` → list[Field]. (4) Calculated-field handler `run(raw)` → list[Field]. (5) Orchestrator **merges** all field lists into one; builds **one** `Datasource` with those tables, relationships, connection, and merged fields; builds **one** `MetadataModel` with `datasources = [that Datasource]`. | Must |

### 3.4 Semantic mapping (model → canonical MetadataModel)

| ID | Requirement | Priority |
|----|-------------|----------|
| S1 | **One datasource** per Power BI model (one .pbix = one semantic model). Datasource id/name from model name or identifier. | Must |
| S2 | **Connection:** Parse all connection-related information from partition source. **Primary goal:** identify **datasource type** (e.g. BigQuery, SQL Server, Snowflake, etc.) from M expression or source type. Store server/database/schema when present. | Must |
| S3 | **Tables:** Map each `model.tables[]` to canonical `Table` (id, name, schema, table_name). Include hidden tables (e.g. date tables); optional `extended_properties` for `isHidden`. | Must |
| S4 | **Fields:** Every field must be classified as **dimension** or **measure**. If a field has a **formula** (DAX expression), it must also be classified as **calculated** (e.g. `field_type` = dimension | measure | calculated_field; `is_calculated` = true when formula present). | Must |
| S5 | **Dimensions:** Columns (including calculated columns) map to canonical Field with `field_type` dimension or calculated_field. Use YAML for data_type (Power BI dataType → canonical data_type) and column type (Data, Calculated, calculatedTableColumn → dimension/calculated_field). | Must |
| S6 | **Measures:** `model.tables[].measures[]` map to canonical Field with `field_type` measure. Aggregation inferred from DAX via YAML (e.g. SUM, AVG, COUNT). When formula present, set `is_calculated` true and store `formula`. | Must |
| S7 | **Relationships:** Map `model.relationships[]` to canonical `TableRelationship` (from_table, to_table, join_type, on_columns). join_type from YAML default (Power BI does not store join type in layout). | Must |
| S8 | **Hierarchy:** Support hierarchy in canonical so Transformer can use it. Add to canonical model whatever is needed to identify hierarchy (e.g. optional `hierarchies` on Table or in `extended_properties`). No expansion in parser—only map as-is. | Must |
| S9 | **Format string / lineage / annotations:** Store in Field or Table `extended_properties` to keep canonical agnostic. | Should |
| S10 | **summarizeBy:** Map Power BI column summarization to canonical aggregation (or null) via YAML. | Must |

### 3.5 Visualization / report mapping (later phase)

| ID | Requirement | Priority |
|----|-------------|----------|
| V1 | Map Report definition to canonical **ReportMetadata** or **DashboardMetadata**. In Power BI, “dashboard” = pinned report (not exportable); **Report = Dashboard** in other BI tools. | Must |
| V2 | Map pages and visuals to canonical Visualization/Chart and report pages/sections. Visual type, position, data mappings (queryState), filters from YAML. | Must |

*(Detailed visualization requirements will be refined after semantic is complete.)*

### 3.6 Configuration (YAML)

| ID | Requirement | Priority |
|----|-------------|----------|
| C1 | **Multiple YAML files** are acceptable (e.g. `semantic_mapping.yaml`, `visualization_mapping.yaml`). Optional index YAML to reference paths. | Must |
| C2 | **Semantic YAML:** data_types, column_types (including calculatedTableColumn), measure_aggregation, summarizeBy, relationship default join_type, defaults. | Must |
| C3 | **Visualization YAML:** visual type mapping, query role mapping (Category, Y, Values, etc. → mapping_role). | Must |
| C4 | **Enums in code:** Validate YAML keys against enums (e.g. FieldType, DataType, Aggregation, MappingRole). Reject or default unknown values per project rules. | Must |

### 3.7 Orchestrator and output

| ID | Requirement | Priority |
|----|-------------|----------|
| O1 | **Loop:** Orchestrator iterates over each **report folder** in `parsed_output`. | Must |
| O2 | For each report folder: load raw → run semantic mapping (and later visualization) → produce canonical bundle. | Must |
| O3 | **Output location:** Write canonical output to **canonical_output**. One subfolder (or one file set) **per report** (e.g. `canonical_output/<report_id>/metadata_model.json` or similar). | Must |
| O4 | **Exception handling:** If processing of one report fails (load or map), record the failure in **canonical_output** so it is visible—e.g. write `canonical_output/<report_id>/_error.json` with `{"success": false, "report_id": "...", "error": "...", "stage": "load"|"semantic"|"visualization"}` or append to a manifest file listing successes and failures. | Must |
| O5 | Do not abort entire batch on single report failure; continue with remaining reports. | Must |

### 3.8 Constraints

| ID | Requirement | Priority |
|----|-------------|----------|
| X1 | **No processing beyond mapping.** No DAX execution, no SQL generation, no new derived columns. | Must |
| X2 | **Canonical models remain BI-source agnostic.** Power BI–specific details go in `extended_properties`. | Must |
| X3 | Follow Cursor architectural rules (parser_normalizer layout, common.yaml_loader, models in `models/`). | Must |

---

## 4. Non-functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| N1 | Parser/normalizer must be deterministic: same input → same canonical output. | Should |
| N2 | Large parsed_output (many reports) should be processable without loading all into memory at once (stream/iterate per report). | Should |
| N3 | Clear error messages and stage (load vs semantic vs viz) when a report fails. | Must |

---

## 5. Execution order (agreed)

1. **Semantic model → canonical mapping** (first).
2. **Visualization/report mapping** (after semantic).

---

## 6. Dependencies

- **Collector** must produce `parsed_output` with `Model/database.json` and `Report/definition/` structure.
- **Canonical models** in `models/canonical.py` and `models/dashboard.py`; may need small additions (e.g. hierarchy in Table extended_properties, `Connection.connection_provider` for datasource type) as documented in **`plan/semantic_model_canonical_mapping.md`**.
- **Config:** YAML files in `config/`; load via `common.yaml_loader`.

---

## 7. Acceptance criteria (semantic phase)

- [ ] Loader reads `parsed_output` path and returns raw `{ "model", "report" }` per report.
- [ ] Semantic orchestrator builds one `MetadataModel` per report from `raw["model"]`.
- [ ] All tables (including hidden) mapped to canonical Table.
- [ ] All columns and measures mapped to canonical Field; every field is dimension or measure; fields with formula have is_calculated true / field_type calculated_field where appropriate.
- [ ] Relationships mapped to TableRelationship; Connection includes datasource type identification.
- [ ] Hierarchy information present in canonical (table or extended_properties).
- [ ] Orchestrator loops report folders and writes canonical_output per report.
- [ ] On failure, canonical_output contains explicit error information for that report.
- [ ] All mapping rules driven by YAML; enums validate config.
- [ ] Semantic handlers implement interface (can_handle, run); each returns own type; orchestrator sends full raw and merges fields into one Datasource.
- [ ] Code flow matches single-datasource structure (tables → tables+relationships+connection; dimension+measure+calc_field → merged fields → one Datasource).

---

## 8. Output JSON contract (final output shapes)

Canonical output files must conform to the following shapes so consumers and tests have a single contract.

### 8.1 Success: `canonical_output/<report_id>/metadata_model.json`

Root object is a **MetadataModel**. Example (minimal):

```json
{
  "metadata_version": "1.0",
  "source_system": "powerbi",
  "extracted_at": "2025-02-17T12:00:00Z",
  "datasources": [
    {
      "id": "report_id_or_model_name",
      "name": "Model display name",
      "source_system": "powerbi",
      "datasource_type": "embedded",
      "connection": {
        "type": "import",
        "server": "",
        "database": "dataset_name",
        "schema": "schema_name",
        "connection_provider": "bigquery"
      },
      "tables": [
        {
          "id": "table_lineage_tag",
          "name": "table_name",
          "schema": "schema_name",
          "table_name": "table_name"
        }
      ],
      "table_relationships": [
        {
          "from_table": "table_a",
          "to_table": "table_b",
          "join_type": "LEFT",
          "on_columns": [{"from": "col_id", "to": "col_id"}]
        }
      ],
      "fields": [
        {
          "id": "field_lineage_tag",
          "name": "field_name",
          "field_type": "dimension",
          "data_type": "string",
          "source_table": "table_name",
          "source_column": "column_name",
          "aggregation": null,
          "formula": null,
          "depends_on": null,
          "is_calculated": false
        },
        {
          "id": "measure_lineage_tag",
          "name": "Total Revenue",
          "field_type": "measure",
          "data_type": "number",
          "source_table": "marketing_campaign_data",
          "source_column": null,
          "aggregation": "SUM",
          "formula": "SUM(marketing_campaign_data[Revenue])",
          "depends_on": null,
          "is_calculated": true
        }
      ],
      "parameters": [],
      "extended_properties": null
    }
  ],
  "cross_datasource_relationships": []
}
```

### 8.2 Failure: `canonical_output/<report_id>/_error.json`

Written when load or semantic (or later visualization) fails for that report. Example:

```json
{
  "success": false,
  "report_id": "<report_folder_name>",
  "error": "Human-readable error message (e.g. KeyError, validation error)",
  "stage": "load"
}
```

Allowed `stage` values: `"load"`, `"semantic"`, `"visualization"`.

### 8.3 Optional: `canonical_output/_manifest.json`

List of all reports processed; success and path or error. Example:

```json
[
  {
    "report_id": "Report_A_abc123",
    "success": true,
    "metadata_model": "Report_A_abc123/metadata_model.json"
  },
  {
    "report_id": "Report_B_def456",
    "success": false,
    "error": "Missing model.tables",
    "stage": "semantic"
  }
]
```

---

## 9. References

- `docs/code_layout.md` — Parser & normalizer folder structure.
- `.cursor/rules/pipeline-and-layout.mdc` — Pipeline and layout.
- `.cursor/rules/yaml-and-config.mdc` — YAML as rule-based config.
- `plan/semantic_model_canonical_mapping.md` — Detailed semantic → canonical mapping (to be created/updated).
- `plan/parser_normalizer_implementation_plan.md` — Implementation plan.
