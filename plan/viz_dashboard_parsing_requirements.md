# Visualization & Dashboard Parsing — Requirements Document

**Version:** 1.0  
**Status:** For approval  
**Input:** Raw report structure from loader (`raw["report"]`, `raw["pages_metadata"]`, `raw["pages"]`)  
**Output:** Canonical `DashboardMetadata` (Dashboard, DashboardPage, DashboardComponent, Visualization, FilterComponent, etc.)  
**Reference:** Same code architecture as semantic layer (parse → map to canonical; config in YAML; handlers + orchestrator).

---

## 1. Objective

Parse and map **report/dashboard and visual metadata** (from loader output) into the **canonical dashboard model** with no transformation logic. This layer only maps raw metadata to canonical structures (Dashboard, DashboardPage, DashboardComponent, Visualization, FilterComponent, DataMapping, Position). All **configurable rules** (e.g. visual types, queryState → mapping_role) live in **YAML**; no hardcoding of visual types or roles in code.

- **Report/pages** → canonical `Dashboard` + `DashboardPage[]`.
- **Visuals** → `DashboardComponent` per visual; data-bound visuals → `Visualization`; slicers → `FilterComponent`.
- **queryState** → `DataMapping[]` (dimension, measure, grouping, tooltip, sort, etc.) using YAML-driven role mapping.

---

## 2. Scope

### 2.1 In scope

- **Input:** Same raw dict as semantic phase: `raw["report"]`, `raw["pages_metadata"]`, `raw["pages"]` (from loader).
- **Output:** Canonical dashboard bundle per report: `DashboardMetadata` (dashboards, visualizations, filter_components, etc.), written to **canonical_output** (e.g. `canonical_output/<report_id>/dashboard_metadata.json`).
- **Configuration:** All mapping rules in YAML (e.g. `visualization_mapping.yaml` or a section in existing `powerbi_canonical_mapping.yaml`): visual types, component type per visual type, queryState key → mapping_role. Enums in code validate against YAML.
- **Architecture:** Handlers (dashboard, pages, visuals) with a common interface; orchestrator runs handlers and assembles `DashboardMetadata`. Same pattern as semantic (tables, dimension, measure).
- **Tests:** Unit tests per handler and per visual type; integration test in `scripts/run_integration.py` once implementation is complete.
- **Exception handling:** On failure, record in canonical_output (e.g. `_error.json` with `stage: "visualization"`); do not abort entire batch.

### 2.2 Out of scope

- No transformation beyond mapping (no layout computation, no DAX, no SQL).
- No changes to loader or semantic orchestrator logic (only reuse loader output).
- Interactions/drill-through mapping may be a later phase; document as optional if not in v1.

---

## 3. Code Architecture (aligned with semantic layer)

### 3.1 Pipeline

1. **Load** (existing): `load(path)` → raw `{"model", "report", "pages_metadata", "pages"}`.
2. **Parse → Map (viz/dashboard):** Viz orchestrator takes `raw` (or `raw["report"]`, `raw["pages_metadata"]`, `raw["pages"]`) and runs handlers to build canonical dashboard model.
3. **Output:** One `DashboardMetadata` per report (dashboards, visualizations, filter_components, text_components, etc.).

### 3.2 Handler interface (protocol)

Same pattern as semantic: **handlers implement a common protocol**; orchestrator sends **full raw** (or report slice) to each handler.

| Concept | Semantic (existing) | Viz/Dashboard (this doc) |
|--------|----------------------|---------------------------|
| Protocol | `can_handle(raw) -> bool`, `run(raw) -> T` | Same: `can_handle(raw) -> bool`, `run(raw) -> T` |
| Handlers | tables, dimension, measure | dashboard (or report), pages, visuals (or one “report” handler that builds Dashboard + pages + components) |
| Return types | TablesResult, list[Field] | DashboardResult (or inline): Dashboard, list[DashboardPage], list[Visualization], list[FilterComponent], etc. |
| Config | powerbi_canonical_mapping.yaml | visualization_mapping.yaml (or viz section in same YAML): visual_types, component_type_mapping, query_state_role_mapping |

### 3.3 Recommended module layout

