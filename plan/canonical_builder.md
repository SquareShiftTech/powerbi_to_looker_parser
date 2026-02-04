# Canonical Builder Plan: Raw Metadata → MetadataModel

Plan for implementing the **canonical builder** that converts raw Power BI collector output into the canonical `MetadataModel` (used by transformer → generator).

---

## 1. Scope and responsibility

**Canonical builder:** Convert the single raw metadata dict (collector output) into the canonical schema: `MetadataModel` with `Datasource(s)`, `Table`, `TableRelationship`, `Field`, `Connection`, and `Parameter`.

- **Input:** Raw dict from collector: `workspace_id`, `workspace_name`, `report_name`, `workspaces`, `relationships`, `report_layout`, `dax_measures`, `power_query`, `rls`.
- **Output:** `MetadataModel` (Pydantic) with one datasource (for single-report flow), populated tables, relationships, and fields.

Reference: [powerbi_to_looker/src/powerbi_to_looker/canonical/models.py](../powerbi_to_looker/src/powerbi_to_looker/canonical/models.py), [powerbi_to_looker/src/powerbi_to_looker/canonical/builder.py](../powerbi_to_looker/src/powerbi_to_looker/canonical/builder.py).

---

## 2. Input (raw) vs output (canonical) mapping

| Canonical piece | Source in raw | Notes |
|-----------------|---------------|--------|
| **Connection** (server, database, schema) | `power_query[]` M expressions (e.g. `Sql.Databases("...")`, schema from `dbo_*`) | Parse M for server/database or use defaults. |
| **Datasource** (id, name) | `workspaces[].datasets[]`: `id`, `name` | First workspace/dataset for single-report flow. |
| **Table** (id, name, schema, table_name) | `workspaces[0].datasets[0].tables[]`: `name` | id/schema derivable; table_name = name. |
| **TableRelationship** (from_table, to_table, join_type, on_columns) | Top-level or dataset `relationships[]`: fromTable, fromColumn, toTable, toColumn | See §3. |
| **Field (dimension)** | Each table `columns[]`: name, dataType | Map PBI dataType → canonical data_type. |
| **Field (measure)** | Each table `measures[]`: name, expression (DAX) | field_type = `measure`; formula = expression. |
| **Field (calculated_field)** | Column with `columnType: "Calculated"` or column-level expression | Only when present in raw; current collector output has none. |
| **Parameters** | Report/dataset parameters (if any from API) | **Empty for now:** `parameters=[]`. |
| **Primary key** | Not in raw | **Keep null if no PK** — do not infer. |

All enum and mapping tables above (data types, column types, relationship join type, measure aggregation) are driven from canonical YAML; see §9.

---

## 3. Relationships and join behavior

### 3.1 Which relationships to emit

- **Include:** Only relationships where both `toTable` and `toColumn` are non-null (real table-to-table joins).
- **Skip:** Relationships with `toTable: null` / `toColumn: null` (Power BI date/auto-date “relationships” — not actual joins).

### 3.2 Join type (Power BI semantics)

- **All emitted relationships:** Use **LEFT** (left outer join) so behavior matches Power BI (many-side rows preserved).
- Canonical `join_type`: `"LEFT"` (or `"LEFT_OUTER"` if standardised in code).
- Transformer/Generator: map to Looker `type: left_outer`.

### 3.3 Example (Suprer Store Dashboard)

| From → To | Cardinality (raw) | Canonical join_type |
|-----------|-------------------|---------------------|
| Orders → Order_Details (Order_ID) | M:M | LEFT |
| Orders → Region (Order_ID → ID) | M:1 | LEFT |
| Orders → Returns (Order_ID) | M:1 | LEFT |
| Order_Details/Orders date columns → null | (skipped) | — |

---

## 4. Field mapping rules

| Raw | Canonical Field |
|-----|-----------------|
| Table column (`columnType: "Data"`) | `field_type: "dimension"`, `source_table`, `source_column`, `data_type` from column `dataType` mapping. |
| Table measure (name + expression) | `field_type: "measure"`, `source_table` = table name, `formula` = DAX expression; `aggregation` = null (or optional best-effort infer later). |
| Column with `columnType: "Calculated"` (when available) | `field_type: "calculated_field"`; reserve for future when collector exposes it. |

