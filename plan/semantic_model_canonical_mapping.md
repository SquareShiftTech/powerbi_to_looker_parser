# Semantic Model → Canonical Mapping

**Version:** 1.0  
**Status:** For review  
**Purpose:** Define how Power BI parsed semantic metadata (`Model/database.json`) maps to the canonical model. Documents source/target mapping and any canonical model changes required (and why).

---

## 1. Source: Power BI parsed model structure

Input is the contents of **`Model/database.json`** (and optionally report-level context). Top-level shape:

```json
{
  "name": "Model name (e.g. Global Marketing _ Customer Insights Dashboard_ad094011)",
  "compatibilityLevel": 1600,
  "model": {
    "culture": "en-US",
    "sourceQueryCulture": "en-IN",
    "tables": [ ... ],
    "relationships": [ ... ],
    "cultures": [ ... ],
    "annotations": [ ... ]
  }
}
```

### 1.1 Tables

Each `model.tables[]` has:

| Source path | Type | Description |
|-------------|------|-------------|
| `name` | string | Table name |
| `lineageTag` | string | Stable identifier |
| `isHidden` | bool (optional) | True for date templates, local date tables |
| `columns` | array | Column definitions |
| `measures` | array (optional) | Measure definitions |
| `partitions` | array | Source (M expression or calculated) |
| `hierarchies` | array (optional) | e.g. Date Hierarchy (levels: Year, Quarter, Month, Day) |
| `annotations` | array | PBI annotations |

**Column** (in `columns[]`):

| Source path | Type | Description |
|-------------|------|-------------|
| `name` | string | Column name |
| `dataType` | string | String, Int64, Double, DateTime, Boolean |
| `type` | string (optional) | "calculated", "calculatedTableColumn" (omit = Data) |
| `sourceColumn` | string (optional) | Source reference |
| `expression` | array (optional) | DAX for calculated column |
| `formatString` | string (optional) | Display format |
| `lineageTag` | string | Stable id |
| `summarizeBy` | string | none, sum, etc. |
| `variations` | array (optional) | Date variation / hierarchy link |

**Measure** (in `measures[]`):

| Source path | Type | Description |
|-------------|------|-------------|
| `name` | string | Measure name |
| `expression` | array | DAX (lines of formula) |
| `formatString` | string (optional) | Display format |
| `lineageTag` | string | Stable id |

**Partition** (in `partitions[]`):

| Source path | Type | Description |
|-------------|------|-------------|
| `name` | string | Partition name |
| `mode` | string | "import", "directQuery", etc. |
| `source.type` | string | "m" (M query) or "calculated" |
| `source.expression` | array | M or DAX lines (for connection/source type detection) |

### 1.2 Relationships

Each `model.relationships[]`:

| Source path | Type | Description |
|-------------|------|-------------|
| `name` | string | Relationship id |
| `fromTable` | string | From table name |
| `fromColumn` | string | From column name |
| `toTable` | string | To table name |
| `toColumn` | string | To column name |
| `toCardinality` | string (optional) | e.g. "many" |
| `crossFilteringBehavior` | string (optional) | e.g. "bothDirections" |
| `joinOnDateBehavior` | string (optional) | e.g. "datePartOnly" |

Power BI does **not** store join direction (LEFT/INNER) in this layout; use config default.

---

## 2. Target: Canonical model (current)

- **MetadataModel:** metadata_version, source_system, extracted_at, datasources[], cross_datasource_relationships[].
- **Datasource:** id, name, source_system, datasource_type, connection, tables[], table_relationships[], fields[], parameters[], extended_properties.
- **Connection:** type, server, database, schema.
- **Table:** id, name, schema, table_name.
- **TableRelationship:** from_table, to_table, join_type, on_columns (list of {from, to}).
- **Field:** id, name, field_type (dimension | measure | calculated_field), data_type, source_table, source_column, aggregation, formula, depends_on, is_calculated.

---

## 3. Mapping rules (semantic → canonical)

### 3.1 MetadataModel