- **Config:** `config/visualization_mapping.yaml` (or extend `config/powerbi_canonical_mapping.yaml` with a `visualization:` top-level key). No hardcoded visual type strings or queryState keys in Python.
- **Handlers:** Under `parser_normalizer/dashboard/` (or `parser_normalizer/viz/`):
  - `protocol.py` — Protocol and result types (e.g. `DashboardBundle` or `DashboardMetadata`).
  - `dashboard.py` — Builds Dashboard (id, name, source_system, report_id, is_multi_page, pages).
  - `pages.py` — Builds list of DashboardPage from raw pages + pages_metadata.
  - `visuals.py` — Builds DashboardComponent per visual; delegates to visual-type logic (chart → Visualization, slicer → FilterComponent, button → Visualization with empty data_mappings).
  - `query_state.py` — Maps queryState + sortDefinition to list of DataMapping (uses YAML for role mapping).
- **Orchestrator:** `parser_normalizer/dashboard/orchestrator.py` (or `viz/orchestrator.py`) — Runs handlers in order, merges results into `DashboardMetadata`.
- **Enums:** Validate YAML keys (e.g. component_type, mapping_role, visual_type) in code; no default for missing keys—reject or skip and record.

### 3.4 Single entry point

- `run_viz(raw: dict) -> DashboardMetadata` (or `run_dashboard(raw: dict) -> DashboardMetadata`) in the viz/dashboard orchestrator, called after semantic (or in parallel from same raw) in the top-level run/integration script.

---

## 4. Configuration (YAML) — no hardcoding

All of the following must be configurable via YAML. **No hardcoded** visual type strings (e.g. `"slicer"`, `"clusteredColumnChart"`) or queryState keys (e.g. `"Category"`, `"Y"`) in application code; read from config and validate with enums.

### 4.1 Visual type → component type

| YAML key | Purpose | Example |
|----------|---------|---------|
| `visual_types.component_type` | Map Power BI visualType to canonical DashboardComponent.type | `slicer` → `filter`; `clusteredColumnChart` → `visualization`; `actionButton` → `visualization` or `button` |
| `visual_types.creates_filter_component` | Which visual types create a FilterComponent (slicer) | `[slicer]` |
| `visual_types.creates_visualization` | Which visual types create a Visualization (charts, cards, tableEx, KPI, actionButton) | `[clusteredColumnChart, barChart, slicer, card, cardVisual, tableEx, ...]` |
| `visual_types.empty_data_mappings` | Which visual types have empty data_mappings | `[actionButton]` |

(Exact key names can be chosen to minimize duplication; e.g. one list per component kind.)

### 4.2 mapping_role from projection (no YAML fallback)

**mapping_role is derived only from the raw projection.** No fallback from YAML for dimension vs measure.

| Rule | Source | Canonical mapping_role |
|------|--------|------------------------|
| Projection has **Measure** | `field.Measure` in raw | **measure** (always). |
| Projection has **Column** (or equivalent) | `field.Column` in raw | **dimension**, **grouping**, **tooltip**, **detail**, or **label** — see below. |

For **Column** projections, the specific role (dimension vs grouping vs tooltip vs detail vs label) is determined by the **queryState key** (e.g. Category, Legend, Tooltip) using YAML **query_state_roles** only for that purpose. YAML **must not** assign **measure** to any key; measure comes solely from the projection. (Y can hold a dimension; Axis can hold a measure — so slot names in YAML do not imply dimension/measure.)

**query_state_roles (YAML):** Optional **allow-list** of queryState keys to process. For each key listed, Column projections get the role from this map (dimension | grouping | tooltip | detail | label). Keys not in the map are not processed (no default). The map is **not** used to assign **measure**; measure is only from projection.

**Looker impact:** Correct dimension vs measure in canonical ensures the transform layer maps fields to the right Looker type (dimension vs measure), so charts and explores are generated correctly. No fallback keeps the canonical output deterministic and safe for Looker translation.

### 4.3 No default when missing in YAML

