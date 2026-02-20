# Dimension vs measure classification

**Purpose:** Document how we assign canonical `field_type` (dimension | measure) from Power BI parsed model (`Model/database.json`). Formula-based fields use **dimension** or **measure** with `is_calculated=True`; we do not use a separate `calculated_field` type.

**Config:** `config/powerbi_canonical_mapping.yaml` (column_types, summarizeBy, defaults).

---

## 1. Three handlers, no overlap on formulas

| Handler | Output | Rule |
|--------|--------|------|
| **Dimension** | `field_type="dimension"` only | Columns with **no expression** and **no summarizeBy** (or summarizeBy → null). No formula; `is_calculated=False`. |
| **Measure** | `field_type="measure"` only | Columns with **summarizeBy** that maps to an aggregation (e.g. sum → SUM). No formula; `is_calculated=False`; transform applies aggregation to column. |
| **Calc_field** | `field_type="dimension"` or `"measure"` | **All fields that have a formula:** (1) calculated columns → `field_type="dimension"`, (2) model measures → `field_type="measure"`. Both with `is_calculated=True` and `formula` set. |

So: dimension and measure handlers never emit a formula. The calc_field handler emits dimension/measure with `formula` and `is_calculated=True`.

---

## 2. Dimension handler

- **Source:** `model.tables[].columns[]` only.
- **Filter:** Skip any column that has `expression`. Skip any column whose `summarizeBy` maps to a non-null aggregation (those go to measure).
- **Output:** One `Field` per remaining column: `field_type="dimension"`, `formula=None`, `aggregation=None`, `is_calculated=False`. data_type from column.dataType via YAML.

---

## 3. Measure handler

- **Source:** `model.tables[].columns[]` only (columns with summarizeBy).
- **Filter:** Only columns where `summarizeBy` maps to a non-null aggregation (e.g. sum → SUM).
- **Output:** One `Field` per such column: `field_type="measure"`, `aggregation` set from YAML, `formula=None`, `is_calculated=False`. Transform layer will apply this aggregation to the column.

Model measures (`tables[].measures[]`) are **not** handled here; they have formulas and go to calculated_field.

---

## 4. Calc_field handler

- **Source:** (1) `model.tables[].columns[]` where column has `expression`, (2) `model.tables[].measures[]`.
- **Output:** One `Field` per such item: **calculated columns** → `field_type="dimension"`, **model measures** → `field_type="measure"`; both with `formula` set (DAX string) and `is_calculated=True`. `aggregation=None` (transform emits formula as-is to avoid double aggregation).

---

## 5. Summary table

| Source | Handler | field_type | is_calculated | formula | aggregation |
|--------|---------|------------|---------------|---------|-------------|
| Column, no expression, summarizeBy none | dimension | dimension | false | None | null |
| Column, summarizeBy sum (etc.) | measure | measure | false | None | SUM (etc.) |
| Column, has expression | calc_field | dimension | true | DAX | null |
| Model measure (tables[].measures[]) | calc_field | measure | true | DAX | null |

---

## 6. Transform layer contract

- **Dimension** → Emit as dimension (no aggregation unless chart asks).
- **Measure** (no formula) → Apply `aggregation` to the referenced column (e.g. SUM(column)).
- **Measure/Dimension** with `is_calculated=True` (formula set) → Emit formula as-is (translate DAX). Do not apply extra aggregation.

See also: `plan/semantic_model_canonical_mapping.md` §3.5, `validation/semantic_dashboard_relationship.md`.
