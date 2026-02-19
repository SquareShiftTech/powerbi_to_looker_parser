# Dimension vs measure classification

**Purpose:** Document how we assign canonical `field_type` (dimension, measure, calculated_field) from Power BI parsed model (`Model/database.json`). Used by the semantic layer (dimension + measure handlers) and by the transform layer when emitting LookML/SQL.

**Config:** `config/powerbi_canonical_mapping.yaml` (column_types, summarizeBy, defaults).

---

## 1. Source of fields

Canonical **fields** come from two places in the Power BI model:

| Source | Path | Description |
|--------|------|-------------|
| **Columns** | `model.tables[].columns[]` | Table columns (data, calculated, or from calculated tables). |
| **Measures** | `model.tables[].measures[]` | Model measures: DAX expressions (e.g. `AVERAGE(...)`, `SUM(...)`). |

Columns and measures are processed by different handlers; the combined list is the datasource’s `fields[]`.

---

## 2. Classification for columns (dimension handler)

Columns are classified using **column type** and **summarizeBy**:

### 2.1 Base type from column type

Power BI column `type` is mapped via YAML **column_types**:

| Power BI column.type | Canonical base field_type |
|----------------------|---------------------------|
| (omit / Data) | dimension |
| Calculated | calculated_field |
| calculatedTableColumn | dimension |

So by default a column is **dimension** or **calculated_field** from its type alone.

### 2.2 Override: summarizeBy → measure

If the column has **summarizeBy** set to an aggregation (e.g. `sum`), we treat it as a measure for canonical purposes:

| Condition | Result |
|-----------|--------|
| Column has `summarizeBy` and YAML maps it to a non-null **aggregation** (e.g. sum → SUM) | **field_type = "measure"**, **aggregation** = that value (e.g. SUM). data_type defaults to measure_data_type (number) if not set. |
| Column has `summarizeBy` = none (or unmapped) | Keep **base field_type** (dimension or calculated_field). **aggregation** = null. |

So:

- **dimension** = column with no aggregation (summarizeBy none or default).
- **calculated_field** = column with type Calculated and no aggregation.
- **measure** (from columns) = column with summarizeBy that maps to an aggregation (e.g. sum). These get **aggregation** set; the transform layer will apply that aggregation to the column (e.g. SUM(column)).

---

## 3. Classification for model measures (measure handler)

All entries in **`model.tables[].measures[]`** are emitted as:

| Canonical field | Value |
|-----------------|--------|
| field_type | **"measure"** |
| formula | DAX expression (string or joined lines). |
| aggregation | **null** |
| is_calculated | true when formula is present. |

We do **not** set aggregation on model measures. The DAX formula is already the full expression (e.g. `AVERAGE(fact_enrollments[total_marks])`). Setting aggregation there would imply “apply this aggregation again” and cause **double aggregation** in the transform layer. So: measure with formula and aggregation null → transform layer should **emit formula only**.

---

## 4. Summary table

| Source | field_type | aggregation | formula | When |
|--------|------------|-------------|---------|------|
| Column, type Data, summarizeBy none | dimension | null | (optional) | Regular dimension. |
| Column, type Calculated, summarizeBy none | calculated_field | null | (optional) | Calculated column. |
| Column, type Data/Calculated, summarizeBy sum (etc.) | measure | SUM (etc.) | (optional) | Column used as measure; transform applies aggregation. |
| Model measure (tables[].measures[]) | measure | **null** | DAX | Full expression; transform emits formula only. |

---

## 5. Transform layer contract

- **Measure with formula and aggregation = null**  
  → Emit the formula as-is (translate DAX to SQL/LookML expression). Do **not** apply an extra aggregation.

- **Measure with aggregation set** (e.g. from summarizeBy on a column)  
  → Apply that aggregation to the referenced column (e.g. SUM(dimension)).

- **Dimension / calculated_field**  
  → Emit as dimension (no aggregation unless the chart asks for it elsewhere).

See also: `plan/semantic_model_canonical_mapping.md` §3.5 (Field mapping), `validation/semantic_dashboard_relationship.md` (dashboard refs to semantic fields).