- **If a visual type is not present in YAML:** the implementation must **not** substitute any default (e.g. must not assume `component_type: "visualization"` or `visualization_type: "unknown"`). It must **fail** with a clear error that the visual type is not configured, or skip that visual and record the skip in a deterministic way. No silent fallback.
- **If a queryState key is not present in YAML** (`query_state_roles`): the implementation must **not** assume a mapping_role. Either **omit** that key’s projections from data_mappings (and optionally record the unmapped key) or **fail** with a clear error. No default mapping_role. **mapping_role for measure is never taken from YAML** — only from projection (Measure → measure).
- **Summary:** Visual types and which queryState keys are processed are driven only by what is in YAML. mapping_role (dimension vs measure) is driven only by the projection; no fallback.

### 4.4 Complete contents of visualization YAML

Everything that belongs in the viz config must be listed below. The file (e.g. `config/visualization_mapping.yaml`) must contain **only** these keys (or a single top-level key such as `visualization:` that nests them). Nothing is implied by code.

| Section / Key | Type | Required | Description |
|---------------|------|----------|-------------|
| **visual_types** | mapping (see below) | Yes | Defines how each Power BI `visualType` is handled. |
| **visual_types.component_type** | map: string → string | Yes | One entry per supported visualType. Key = Power BI visualType (e.g. `clusteredColumnChart`, `slicer`, `actionButton`). Value = canonical `DashboardComponent.type` (`visualization`, `filter`, `button`, `text`, `image`, etc.). Every visualType that the parser will see must have an entry; no default. |
| **visual_types.creates_filter_component** | list of string | Yes | List of visualType values that create a FilterComponent (e.g. `[slicer]`). Visual types not in this list do not create a FilterComponent. |
| **visual_types.creates_visualization** | list of string | Yes | List of visualType values that create a Visualization (e.g. `clusteredColumnChart`, `barChart`, `card`, `cardVisual`, `tableEx`, `lineChart`, `donutChart`, `actionButton`, …). Visual types not in this list do not create a Visualization. |
| **visual_types.empty_data_mappings** | list of string | Yes | List of visualType values for which Visualization has `data_mappings: []` (e.g. `[actionButton]`). All other visuals that create a Visualization get data_mappings from queryState. |
| **query_state_roles** | map: string → string | Yes | Allow-list: keys = queryState keys to process (e.g. `Category`, `Y`, `Values`, `Legend`, `Tooltip`). Value = role for **Column** projections only: `dimension`, `grouping`, `tooltip`, `detail`, or `label`. **Measure** projections always get `mapping_role: measure` from the projection; this map is not used for measure. Keys not in this map are not processed (no default). |

**Example minimal YAML structure (all keys that must exist):**

```yaml
visual_types:
  component_type:
    clusteredColumnChart: visualization
    barChart: visualization
    slicer: filter
    actionButton: visualization
    card: visualization
    cardVisual: visualization
    tableEx: visualization
    lineChart: visualization
    donutChart: visualization
    lineStackedColumnComboChart: visualization
    # ... every visualType that can appear in parsed reports
  creates_filter_component:
    - slicer
  creates_visualization:
    - clusteredColumnChart
    - barChart
    - card
    - cardVisual
    - tableEx
    - lineChart
    - donutChart
    - lineStackedColumnComboChart
    - actionButton
    # ... same set as needed
  empty_data_mappings:
    - actionButton

query_state_roles:
  # Role for Column projections only; Measure → measure always from projection (no YAML).
  Category: dimension
  Y: dimension
  Values: dimension
  Legend: grouping
  Tooltip: tooltip
  Axis: dimension
  Rows: dimension
  Columns: grouping
  Detail: detail
  Label: label
  # Keys not listed are not processed (no default).
```

### 4.5 Query state capture — how we capture it and sample canonical output

**Source in raw:** For each visual, query state lives under:

- `visual["query"]["queryState"]` — object whose **keys** are Power BI role names (e.g. `Category`, `Y`, `Values`, `Legend`, `Tooltip`). Each key’s value has a **projections** array; each projection has **field** (Measure or Column with Expression.SourceRef.Entity and Property/Column) and often **queryRef** / **nativeQueryRef**.
- `visual["query"]["sortDefinition"]` — optional; has **sort** array with **field** (same structure as above) and **direction** (`Ascending` / `Descending`).

**Capture rules:**