### 4.1 Power BI dataType → canonical data_type

Map to canonical: `string`, `number`, `date`, `datetime`, `boolean`.

- String → string  
- Int64, Double → number  
- DateTime → datetime  
- (Date-only if present → date)  
- Boolean → boolean  

---

## 5. Decided behaviour (from discussion)

- **Primary key:** Keep null when raw has no explicit PK; do not infer from column names or order.
- **Measures:** Map Power BI measures to canonical **measures** (`field_type: "measure"`).
- **Parameters:** Use empty list for now: `parameters=[]`.
- **Calculated fields:** In current metadata all columns are `columnType: "Data"` (no calculated columns). Use `calculated_field` only when API/pbixray returns calculated columns (e.g. columnType "Calculated" or column expression).

---

## 6. Metadata sufficiency (for given data model)

For the current data model (Orders, Order_Details, Region, Returns + relationships + measures), the collector output has **enough** to populate the canonical model:

- Connection: from power_query or defaults ✓  
- Datasource id/name: from workspace/dataset ✓  
- Tables: from dataset.tables ✓  
- TableRelationships: from relationships (filter null toTable) ✓  
- Fields (dimensions): from columns ✓  
- Fields (measures): from measures ✓  
- Parameters: [] ✓  

No additional collector output is required for the canonical builder for this scope.

---

## 7. Implementation order (suggested)

1. Connection + single Datasource from first workspace/dataset.
2. Tables from `dataset.tables`.
3. TableRelationships from raw `relationships` (skip null toTable; join_type LEFT).
4. Fields: dimensions from columns (with dataType → canonical data_type), then measures from table `measures[]`.
5. Parameters = [].
6. (Later) Optional: infer aggregation from DAX for measures; support calculated_field when raw provides it.

---

## 8. Edge cases / notes

- **Multiple datasets:** Current flow is one report → one dataset; one datasource in canonical. Split/multi-datasource can be added later if needed.
- **Measure “home” table vs DAX reference:** e.g. “Customer Count” on Order_Details but expression references Orders. Keep canonical `source_table` as the table the measure is declared on; transformer can handle cross-table reference later if needed.
- **Duplicate relationships:** Dedupe by (fromTable, fromColumn, toTable, toColumn) when building TableRelationship list.
- **RLS:** Raw has `rls: []`. Canonical model does not yet model RLS; can be added later if needed.

---

## 9. Mapping rules (YAML) – canonical only

Per the architecture document, mapping rules are defined in YAML. The **canonical** YAML file(s) contain **only Power BI → canonical** mappings. Canonical → Looker/LookML mappings belong to the **transformer** (see [plan/yaml_rules.md](yaml_rules.md)), not here.

### 9.1 What to manage in canonical YAML

| Section | Purpose | Example |
|--------|----------|---------|
| **data_types** | Power BI column `dataType` → canonical `Field.data_type` | `String` → `string`, `Int64`/`Double` → `number`, `DateTime` → `datetime`, `Boolean` → `boolean` |
| **column_types** | Power BI `columnType` → canonical `Field.field_type` | `Data` → `dimension`, `Calculated` → `calculated_field` |
| **relationship.join_type** | Power BI relationship → canonical `TableRelationship.join_type` | `default: LEFT` (Power BI semantics); optional per cardinality later |
| **measure_aggregation** | DAX / Power BI measure → canonical `Field.aggregation` | e.g. SUM/SUMX → `SUM`, DISTINCTCOUNT/COUNT → `COUNT`, AVERAGE/AVERAGEX → `AVG`, MIN/MAX → `MIN`/`MAX`; default `null` when not inferrable |
| **defaults** | Fallback when raw value is missing or unknown | e.g. `data_type: string`, `join_type: LEFT` |

### 9.2 What not to put in canonical YAML

- **Canonical → LookML** mappings (e.g. canonical `data_type` → LookML type, canonical `join_type` → Looker `left_outer`, canonical `aggregation` → LookML measure type). Those are **transformer** responsibility.

### 9.3 File location (suggested)

- e.g. `powerbi_to_looker/config/powerbi_canonical_mapping.yaml` or `rules/powerbi_canonical.yaml`.
- Canonical builder loads this file when building the MetadataModel; no Looker-specific keys in this file.