| Canonical field | Source | Rule |
|-----------------|--------|------|
| metadata_version | — | Fixed "1.0" |
| source_system | — | "powerbi" |
| extracted_at | — | Now (or from collector if passed) |
| datasources | model | One datasource per database.json (see 3.2) |
| cross_datasource_relationships | — | Empty for single-model .pbix |

### 3.2 Datasource

| Canonical field | Source | Rule |
|-----------------|--------|------|
| id | database.name or lineage | Sanitized model name or derived id |
| name | database.name | Model display name |
| source_system | — | "powerbi" |
| datasource_type | — | "embedded" (for .pbix) or from config |
| connection | model.tables[].partitions[].source | See 3.3 |
| tables | model.tables[] | See 3.4 |
| table_relationships | model.relationships[] | See 3.6 |
| fields | model.tables[].columns + .measures | See 3.5 |
| parameters | — | [] (unless report params added later) |
| extended_properties | model.culture, model.annotations | Optional |

### 3.3 Connection and datasource type

| Canonical field | Source | Rule |
|-----------------|--------|------|
| type | partition.mode | "import" → live/extract; "directQuery" → direct_query (map via YAML) |
| server | M expression | From first partition with source.type "m": parse M for host (e.g. BigQuery project, SQL Server host). If not parseable, use default or empty. |
| database | M expression | e.g. BigQuery dataset name, SQL database name. Parse from M. |
| schema | M expression | e.g. BigQuery schema / SQL schema. Parse from M when present. |

**New field required:** **`datasource_type`** (or equivalent) to identify **kind** of backend (BigQuery, SQL Server, Snowflake, etc.).

**Reason:** Looker and downstream need to know the backend for SQL dialect and connection. Power BI stores only M; we infer from function names (e.g. `GoogleBigQuery.Database()`, `Sql.Database()`).

**Proposed change:**

- Add **`connection_provider: Optional[str] = None`** to **Connection** (e.g. "bigquery", "sql_server", "snowflake").  
  **Or** add **`datasource_type: Optional[str] = None`** to **Datasource** (semantic: "bigquery", "sql_server").  
- Parser sets this from partition source (M) using a YAML map: M function or pattern → canonical provider/datasource_type.  
- If not identifiable, leave null or "unknown".

### 3.4 Table

| Canonical field | Source | Rule |
|-----------------|--------|------|
| id | table.lineageTag or table.name | Stable id |
| name | table.name | Display name |
| schema | partition.source (M) | From M (e.g. schema/dataset); null for calculated table |
| table_name | table.name | Same as name for PBI |

**Hierarchy support:** Power BI has `table.hierarchies[]` (e.g. Date Hierarchy with levels). Canonical has no hierarchy concept today.

**Proposed change:**

- Add **`hierarchies: Optional[List[dict]] = None`** to **Table** (BI-agnostic: list of {name, levels: [{name, column}]}).  
  **Or** keep hierarchies in **`extended_properties`** (e.g. `{"hierarchies": [...]}`) to avoid changing canonical schema.  
- **Recommendation:** Put in **Table.extended_properties** for now (`"hierarchies": table.hierarchies` as-is or minimal shape). If Transformer needs stronger typing, add optional `hierarchies` to Table later.

### 3.5 Field (dimensions and measures)

**Rule:** Every field is either **dimension** or **measure**. If it has a **formula** (DAX expression), it is also treated as **calculated** (field_type = calculated_field or is_calculated = true).