1. Iterate over each key in `queryState`. If the key is **not** in YAML **query_state_roles**, do not add any DataMapping for it (no default).
2. For each **projection** under that key: resolve **Entity** → `datasource_id`, **Property** or **Column** → `field_id`. **mapping_role:** if the projection has **Measure** → `measure` (always, from projection). If the projection has **Column** (or equivalent) → use **query_state_roles[key]** for that key (dimension | grouping | tooltip | detail | label). Append one **DataMapping** (field_id, datasource_id, mapping_role; optional aggregation, sort_order).
3. If **sortDefinition** exists, for each sort entry resolve the field and set **sort_order** (`asc` / `desc`) on the **matching** DataMapping (same field_id/datasource_id) if that mapping was created from queryState.

**Sample raw queryState (Power BI visual.json):**

```json
{
  "visual": {
    "visualType": "clusteredColumnChart",
    "query": {
      "queryState": {
        "Category": {
          "projections": [
            {
              "field": {
                "Column": {
                  "Expression": {
                    "SourceRef": { "Entity": "marketing_campaign_data" }
                  },
                  "Property": "Campaigns Exposed1"
                }
              },
              "queryRef": "marketing_campaign_data.Campaigns Exposed1"
            }
          ]
        },
        "Y": {
          "projections": [
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": { "Entity": "campaign_products" }
                  },
                  "Property": "Conversion Rate by Exposure"
                }
              },
              "queryRef": "campaign_products.Conversion Rate by Exposure"
            },
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": { "Entity": "marketing_campaign_data" }
                  },
                  "Property": "Avg Revenue per Customer"
                }
              }
            }
          ]
        }
      },
      "sortDefinition": {
        "sort": [
          {
            "field": {
              "Measure": {
                "Expression": {
                  "SourceRef": { "Entity": "campaign_products" }
                },
                "Property": "Conversion Rate by Exposure"
              }
            },
            "direction": "Descending"
          }
        ]
      }
    }
  }
}
```

**Sample canonical Visualization (result of capturing the above):**

```json
{
  "id": "5beaf60287a0cbc6c703",
  "name": "clusteredColumnChart",
  "visualization_type": "clusteredColumnChart",
  "source_system": "powerbi",
  "viz_calculated_fields": [],
  "data_mappings": [
    {
      "field_id": "Campaigns Exposed1",
      "datasource_id": "marketing_campaign_data",
      "mapping_role": "dimension"
    },
    {
      "field_id": "Conversion Rate by Exposure",
      "datasource_id": "campaign_products",
      "mapping_role": "measure",
      "sort_order": "desc"
    },
    {
      "field_id": "Avg Revenue per Customer",
      "datasource_id": "marketing_campaign_data",
      "mapping_role": "measure"
    }
  ],
  "filters": [],
  "parameters": [],
  "conditional_formatting": null,
  "extended_properties": null
}
```

**Slicer example (raw queryState → FilterComponent):** Raw has `queryState.Values.projections[0].field.Column.Expression.SourceRef.Entity` = `"customers"`, `Property` = `"Country"`. Canonical FilterComponent: `{"id": "filter_0305869d2bda1083210a", "field_id": "Country", "datasource_id": "customers", "extended_properties": null}`.

---

## 5. Functional Requirements

### 5.1 Loader (reuse)

| ID | Requirement | Priority |
|----|-------------|----------|
| L1 | Reuse existing loader. Viz pipeline consumes `raw["report"]`, `raw["pages_metadata"]`, `raw["pages"]`. | Must |

### 5.2 Dashboard-level mapping

| ID | Requirement | Priority |
|----|-------------|----------|
| D1 | One **Dashboard** per report: id (e.g. report folder name), name (from report or first page), source_system = "powerbi", report_id optional, is_multi_page from len(pages_metadata.pageOrder) > 1. | Must |
| D2 | **DashboardPage** per page: page_id, page_name (displayName), page_order (index in pageOrder), layout (dict), components (list of DashboardComponent). | Must |
| D3 | Page order must follow `pages_metadata.pageOrder`. | Must |

### 5.3 Visual → DashboardComponent

| ID | Requirement | Priority |
|----|-------------|----------|
| V1 | One **DashboardComponent** per visual.json: id (visual container id), type (from YAML by visualType), position (Position: x, y, width, height; optional z, tab_order). | Must |
| V2 | Component type (visualization | filter | text | image | button | …) from **YAML** by visualType; no hardcoded visual type strings. | Must |
| V3 | When type is visualization: set visualization_id. When type is filter: set filter_id. When type is button/visualization for actionButton: set visualization_id to the optional Visualization id. | Must |

