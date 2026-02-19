# Visual & Dashboard → Canonical Mapping

**Version:** 1.0  
**Status:** For verification  
**Purpose:** Define how Power BI report/dashboard and visual metadata map to the canonical Dashboard, DashboardPage, DashboardComponent, and Visualization models. Use this to verify mappings in Power BI Desktop and to identify any canonical model changes.

---

## 1. Requirement

All dashboard-level and visual components from the parsed report must be translated into the canonical model:

- **Dashboard** (one per report; id, name, source_system, is_multi_page, pages)
- **DashboardPage** (one per page; page_id, page_name, page_order, layout, components)
- **DashboardComponent** (one per visual/container on a page; id, type, position, visualization_id, etc.)
- **Visualization** (one per data-bound visual; id, name, visualization_type, data_mappings, filters, etc.)
- **DataMapping** (from visual queryState → field_id, datasource_id, mapping_role)
- **Filter** (from visual filters / slicer state where applicable)

---

## 2. Source: Power BI report structure (loader output)

Raw metadata shape after `loader.load(...)`:

| Key | Source file / structure | Description |
|-----|-------------------------|-------------|
| `report` | `Report/definition/report.json` | Report-level config (theme, objects, etc.) |
| `pages_metadata` | `Report/definition/pages/pages.json` | `pageOrder[]`, `activePageName` |
| `pages` | `Report/definition/pages/<pageId>/` | One entry per page |
| `pages[pageId].page` | `page.json` | Page display name, layout hints |
| `pages[pageId].visuals` | `visuals/<visualId>/visual.json` | One visual container per visual |

Each **visual.json** contains:

- `name` — visual container id (often same as folder name)
- `position` — `{ x, y, z, width, height }`
- `visual` — `visualType`, `query` (queryState, sortDefinition, filters), config, etc.

---

## 3. Report / pages → Dashboard, DashboardPage

| Raw path | Canonical target | Notes |
|----------|------------------|-------|
| Report identity (folder name or report config) | `Dashboard.id` | Stable id for the report |
| Report display name (from report or first page) | `Dashboard.name` | |
| `"powerbi"` | `Dashboard.source_system` | |
| `pages_metadata.pageOrder` length > 1 | `Dashboard.is_multi_page` | True if multiple pages |
| — | `Dashboard.pages` | List of DashboardPage (see below) |
| `pages_metadata.pageOrder` | Order of `Dashboard.pages` | Preserve page order |
| `pages[pageId].page` | One `DashboardPage` per page | |
| `pageId` | `DashboardPage.page_id` | |
| `page.displayName` or page config | `DashboardPage.page_name` | |
| Index in `pageOrder` | `DashboardPage.page_order` | 0-based or 1-based (decide and document) |
| Page layout (from page config if any) | `DashboardPage.layout` | Dict for extensibility |
| All visuals on page | `DashboardPage.components` | List of DashboardComponent |

---

## 4. Visual container → DashboardComponent + Visualization

For each **visual.json** in `pages[pageId].visuals`:

| Raw path | Canonical target | Notes |
|----------|------------------|-------|
| Visual container id (e.g. folder name) | `DashboardComponent.id` | Unique on the page (or globally if desired) |
| Chart/data visual | `DashboardComponent.type` = `"visualization"` | |
| Slicer, actionButton, card, etc. | See §6 | type and optional visualization_id |
| `position` (x, y, width, height) | `DashboardComponent.position` | Position model has x, y, width, height only |
| — | `DashboardComponent.visualization_id` | Set to Visualization.id when type=visualization |

**Visualization** (one per data-bound visual; slicers can map to Visualization or FilterComponent per design):

| Raw path | Canonical target | Notes |
|----------|------------------|-------|
| Same as component id or derived | `Visualization.id` | Unique in report |
| `visual.config` or fallback to visualType | `Visualization.name` | Display name if available |
| `visual.visualType` (e.g. clusteredColumnChart) | `Visualization.visualization_type` | Normalize to canonical chart type if needed |
| `"powerbi"` | `Visualization.source_system` | |
| From queryState → DataMapping | `Visualization.data_mappings` | See §5 |
| From query filters / filter pane | `Visualization.filters` | List of Filter |
| Conditional formatting from config | `Visualization.conditional_formatting` | |
| Rest of config / unsupported props | `Visualization.extended_properties` | |

