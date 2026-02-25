# Cross-table formula reference resolution

**Purpose:** Resolve unqualified DAX references (e.g. `[Total Enrollments]`) to the correct Looker view when the field lives on another table, so formulas like `DIVIDE([Total Enrollments], [Total Course Capacity], 0)*100` emit `${other_view.total_enrollments_measure}` instead of `${total_enrollments_measure}` (same-view).

**Scope:** Transformer only. No canonical model schema or formula_ast change.

---

## 1. Problem

- **DAX:** `DIVIDE([Total Enrollments], [Total Course Capacity], 0)*100`
- **Current output:** References resolve as if they were on the **current** view (e.g. `${total_enrollments_measure}`), so the measure is wrong when "Total Enrollments" / "Total Course Capacity" live on **other** tables.
- **Why:** The formula uses **unqualified** refs (`[Total Enrollments]`). The parser correctly sets `table=None` (no table in the formula text). The transformer builds a **per-view** resolution map from the **current table’s fields only**, so other-table fields are missing and we fall back to `clean_ref_name(col)`, which is same-view.

---

## 2. Current behavior

| Component | Behavior |
|-----------|----------|
| **Canonical model** | Each field has `source_table`. Formula AST has `column_ref` with `table=None` for `[Col]`. No change needed. |
| **Transformer `build_views`** | For each table, `resolution_map` is built from **that table’s** `table_fields` only. Keys: display name; values: `field_name` or `field_name_measure`. |
| **Formula converter `_convert_column_ref`** | Unqualified ref: `res_map.get(col)` then `f"${{{resolved}}}"`. If key missing, fallback `clean_ref_name(col)` → same-view name. Qualified ref: `f"{tbl}.{clean_ref_name(col)}"` (no `${}`). |

---

## 3. Desired behavior

- When converting a formula on view **V**, an unqualified ref to a field that belongs to **another** table **T** should resolve to a **cross-view** Looker reference: `${view_name_T.resolved_field_name}` (e.g. `${dim_courses.total_enrollments_measure}`).
- Same-view refs keep current behavior: `${field_name}` or `${field_name_measure}`.
- Looker explores join views, so `${other_view.measure}` is valid in the base view’s measure SQL when the explore includes that join.

---

## 4. Approach

### 4.1 Build a model-wide resolution map (transformer)

- **Where:** `build_views()` in `src/powerbi_to_looker/transformer/views/builder.py`.
- **When:** Before the per-table loop (or in a first pass over tables), build a **global** map that supports resolving **any** field by display name to its Looker reference.

Options:

- **Option A – Two-pass in `build_views`:**  
  - **Pass 0 (new):** For each table (same order as now), compute `view_name`, and for each of its fields compute `field_name` (clean + dedupe) and `_measure_pattern` (and other classification). Do **not** build artifact views yet; store per-table results in a structure keyed by table name (e.g. `table_view_info[table_name] = { "view_name": ..., "fields": [ { "name", "field_name", "_measure_pattern" }, ... ] }`).  
  - Then build a **global resolution map**: for each table and each field, key = field display name (e.g. `"Total Enrollments"`), value = `view_name.field_name` or `view_name.field_name_measure`. If the same display name appears on multiple tables, we need a strategy (see §5).  
  - **Existing loop:** When building each view, for formula conversion use a **merged** resolution map: same-view entries as today (value = `field_name` or `field_name_measure`), and for any other display name use the global map value (e.g. `other_view.field_name_measure`). So the map passed to `convert_with_status` can have values that are either `field_name` (same view) or `view_name.field_name` (other view).

- **Option B – Single pass with deferred resolution:**  
  Build views in order; when building view V, the resolution map for V includes V’s fields. For “other” tables we don’t have view names / field names yet unless we precompute them. So we still need a pre-pass to get view names and resolved field names for all tables, then Option A is the same.

**Recommendation:** Pre-pass to compute per-table view names and per-field resolved names (and measure_pattern), then build a global map `display_name -> resolved_value` (with disambiguation if needed). When building each view, merge: local map (current table) overrides for same-view; fill the rest from the global map. Pass this merged map to `convert_with_status`.

### 4.2 Resolution map value format

- **Same-view:** `field_name` or `field_name_measure` (no prefix). Converter already emits `${resolved}` → `${total_enrollments_measure}`.
- **Other-view:** `view_name.field_name` or `view_name.field_name_measure`. Converter emits `${resolved}` → `${dim_courses.total_enrollments_measure}`.

So the formula converter does **not** need a signature change: it already does `return f"${{{resolved}}}"` for unqualified refs. We only need to feed it a map that sometimes returns `view.field` from the transformer.

### 4.3 Qualified refs (DAX `'Table'[Column]`)