### 5.4 Slicer → FilterComponent

| ID | Requirement | Priority |
|----|-------------|----------|
| F1 | Slicer visuals (visualType from YAML) produce **FilterComponent**: id, field_id, datasource_id from queryState Values (Entity + Property/Column). | Must |
| F2 | DashboardComponent for slicer has type = "filter" and filter_id referencing the FilterComponent. | Must |

### 5.5 Data-bound visual → Visualization

| ID | Requirement | Priority |
|----|-------------|----------|
| X1 | Charts, cards, tableEx, KPI, actionButton (from YAML) produce **Visualization**: id, name, visualization_type, source_system, data_mappings, filters, etc. | Must |
| X2 | **data_mappings** built from queryState. **mapping_role** from projection only: Measure → measure; Column → role from YAML query_state_roles for that key (dimension | grouping | tooltip | detail | label). No YAML fallback for measure. Field resolution: Entity → datasource_id, Property/Column → field_id. | Must |
| X3 | sortDefinition mapped to DataMapping.sort_order (asc/desc). | Must |
| X4 | actionButton (and similar) have data_mappings = [] (no queryState). | Must |

### 5.6 Configuration and validation

| ID | Requirement | Priority |
|----|-------------|----------|
| C1 | Visual types from YAML. queryState keys to process from YAML (query_state_roles); mapping_role for **measure** from projection only (no YAML). For Column projections, role (dimension | grouping | tooltip | detail | label) from query_state_roles. If a visualType or queryState key is not in YAML, no default: fail or skip and record. | Must |
| C2 | Single YAML file or section (e.g. `visualization_mapping.yaml` or `powerbi_canonical_mapping.yaml` visualization section). Load via existing common YAML loader. | Must |

### 5.7 Orchestrator and output

| ID | Requirement | Priority |
|----|-------------|----------|
| O1 | Viz orchestrator runs after (or in parallel with) semantic on same raw. Produces **DashboardMetadata** (dashboards, visualizations, filter_components, …). | Must |
| O2 | Write **dashboard_metadata.json** per report under canonical_output/<report_id>/. On failure, write _error.json with stage "visualization". | Must |
| O3 | Do not abort batch on single report failure; continue and record failure in manifest. | Must |

### 5.8 Constraints

| ID | Requirement | Priority |
|----|-------------|----------|
| X1 | No processing beyond mapping (no layout engine, no DAX, no SQL). | Must |
| X2 | Canonical models remain BI-agnostic; PBI-specific details in extended_properties. | Must |
| X3 | Follow existing parser_normalizer layout and Cursor rules; config in config/; models in models/dashboard.py. | Must |

---

## 6. Test Cases

### 6.1 Unit tests (per handler / per concept)

| ID | Test scope | Description |
|----|------------|-------------|
| T1 | Loader (existing) | Report/pages/visuals present in raw (already covered by test_loader if applicable). |
| T2 | Dashboard handler | Given minimal raw with pages_metadata and one page, run dashboard handler → one Dashboard, is_multi_page correct. |
| T3 | Pages handler | Given raw with 2 pages, run pages handler → 2 DashboardPage, correct page_id, page_name, page_order. |
| T4 | Visual → DashboardComponent | Given one visual.json (e.g. clusteredColumnChart), component has id, type=visualization, position, visualization_id. |
| T5 | Slicer → FilterComponent | Given one visual.json (slicer) with Values = Entity + Property, output FilterComponent with field_id, datasource_id; DashboardComponent type=filter, filter_id set. |
| T6 | queryState → DataMapping | Given queryState with Category and Y, output 1 dimension + N measure DataMappings; mapping_role from YAML. |
| T7 | actionButton | Given visual.json actionButton (no query), output Visualization with data_mappings=[], visualization_type from config. |
| T8 | Config loading | Load visualization_mapping.yaml; verify structure (visual_types, query_state_roles). Unknown visual type or queryState key must not be defaulted; test must assert fail or explicit skip (no default). |

### 6.2 Integration test

