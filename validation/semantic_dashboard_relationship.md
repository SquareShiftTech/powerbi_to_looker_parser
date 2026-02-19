# Relationship between semantic canonical and dashboard canonical

Both are produced from the same **parsed_output** (per report) but describe different aspects:

| | Semantic (`metadata_model.json`) | Dashboard (`dashboard_metadata.json`) |
|---|----------------------------------|--------------------------------------|
| **Source** | `raw["model"]` (Model/database.json) | `raw["pages_metadata"]`, `raw["pages"]` (Report definition or sections) |
| **Content** | One **MetadataModel**: datasources, tables, table_relationships, **fields** (dimensions, measures) | **DashboardMetadata**: dashboards, pages, visualizations, filter_components, with **data_mappings** and filter field references |

## How they relate

Dashboard visuals and filters **reference the same logical fields** that the semantic model describes:

- In **semantic**: each **Field** has `name`, `source_table` (table name), and lives under a **Datasource** (one per model). Tables have `name` (e.g. `dim_courses`, `fact_enrollments`).
- In **dashboard**: each **DataMapping** and **FilterComponent** uses:
  - **`datasource_id`** = Power BI visual query **Entity** = **table name** (same as semantic `Table.name`)
  - **`field_id`** = Power BI visual query **Property** = **field name** (same as semantic `Field.name` for that table)

So:

- **Dashboard `datasource_id`** corresponds to **semantic `Table.name`** (not to semantic `Datasource.id`; the semantic model has one Datasource per report model).
- **Dashboard `field_id`** corresponds to **semantic `Field.name`**, for the field whose **`Field.source_table`** equals that table name.

A dashboard reference `(datasource_id, field_id)` is **consistent** with the semantic model when there exists a **Field** in the semantic datasource such that `Field.source_table == datasource_id` and `Field.name == field_id`.

## Why this matters

- **Looker / downstream**: Semantic describes the data model (tables, columns, measures). Dashboard describes which fields are used in which visuals and filters. Linking them allows generating LookML that uses the same field identifiers in views and in dashboard tile definitions.
- **Validation**: You can check that every `(datasource_id, field_id)` in dashboard visualizations and filter_components resolves to a field in the semantic model (see cross-reference validation below).

## Cross-reference validation

To ensure “dashboard and semantic stay in sync,” a validator can:

1. Load both `metadata_model.json` and `dashboard_metadata.json` for each report.
2. Build a set of valid (table, field) pairs from semantic: `(Field.source_table, Field.name)` for all fields in the semantic datasource(s).
3. For each dashboard **DataMapping** and **FilterComponent**, take `(datasource_id, field_id)` and assert it exists in that set.
4. Report any dashboard reference that has no matching semantic field (e.g. typo, or field removed from model).

The existing validation test in `tests/validation/` only checks that each canonical file parses as valid JSON/schema; it does **not** yet run this cross-reference check. Adding it would close the loop between semantic and dashboard canonicals.