| Canonical field | Source (column) | Source (measure) | Rule |
|-----------------|------------------|------------------|------|
| id | column.lineageTag | measure.lineageTag | Stable id |
| name | column.name | measure.name | As-is |
| field_type | column type | — | "dimension" or "calculated_field" (YAML: Data→dimension, Calculated/calculatedTableColumn→dimension or calculated_field). Measures → "measure"; measures with expression → "measure" + is_calculated true (or calculated_field per project). |
| data_type | column.dataType | — | YAML: String→string, Int64→number, Double→number, DateTime→datetime, Boolean→boolean. Measures: default measure_data_type (number). |
| source_table | table.name | table.name | Owning table |
| source_column | column.sourceColumn / column.name | — | Column name or source ref |
| aggregation | column.summarizeBy (YAML) | DAX inference (YAML) | Dimension: summarizeBy → canonical aggregation or null. Measure: from DAX (SUM, AVG, etc.) via measure_aggregation YAML; else null. |
| formula | column.expression (if present) | measure.expression | Concatenate expression array to string (DAX). |
| depends_on | — | Optional: parse DAX for table/column refs | Can be null in Phase 1. |
| is_calculated | true if expression present | true if expression present | True for calculated columns and all measures with formula. |

**Format string / PBI-specific:** Store in **Field.extended_properties** (e.g. `{"format_string": "0.00%"}`) so canonical stays agnostic.

**New field (optional):** If we want a first-class **format_string** on Field for Transformer, add `format_string: Optional[str] = None` to Field. **Recommendation:** Keep in extended_properties unless Transformer strongly needs it on the top level.

### 3.6 TableRelationship

| Canonical field | Source | Rule |
|-----------------|--------|------|
| from_table | relationship.fromTable | As-is |
| to_table | relationship.toTable | As-is |
| join_type | — | From YAML default (e.g. LEFT); PBI does not store. |
| on_columns | fromColumn, toColumn | [{"from": fromColumn, "to": toColumn}] |

Power BI cardinality/crossFiltering can go into **extended_properties** on a future Relationship model if needed; for now TableRelationship is minimal.

---

## 4. Canonical model changes summary

| Change | Where | Why |
|--------|--------|-----|
| **Connection: add connection_provider (or Datasource: datasource_type)** | models/canonical.py | Identify backend (BigQuery, SQL Server, etc.) from M; required for Transformer and connection setup. |
| **Table: hierarchies in extended_properties** | models/canonical.py | Store hierarchy (e.g. Date Hierarchy) as-is for Transformer; no schema change if we use extended_properties. Optional: add `hierarchies: Optional[List[dict]] = None` to Table if we want first-class. |
| **Field: keep as-is** | — | dimension | measure | calculated_field; is_calculated and formula already exist. format_string in extended_properties. |

**Minimal change set for Phase 1:**

1. **Connection:** Add `connection_provider: Optional[str] = None` (values e.g. "bigquery", "sql_server", "snowflake", "unknown").  
2. **Table:** Use **extended_properties** for hierarchies (no new field). If later needed, add `hierarchies`.  
3. **Field:** No new fields; use extended_properties for format_string, lineageTag, etc.

---

## 5. YAML config (semantic)

- **data_types:** Power BI dataType → canonical data_type (already in powerbi_canonical_mapping.yaml).
- **column_types:** Data | Calculated | calculatedTableColumn → dimension | calculated_field.
- **measure_aggregation:** DAX function name → canonical aggregation (SUM, AVG, COUNT, etc.); already present.
- **summarizeBy:** Power BI summarizeBy → canonical aggregation for dimensions (e.g. sum → SUM, none → null).
- **relationship.join_type.default:** LEFT (already present).
- **connection_provider:** Add new section: M pattern or source type → canonical provider (e.g. "GoogleBigQuery.Database" → "bigquery", "Sql.Database" → "sql_server"). Parser uses this to set Connection.connection_provider.

---

## 6. Exception handling (semantic)

- Missing required key in model (e.g. tables, name): log, set safe default or fail that report; orchestrator writes _error.json.
- Invalid or unknown dataType/column type: use YAML default (e.g. string).
- Relationship with unknown table name: still emit TableRelationship; optional validation step can warn.
- M parse failure for connection: set connection_provider to "unknown"; server/database/schema from defaults or empty.

---

## 7. References

- `src/powerbi_to_looker/models/canonical.py` — current canonical model.
- `src/powerbi_to_looker/config/powerbi_canonical_mapping.yaml` — current mapping.
- `plan/parser_normalizer_requirements.md` — requirements.
- `plan/parser_normalizer_implementation_plan.md` — implementation plan.