**Position:** Raw `position` has `x`, `y`, `z`, `width`, `height`. Canonical **Position** today has only `x`, `y`, `width`, `height`. `z` and any tabOrder are not in the canonical model (see Model changes §8).

---

## 5. queryState → DataMapping

Map visual `query.queryState` and related nodes to **DataMapping** (`field_id`, `datasource_id`, `mapping_role`, optional `aggregation`, `sort_order`).

**Mapping roles:**

| queryState key / usage | mapping_role | Notes |
|------------------------|--------------|-------|
| Category / Axis (X) | `dimension` | Single or multiple projections → one DataMapping per field |
| Y (values) | `measure` | Include aggregation from measure or default |
| Legend / Series | `grouping` | |
| Small multiples / similar | `grouping` | |
| Tooltip | `tooltip` | |
| Filter pane / visual filter | `filter` | Or separate Filter model |
| Sort | `sort` | Use sort_order (asc/desc) from sortDefinition |
| Detail / “detail” role | `detail` | |
| Label | `label` | |

**Field resolution:**  
Each projection has `field` (Measure, Column, etc.) with Expression.SourceRef.Entity and Property (or Column). Resolve to:

- **datasource_id** — from Entity (table) or model table id.
- **field_id** — from Property/Column name or measure name; prefer lineageTag when available for stability.

**aggregation:** From measure definition or summarization (e.g. Sum, Avg); leave None for dimension.

**sort_order:** From `query.sortDefinition` for the same field.

---

## 6. Non-chart visuals

| Raw visualType / kind | DashboardComponent | Visualization / other |
|------------------------|--------------------|------------------------|
| Slicer | type = `"filter"` or `"visualization"` | If visualization: data_mappings for slicer field; or FilterComponent with field_id/datasource_id |
| actionButton | type = `"visualization"` or new type | Optional Visualization with empty data_mappings or a “button” visualization_type (see Model changes) |
| card / cardVisual | type = `"visualization"` | Visualization with measure (and optional category) in data_mappings |
| tableEx (table/matrix) | type = `"visualization"` | Visualization; rows/columns/values → data_mappings (dimension/measure/grouping) |
| KPI | type = `"visualization"` | Visualization with value/target/trend mappings |
| Text box / image | type = `"text"` / `"image"` | Use text_id / image_id; no Visualization required |

---

## 7. Verification checklist (Power BI Desktop)

Use one report, one page, one chart to confirm the mapping:

1. **Report → Dashboard**  
   - [ ] Open the report; note report name and page count.  
   - [ ] Compare with canonical Dashboard (id, name, is_multi_page, pages length and order).

2. **Page → DashboardPage**  
   - [ ] Select one page; note page name and order.  
   - [ ] Compare with one DashboardPage (page_id, page_name, page_order, layout).

3. **One chart → DashboardComponent + Visualization**  
   - [ ] Pick one chart; note its position (x, y, width, height) and visualType.  
   - [ ] Compare raw visual.json position with DashboardComponent.position (z not in model).  
   - [ ] Compare visualType with Visualization.visualization_type.  
   - [ ] For each queryState role (Category, Y, Legend, etc.), confirm one DataMapping with correct mapping_role and field_id/datasource_id.  
   - [ ] Compare sortDefinition with DataMapping.sort_order where applicable.

4. **Filters**  
   - [ ] Add a visual-level or page filter in PBI; re-export or re-parse.  
   - [ ] Confirm corresponding Filter or data_mappings with role filter on Visualization.

5. **Slicer / actionButton**  
   - [ ] Confirm slicer → FilterComponent or Visualization per §6.  
   - [ ] Confirm actionButton → component type and optional Visualization (or “button” type).

---

## 8. Validation example: Global Marketing & Customer Insights

Use this section to **verify manually in Power BI Desktop** that every visual in the report maps to the canonical model. Parsed report path: `parsed_output/Global Marketing & Custome_ad094011` (folder name may be truncated).

### 8.1 Report → Dashboard