| ID | Test scope | Description |
|----|------------|-------------|
| I1 | **run_integration.py** | After implementation: extend **Step 3 (Canonical)** to run **viz/dashboard** mapping in addition to semantic. For each report: load → semantic → **viz/dashboard** → write metadata_model.json **and** dashboard_metadata.json. Manifest entries include success/failure and paths to both files (or _error.json with stage load | semantic | visualization). |
| I2 | End-to-end one report | Run integration script on one report (e.g. Global Marketing & Customer Insights); assert canonical_output/<report_id>/dashboard_metadata.json exists, contains one Dashboard, N pages, M components, and correct counts of visualizations and filter_components. |

---

## 7. Integration with scripts/run_integration.py

- **Current step 3:** load → semantic → write metadata_model.json (or _error.json).
- **Required change:** In the same per-report loop, after semantic succeeds (or in parallel on same raw):
  - Run **viz/dashboard** orchestrator: `run_viz(raw)` → `DashboardMetadata`.
  - Write **dashboard_metadata.json** under the same report output folder (canonical_output/<report_id>/).
- **Manifest:** Each entry may include `"dashboard_metadata": "<report_id>/dashboard_metadata.json"` when success; on viz failure, stage = `"visualization"` and no dashboard_metadata path.
- **Error contract:** _error.json stage may be `"load"` | `"semantic"` | `"visualization"` so failures are visible.

---

## 8. Output JSON Contract

### 8.1 Success: canonical_output/<report_id>/dashboard_metadata.json

Root object is **DashboardMetadata** (see models/dashboard.py). Example minimal shape:

```json
{
  "metadata_version": "1.0",
  "source_system": "powerbi",
  "extracted_at": "2025-02-17T12:00:00Z",
  "dashboards": [
    {
      "id": "Report_id",
      "name": "Report Name",
      "source_system": "powerbi",
      "report_id": "Report_id",
      "is_multi_page": true,
      "pages": [
        {
          "page_id": "page_id_1",
          "page_name": "Page 1",
          "page_order": 0,
          "layout": {},
          "components": [
            {
              "id": "visual_id_1",
              "type": "visualization",
              "position": {"x": 0, "y": 0, "width": 100, "height": 100},
              "visualization_id": "visual_id_1"
            }
          ]
        }
      ],
      "interactions": []
    }
  ],
  "visualizations": [],
  "filter_components": [],
  "text_components": [],
  "image_components": [],
  "container_components": [],
  "parameter_components": [],
  "web_content_components": []
}
```

(Full content per plan/visual_dashboard_canonical_mapping.md and dashboard.py.)

### 8.2 Failure: canonical_output/<report_id>/_error.json

Already defined; stage may be `"visualization"` when viz/dashboard mapping fails.

### 8.3 Manifest: canonical_output/_manifest.json

Each entry may include:

- `"metadata_model": "<report_id>/metadata_model.json"`
- `"dashboard_metadata": "<report_id>/dashboard_metadata.json"` (when viz step succeeds)

---

## 9. YAML data from parsed_output

A full **visualization_mapping.yaml** has been generated from all visuals found under **parsed_output** (Report/definition/pages and Report/sections where applicable). File location: **`src/powerbi_to_looker/config/visualization_mapping.yaml`**.

**Visual types included (all that appear in parsed_output):**

| Category | visualType values |
|----------|-------------------|
| Charts | clusteredColumnChart, clusteredBarChart, barChart, columnChart, lineChart, areaChart, pieChart, donutChart, scatterChart, lineStackedColumnComboChart, lineClusteredColumnComboChart, hundredPercentStackedColumnChart, hundredPercentStackedBarChart, waterfallChart, ribbonChart, treemap |
| Tables | tableEx, pivotTable |
| Cards | card, cardVisual |
| Slicers | slicer, listSlicer, advancedSlicerVisual |
| Buttons / nav | actionButton, pageNavigator |
| Decorative | textbox (text), image, shape (image) |
| Custom | Gantt1448688115699, Sunburst1445472000808, sdmPbiTable78C63D3ED55C41ECB9F4B21D24D6AB3F |