- Today: `_convert_column_ref` with `table` set returns `f"{tbl}.{clean_ref_name(col)}"` (no `${}`). That is table.column, which in BQ/SQL might be an alias.
- In Looker, if the formula lives in a derived table and references another view’s measure, we may need `${view_name.field_name}`. So if we have a “table name → view name” map, we could translate qualified refs to `${view_name.resolved_field_name}` when the table is another view. **Out of scope for this plan:** keep qualified ref behavior as-is; we can add a follow-up to map table name → view name and emit `${view.field}` for qualified cross-table refs if needed.

---

## 5. Disambiguation (same display name on multiple tables)

- If two tables have a field with the same display name (e.g. "Name"), the global map cannot store a single `name -> value`.
- **Strategy 1 – First wins:** Global map key = display name; value = first table’s `view_name.field_name`. Simple but can be wrong.
- **Strategy 2 – Prefer current view:** When building the map for view V, for each display name that appears on multiple tables, set the map entry to the **current view’s** field if that view has it; otherwise use the single other table’s value; if multiple others, first or document as ambiguous.
- **Strategy 3 – Map to list:** `display_name -> [ (view_name, resolved_name), ... ]`. Converter (or builder) then needs current view context: prefer the entry for the current view; if not present, use the only entry; if multiple and none is current view, pick one (e.g. first) and optionally flag. This requires passing `current_view_name` into the converter or resolving in the builder before calling the converter.

**Recommendation:** Start with **Strategy 2** in the transformer: when building the merged resolution map for view V, (1) add all of V’s fields (same-view); (2) for display names not in V, add entries from the global map; if global map has multiple tables for the same name, prefer the one that is “closest” (e.g. by relationship) or first. If we only have one field per display name across the model (common for measure names), no disambiguation needed.

---

## 6. Implementation order

1. **Pre-pass in `build_views`**  
   Compute for every table (that we don’t skip): view_name, and for each field: field_name (clean + dedupe), _measure_pattern (and any other classification needed). Store in a structure (e.g. `table_view_info`) keyed by table name. Reuse existing helpers: `clean_field_name`, `deduplicate_field_names`, and the same classification logic as in the current Pass 1.

2. **Global resolution map**  
   Build `global_resolution: dict[str, str]` (or a structure that supports multiple tables per name). For each table in `table_view_info` and each field, set `global_resolution[display_name] = view_name.field_name` or `view_name.field_name_measure`. Handle duplicates (e.g. keep list per name or “first wins” and document).

3. **Per-view merged map**  
   In the existing table loop, after building the current table’s local `resolution_map` (same as today), merge with global: for each key in `global_resolution` that is not in the local map, add it (so other-view refs are available). If we use “prefer current view,” local map already overrides.

4. **Pass merged map to formula conversion**  
   All calls to `convert_with_status(formula_ast, resolution_map)` already use the per-view resolution_map; once that map is merged with global, no signature change. Verify that values like `dim_courses.total_enrollments_measure` produce `${dim_courses.total_enrollments_measure}` in the converter.

5. **Tests**  
   - Unit test: build a minimal `tables` + `fields` with two tables; one measure on table A, a formula on table B that references A’s measure. Assert converted formula contains `${view_a.measure_name}` (or `_measure` suffix as appropriate).  
   - Integration test: use existing Education (or similar) canonical model and assert a known cross-table measure ref in a formula resolves to the correct view.

---

## 7. Files to touch

| File | Change |
|------|--------|
| `src/powerbi_to_looker/transformer/views/builder.py` | Pre-pass for view names and field resolution; global resolution map; merge into per-view map before `convert_with_status`. |
| `src/powerbi_to_looker/transformer/views/formula_converter.py` | No change if resolved value is already `view.field`; confirm `${resolved}` is correct for values containing `.`. |
| Tests | New or updated transformer test(s) for cross-table formula resolution. |

---

## 8. Out of scope

- **Canonical model:** No change to schema or to formula_ast (table stays null for unqualified refs).
- **Qualified refs:** DAX `'Table'[Column]` → table.col; translating to `${view_name.field_name}` when table is another view can be a follow-up.
- **Parser:** No change; unqualified refs correctly have `table=None`.

---

## 9. Implementation status

- **Done:** Pre-pass in `build_views` (table_view_info + global_resolution); `_prepare_table_fields` extracted and used in pre-pass and main loop; per-view resolution_map merged with global_resolution; formula converter unchanged (values like `view.field` already emit `${view.field}`). Test `test_cross_table_formula_resolution` in `test_integration_transformer.py` asserts cross-view ref in formula sql.

---

## 10. References

- Current resolution map: `builder.py` §3 and §4 (lines ~111–119, ~145–166).
- Formula converter column ref: `formula_converter.py` `_convert_column_ref` (unqualified → `res_map.get(col)`, then `f"${{{resolved}}}"`).
- Plan style: `plan/dimension_measure_classification.md`, `plan/transformer_requirements.md`.