| Raw (this report) | Canonical | Verify in PBI Desktop |
|-------------------|-----------|------------------------|
| Folder name `Global Marketing & Custome_ad094011` | `Dashboard.id` | Report identity matches. |
| Display name e.g. "Global Marketing & Customer Insights Dashboard" | `Dashboard.name` | Report title in PBI matches. |
| — | `Dashboard.source_system` = `"powerbi"` | Fixed. |
| `pages.json` → `pageOrder` has **3** entries | `Dashboard.is_multi_page` = **true** | [ ] Report has 3 pages. |
| Same 3 page ids in order | `Dashboard.pages` = [Page0, Page1, Page2] | [ ] Page order matches. |

**Outcome:** 1 report → 1 Dashboard with 3 pages.

### 8.2 Pages → DashboardPage

| Page id | displayName (page.json) | page_order | # visuals |
|---------|-------------------------|------------|----------|
| `7b90683d8c04015200ce` | " Customer Segmentation & Targeting" | 0 | 10 |
| `b452f455c97e4d793c06` | "Cross-Channel Analysis" | 1 | 8 |
| `38743722d0b026d77781` | "Multi-Campaign Analysis" | 2 | 8 |

**Verify in PBI Desktop:** [ ] Each page has correct name and order. [ ] Each page’s component count = # visuals in table (10, 8, 8).

### 8.3 Every visual → DashboardComponent (all 26 components)

**Rule:** Each `visual.json` → one **DashboardComponent**. Total visuals = 10 + 8 + 8 = **26**.

**Page 1 — " Customer Segmentation & Targeting" (10 visuals)**

| Visual id | visualType | Component type | Also create |
|-----------|------------|----------------|-------------|
| `fa1fb5d7cb1dc36a83a1` | cardVisual | visualization | Visualization |
| `a8d5011213188600e55a` | cardVisual | visualization | Visualization |
| `56a425679bddc06aed81` | cardVisual | visualization | Visualization |
| `8ccaf343d40810501008` | cardVisual | visualization | Visualization |
| `1a5bf9b117420b2d0583` | slicer | filter / visualization | FilterComponent or Visualization |
| `ade190786818e7ee1580` | slicer | filter / visualization | FilterComponent or Visualization |
| `a4c8f13d993554a29caa` | slicer | filter / visualization | FilterComponent or Visualization |
| `6cfe515b343901805938` | slicer | filter / visualization | FilterComponent or Visualization |
| `3271eea10ced1b066668` | barChart | visualization | Visualization + data_mappings |
| `39a2868a6385c391517e` | actionButton | visualization (or button) | Optional Visualization (empty data_mappings) |

**Verify:** [ ] 10 DashboardComponents on page 1.

**Page 2 — "Cross-Channel Analysis" (8 visuals)**

| Visual id | visualType | Component type | Also create |
|-----------|------------|----------------|-------------|
| `f766ec3e9c1a3c08abd9` | tableEx | visualization | Visualization + data_mappings |
| `116839bf4a40ad630b0e` | lineChart | visualization | Visualization + data_mappings |
| `0580b2b9577747ad6b82` | donutChart | visualization | Visualization + data_mappings |
| `95708cade473ec18c600` | clusteredColumnChart | visualization | Visualization + data_mappings |
| `e3386372b31031655163` | card | visualization | Visualization |
| `028706a7243a0c855eb2` | card | visualization | Visualization |
| `4134bdd193c689269b0a` | card | visualization | Visualization |
| `7d95bfc8d7d38547c271` | actionButton | visualization (or button) | Optional Visualization (empty data_mappings) |

**Verify:** [ ] 8 DashboardComponents on page 2.

**Page 3 — "Multi-Campaign Analysis" (8 visuals)**

| Visual id | visualType | Component type | Also create |
|-----------|------------|----------------|-------------|
| `0305869d2bda1083210a` | slicer | filter / visualization | FilterComponent or Visualization (e.g. customers.Country) |
| `27e0b0e41843d04ba467` | slicer | filter / visualization | FilterComponent or Visualization |
| `71a3fb848d3b0a16e004` | slicer | filter / visualization | FilterComponent or Visualization |
| `5beaf60287a0cbc6c703` | clusteredColumnChart | visualization | Visualization + data_mappings (§8.4) |
| `7e24f393be0c372c03cb` | lineStackedColumnComboChart | visualization | Visualization + data_mappings |
| `e71b263e9038815a9d0c` | card | visualization | Visualization |
| `b0b958f93390949bb427` | card | visualization | Visualization |
| `e0af79c5a2915ffcff59` | actionButton | visualization (or button) | Optional Visualization (empty data_mappings) |