**query_state_roles** in that file: Category, Y, Values, Legend, Tooltip, Axis, Rows, Columns, Detail, Label. Any queryState key not in the YAML is not mapped (no default). New visual types or query roles must be added to the YAML before they are supported.

---

## 10. Looker translatability (transform layer)

**Is the canonical output easy enough to translate to Looker in the transform layer?**

**Yes, with some caveats.** The canonical model is designed to be BI-agnostic and maps cleanly to concepts a Looker transform can use:

| Canonical concept | Looker translation |
|-------------------|---------------------|
| **Dashboard** | Looker Dashboard (one dashboard per report; pages → dashboard layout or multiple dashboards). |
| **DashboardPage** | Dashboard layout (tiles/sections) or separate Looker dashboard; page_order can drive tab or page order. |
| **DashboardComponent** + **Position** | Dashboard tile position (x, y, width, height map to grid/placement). |
| **Visualization** + **visualization_type** | Looker explore/viz type: bar → Looker bar chart, lineChart → line, tableEx/pivotTable → table, card/cardVisual → single value, etc. |
| **DataMapping** (field_id, datasource_id, mapping_role) | Direct: dimension → dimension in explore; measure → measure; grouping → dimension for series/legend. field_id/datasource_id align with semantic model (MetadataModel) so the transform can resolve to Looker model/field. |
| **FilterComponent** (slicer) | Looker dashboard filter; field_id/datasource_id → filter field. |
| **sort_order** on DataMapping | Looker sort on that field. |

**What makes it straightforward:**

- **Single semantic model** (from parser): MetadataModel gives tables/fields; dashboard_metadata gives which fields are used where. Transform joins on datasource_id + field_id to emit Looker model/field references.
- **Explicit roles:** dimension / measure / grouping / tooltip map to Looker “dimensions” and “measures” and to which slot (axis, legend, tooltip) they go.
- **No PBI-specific logic in canonical:** Transform only needs to map visualization_type → Looker chart type and layout; no Power BI APIs.

**Caveats:**

- **Layout:** Looker dashboards use a grid; Position (x, y, width, height) may need scaling or snapping to grid. z-order/tab_order can inform tile order.
- **Visual types:** Some PBI visuals (e.g. waterfallChart, ribbonChart, Gantt) may not have a 1:1 Looker chart; transform may map to “closest” (e.g. bar) or mark as unsupported.
- **Interactions:** Canonical interactions (filter, cross-filter) are optional; if present, transform can map to Looker filter actions / cross-filters.
- **Conditional formatting / extended_properties:** Can be passed through or used for Looker conditional formatting if the transform supports it.

**Conclusion:** The canonical dashboard output is **well-suited for a transform layer** that produces Looker dashboards and explores: stable field references, clear roles, and BI-agnostic structure. The main work in transform is chart-type mapping and layout adaptation, not parsing PBI-specific structures.

---

## 11. Report structure loader: support definition and sections layouts

**Context:** Some reports (e.g. Education_24b04535) are extracted with **Report/sections/** (section.json, visualContainers with config.json, query.json, visualContainer.json) instead of **Report/definition/** (pages.json, page.json, visuals/*/visual.json). The current loader only reads definition; sections reports get empty `raw["pages"]` and thus empty dashboard_metadata.

**Requirement:** Support both layouts so that the same canonical pipeline (viz/dashboard mapping) receives a single, consistent raw shape regardless of layout. **No change** to canonical mapping (viz orchestrator, query_state, visuals, YAML); **only** the loader / report-structure parsing layer changes.

### 11.1 Contract (unchanged)

The loader must produce (for report structure):

- `raw["report"]`, `raw["pages_metadata"]` (e.g. `pageOrder`: list of page/section ids in order), `raw["pages"]`.
- `raw["pages"][page_id]["page"]`: at least displayName, name (or equivalent).
- `raw["pages"][page_id]["visuals"][visual_id]`: one object per visual with **name**, **position** (x, y, width, height; optional z, tabOrder), **visual** with **visualType** and **query** (queryState, sortDefinition).

Viz/dashboard code already consumes this; both layouts must emit it.

### 11.2 Design: Factory pattern