**Verify:** [ ] 8 DashboardComponents on page 3. [ ] Total components across all pages = 26.

### 8.4 One chart in full: queryState → DataMapping

**Chart:** clusteredColumnChart `5beaf60287a0cbc6c703` (Multi-Campaign Analysis).

| queryState / query | Canonical | Verify in PBI |
|--------------------|-----------|---------------|
| **Category** → `marketing_campaign_data.Campaigns Exposed1` | One DataMapping: role `dimension`, datasource_id = `marketing_campaign_data`, field_id = `Campaigns Exposed1` | [ ] One dimension mapping. |
| **Y** → two measures (Conversion Rate by Exposure, Avg Revenue per Customer) | Two DataMappings: role `measure`, correct Entity/Property → datasource_id/field_id | [ ] Two measure mappings. |
| **sortDefinition** (Conversion Rate by Exposure, Descending) | One measure DataMapping has `sort_order` = `"desc"` | [ ] Sort reflected. |
| **position** (x, y, width, height) | DashboardComponent.position (z not in model) | [ ] Position matches (ignore z). |

### 8.5 Slicer example

**Slicer** `0305869d2bda1083210a`: Values = `customers.Country`.

- [ ] One DashboardComponent (type filter or visualization).
- [ ] One FilterComponent or Visualization with field_id = `Country`, datasource_id = `customers`.

### 8.6 actionButton example

**actionButton** `e0af79c5a2915ffcff59`: no queryState.

- [ ] One DashboardComponent (type visualization or button).
- [ ] If Visualization is used: visualization_type e.g. `actionButton`, `data_mappings` = [].

### 8.7 Manual verification summary

1. Open the report in **Power BI Desktop** (source .pbix or same report).
2. Confirm **3 pages** and names/order as in §8.2.
3. On each page, count **visuals** (tiles/charts/slicers/cards/buttons); totals should be 10, 8, 8.
4. For **one chart** (e.g. clustered column on Multi-Campaign Analysis), confirm in the parser output that Category → dimension, Y → measures, sort → sort_order (§8.4).
5. For **one slicer**, confirm component + FilterComponent or Visualization with correct field (§8.5).
6. For **one action button**, confirm component + optional Visualization with empty data_mappings (§8.6).

When the normalizer is implemented, run it on this report and confirm: **total DashboardComponents = 26** and every visual type maps per §4 and §6.

### 8.8 Example canonical model JSON (for verification)

Use these JSON snippets to verify that normalizer output matches the canonical schema. They correspond to **Global Marketing & Customer Insights**: one Dashboard, one full page (Multi-Campaign Analysis), and the chart/slicer/button from §8.4–8.6.

**Dashboard (report level)**

```json
{
  "id": "Global Marketing & Custome_ad094011",
  "name": "Global Marketing & Customer Insights Dashboard",
  "source_system": "powerbi",
  "is_multi_page": true,
  "pages": [
    {
      "page_id": "7b90683d8c04015200ce",
      "page_name": " Customer Segmentation & Targeting",
      "page_order": 0,
      "layout": {},
      "components": []
    },
    {
      "page_id": "b452f455c97e4d793c06",
      "page_name": "Cross-Channel Analysis",
      "page_order": 1,
      "layout": {},
      "components": []
    },
    {
      "page_id": "38743722d0b026d77781",
      "page_name": "Multi-Campaign Analysis",
      "page_order": 2,
      "layout": {},
      "components": []
    }
  ],
  "interactions": []
}
```

*(In real output, each `components` array is filled with DashboardComponents; see below.)*

**DashboardPage — Multi-Campaign Analysis (one page, 8 components)**

```json
{
  "page_id": "38743722d0b026d77781",
  "page_name": "Multi-Campaign Analysis",
  "page_order": 2,
  "layout": {},
  "components": [
    {
      "id": "0305869d2bda1083210a",
      "type": "filter",
      "position": { "x": 1103.9, "y": 42.08, "width": 161.86, "height": 207.18 },
      "filter_id": "filter_0305869d2bda1083210a"
    },
    {
      "id": "5beaf60287a0cbc6c703",
      "type": "visualization",
      "position": { "x": 14.57, "y": 42.08, "width": 854.63, "height": 247.65 },
      "visualization_id": "5beaf60287a0cbc6c703"
    },
    {
      "id": "e0af79c5a2915ffcff59",
      "type": "visualization",
      "position": { "x": 14.13, "y": 672.8, "width": 48.06, "height": 39.58 },
      "visualization_id": "e0af79c5a2915ffcff59"
    }
  ]
}
```

*(Only 3 of 8 components shown; remaining 5 would follow the same pattern.)*

**Visualization — clusteredColumnChart (chart from §8.4)**

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

**Visualization — slicer (Country, §8.5)**  
*(If modeled as Visualization instead of FilterComponent.)*

```json
{
  "id": "viz_0305869d2bda1083210a",
  "name": "slicer",
  "visualization_type": "slicer",
  "source_system": "powerbi",
  "viz_calculated_fields": [],
  "data_mappings": [
    {
      "field_id": "Country",
      "datasource_id": "customers",
      "mapping_role": "dimension"
    }
  ],
  "filters": [],
  "parameters": [],
  "conditional_formatting": null,
  "extended_properties": null
}
```

**Visualization — actionButton (§8.6)**  
*(Requires model change for empty `data_mappings` or use a placeholder; see §9.)*

```json
{
  "id": "e0af79c5a2915ffcff59",
  "name": "actionButton",
  "visualization_type": "actionButton",
  "source_system": "powerbi",
  "viz_calculated_fields": [],
  "data_mappings": [],
  "filters": [],
  "parameters": [],
  "conditional_formatting": null,
  "extended_properties": null
}
```

**FilterComponent (slicer alternative)**  
*(If slicer is modeled as filter component instead of Visualization.)*

```json
{
  "id": "filter_0305869d2bda1083210a",
  "field_id": "Country",
  "datasource_id": "customers",
  "extended_properties": null
}
```

**DashboardMetadata (top-level output with lists)**  
*(Typical normalizer output: one dashboard + flat list of visualizations and optional filter components.)*

```json
{
  "metadata_version": "1.0",
  "source_system": "powerbi",
  "extracted_at": "2025-02-17T00:00:00",
  "dashboards": [
    { "id": "Global Marketing & Custome_ad094011", "name": "Global Marketing & Customer Insights Dashboard", "source_system": "powerbi", "is_multi_page": true, "pages": [] }
  ],
  "visualizations": [],
  "text_components": [],
  "filter_components": [],
  "image_components": [],
  "container_components": [],
  "parameter_components": [],
  "web_content_components": []
}
```

*(In real output, `dashboards[0].pages` and `visualizations` / `filter_components` are populated as in the examples above.)*

**How to verify:** Compare normalizer JSON output against these shapes: same field names, same nesting (Dashboard → pages → components; Visualization.data_mappings; FilterComponent.field_id/datasource_id), and values matching the raw report (e.g. position from visual.json, queryState → data_mappings).

---

## 9. Model changes (implemented)

Implemented in `src/powerbi_to_looker/models/dashboard.py`:

- **Position:** `z: Optional[int] = None` and `tab_order: Optional[int] = None` added for PBI stacking/accessibility.
- **Dashboard:** `report_id: Optional[str] = None` added to link to raw report id.
- **Visualization:** `data_mappings: List[DataMapping] = []` default so actionButton/button can have no data mappings.
- **Visualization.visualization_type:** Allow a “button” or “action”: Already a string; use `"actionButton"` or `"button"` for action buttons.
- **DashboardComponent.type:** `"button"` added to the Literal for actions modeled as components without a full Visualization.

---

## 10. References

- Canonical models: `src/powerbi_to_looker/models/dashboard.py` (Position, DataMapping, Filter, DashboardComponent, DashboardPage, Dashboard, Visualization, etc.).
- Loader: `src/powerbi_to_looker/parser_normalizer/loader.py` (report, pages_metadata, pages, visuals).
- Sample raw: `parsed_output/<report>/Report/definition/` (report.json, pages/pages.json, pages/<id>/page.json, pages/<id>/visuals/<id>/visual.json).
- Semantic mapping: `plan/semantic_model_canonical_mapping.md`.
- Implementation plan: `plan/parser_normalizer_implementation_plan.md` (Phase 2).