- **ReportStructureParser (protocol):** `load(folder: Path) -> dict` returning `{"report": ..., "pages_metadata": ..., "pages": ...}`. Optionally `can_handle(folder: Path) -> bool`.
- **DefinitionReportParser:** Implements the protocol; reads `Report/definition/` (current loader logic). `can_handle` = `(folder / "Report" / "definition").exists()`.
- **SectionsReportParser:** Implements the protocol; reads `Report/sections/`. For each section dir: section.json → page; for each visualContainers subdir: merge visualContainer.json + config.json + query.json into one “visual” object (position, visualType, query). Build pageOrder from section dir order. `can_handle` = `(folder / "Report" / "sections").exists()`.
- **ReportParserFactory:** `get_parser(folder: Path) -> ReportStructureParser | None`. Encapsulates layout detection: if definition exists return DefinitionReportParser(); elif sections exists return SectionsReportParser(); else return None. No if/else in the loader; the factory is the only place that chooses layout.
- **Loader:** After loading model, call `parser = factory.get_parser(folder)`; if parser, `raw.update(parser.load(folder))` (or set raw["report"], raw["pages_metadata"], raw["pages"] from parser.load); else set those keys to empty dicts.

### 11.3 Sections layout details

- **Page order:** List `Report/sections/` directories (e.g. `001_Academic Performance Overview`, `002_...`); order by name or by explicit index if present → `pages_metadata["pageOrder"]`.
- **Page id:** Section folder name (or stable id from section.json if present).
- **Page object:** From section.json (displayName, name, etc.); layout can be `{}` initially.
- **Visual id:** visualContainers subdir name (e.g. `00000_Assessment Composition Overview`) or a sanitized id.
- **Visual object:** Merge: position from visualContainer.json; visualType from config.json; query (queryState, sortDefinition) from query.json. If sections schema uses different key names, map them to the same names the viz pipeline expects.

### 11.4 Scope of code changes

| Component | Change |
|-----------|--------|
| **Loader** | Use factory to get parser; call parser.load(); no layout if/else in loader. |
| **New** | ReportParserFactory, ReportStructureParser protocol, DefinitionReportParser (extract current logic), SectionsReportParser. |
| **Canonical mapping (viz/dashboard)** | **No change.** Same raw shape from either parser. |
| **Semantic parser** | No change (uses raw["model"] only). |

### 11.5 Tests

- Unit test: SectionsReportParser can_handle(folder with sections) True, can_handle(folder with only definition) False.
- Unit test: DefinitionReportParser can_handle(folder with definition) True.
- Unit test: Factory returns DefinitionReportParser when definition exists; returns SectionsReportParser when only sections exists; returns None when neither.
- Integration: Load Education_24b04535 (sections); assert raw["pages_metadata"]["pageOrder"] length 3; raw["pages"] has 3 entries; at least one page has visuals; run_viz(raw) produces non-empty dashboard_metadata (pages and visualizations).

---

## 12. References

- `plan/visual_dashboard_canonical_mapping.md` — Mapping tables, validation example, model changes.
- `plan/parser_normalizer_requirements.md` — Overall parser/normalizer requirements (semantic + viz).
- `src/powerbi_to_looker/models/dashboard.py` — Canonical dashboard models.
- `src/powerbi_to_looker/parser_normalizer/loader.py` — Loader (raw structure).
- `src/powerbi_to_looker/parser_normalizer/semantic/` — Handler/orchestrator pattern to mirror.
- `scripts/run_integration.py` — Integration script to extend with viz/dashboard step.

---

## 13. Approval

This document defines the requirements for **visualization and dashboard canonical parsing and mapping** and for **report structure loader (both layouts)**:

- **Viz/dashboard:** Architecture (handlers + orchestrator); config in YAML; mapping_role from projection only; no YAML fallback for measure; unit and integration tests; Looker translatability.
- **Report structure loader (§11):** Support both **Report/definition** and **Report/sections** layouts via **Factory pattern** (ReportParserFactory, ReportStructureParser protocol, DefinitionReportParser, SectionsReportParser). Same raw contract so canonical mapping and viz pipeline require **no change**. Tests for factory, parsers, and Education (sections) end-to-end.

**Please review and approve to proceed with implementation of §11 (report structure loader).** Once approved, implementation will add the factory and sections parser and wire the loader to use them; viz/dashboard and canonical mapping remain unchanged.
