# Plan: Filter Hidden Tables & Add Derived Table SQL

**Version:** 1.0  
**Status:** Implementation  
**Date:** 2026-02-23

---

## Overview

This plan implements two features:
1. **Filter hidden system tables** (DateTableTemplate, LocalDateTable) from view generation
2. **Add derived_table_sql** for calculated tables by parsing formula AST in canonical model

---

## Part 1: Filter Hidden System Tables

### Problem
- DateTableTemplate and LocalDateTable are system-generated, hidden tables (`isHidden: true`)
- They're not visible in Power BI UI but appear in metadata
- Currently being created as views, causing:
  - Unnecessary views in output
  - Broken joins (if we skip them but joins reference them)
  - Orphaned fields

### Solution
Filter out tables with `isHidden: true` at two levels:
1. **Views builder** - Skip creating views for hidden tables
2. **Explores builder** - Skip joins that reference hidden tables

### Implementation Steps

#### Step 1.1: Filter in views/builder.py
- Location: `src/powerbi_to_looker/transformer/views/builder.py`
- Change: Add check after `table_name` extraction, before processing
- Logic:
  ```python
  extended_props = t.get("extended_properties") or {}
  is_hidden = extended_props.get("isHidden", False)
  if is_hidden:
      continue  # Skip hidden tables
  ```

#### Step 1.2: Filter relationships in explores/builder.py
- Location: `src/powerbi_to_looker/transformer/explores/builder.py`
- Change: Check if `to_table` is hidden before creating join
- Logic:
  ```python
  # Skip joins to hidden tables
  to_table_obj = next((t for t in tables if (t.get("table_name") or t.get("name") or "").strip() == to_t), None)
  if to_table_obj:
      to_extended_props = to_table_obj.get("extended_properties") or {}
      if to_extended_props.get("isHidden", False):
          continue  # Skip joins to hidden tables
  ```

### Impact
- ✅ Cleaner output (matches Power BI UI)
- ✅ No broken joins (filtered at relationship level)
- ⚠️ Fields referencing hidden tables will be lost (acceptable - they're system fields)

---

## Part 2: Add Derived Table SQL for Calculated Tables

### Problem
- Calculated tables (like "Customer Exposure Summary") have DAX formulas
- Currently `derived_table_sql` is always `None` (line 176 comment says "later pass")
- Generated views use `${TABLE}` which doesn't work without derived_table

### Solution
1. Parse table formula AST during normalization (in `tables.py`)
2. Store `formula_ast` and `formula_parse_error` in canonical Table model
3. Use AST in transformer to generate `derived_table_sql`

### Implementation Steps

#### Step 2.1: Update Table Model
- Location: `src/powerbi_to_looker/models/canonical.py`
- Change: Add `formula_ast` and `formula_parse_error` fields
- Fields:
  ```python
  formula_ast: Optional[dict] = None  # Parsed DAX AST (dict)
  formula_parse_error: Optional[str] = None  # Parse error message
  ```

#### Step 2.2: Parse Formula in tables.py
- Location: `src/powerbi_to_looker/parser_normalizer/semantic/tables.py`
- Change: Parse formula after extracting it, before creating Table object
- Logic:
  ```python
  from powerbi_to_looker.dax.parser import parse_formula
  
  # After extracting formula_val
  formula_ast = None
  formula_parse_error = None
  if formula_val:
      formula_ast, formula_parse_error = parse_formula(formula_val)
  
  # Pass to Table constructor
  Table(..., formula_ast=formula_ast, formula_parse_error=formula_parse_error)
  ```

#### Step 2.3: Generate derived_table_sql in builder.py
- Location: `src/powerbi_to_looker/transformer/views/builder.py`
- Change: Use `formula_ast` from canonical model (not parse again)
- Logic:
  ```python
  elif table_type == "calculated":
      formula_ast = t.get("formula_ast")
      formula_parse_error = t.get("formula_parse_error")
      
      if formula_parse_error:
          conversion_status = "manual"
          message = f"Formula parse error: {formula_parse_error}"
      elif formula_ast:
          # Build table resolution map
          table_res_map = {}
          for other_table in tables:
              if other_table.get("table_type") == "physical":
                  table_name = other_table.get("table_name") or other_table.get("name")
                  sql_name = _sql_table_name(database, schema, table_name)
                  table_res_map[table_name] = sql_name
                  table_res_map[f"'{table_name}'"] = sql_name
          
          # Convert AST to SQL
          result = convert_with_status(formula_ast, table_res_map)
          bq_sql = result.get("bq_formula")
          status = result.get("conversion_status", "auto")
          
          if bq_sql and status in ("auto", "partial"):
              # Remove outer parens if present (SUMMARIZE returns subquery)
              if bq_sql.startswith("(") and bq_sql.endswith(")"):
                  derived_table_sql = bq_sql[1:-1]
              else:
                  derived_table_sql = bq_sql
              conversion_status = status
              message = result.get("message")
          else:
              conversion_status = "manual"
              message = result.get("message") or "Conversion failed"
  ```

### Expected Output
For "Customer Exposure Summary" with formula:
```
SUMMARIZE('marketing_campaign_data', 'marketing_campaign_data'[CustomerID], 
          "Campaigns Exposed", DISTINCTCOUNT(...), ...)
```

Should generate:
```sql
SELECT 
  marketing_campaign_data.CustomerID,
  COUNT(DISTINCT marketing_campaign_data.CampaignID) AS `Campaigns Exposed`,
  SUM(marketing_campaign_data.Conversions) AS Conversions,
  SUM(marketing_campaign_data.Revenue) AS Revenue
FROM `tableau-to-looker-migration.Marketing_Campaign.marketing_campaign_data`
GROUP BY marketing_campaign_data.CustomerID
```

---

## Testing

### Test Cases

1. **Hidden Tables Filter**
   - ✅ DateTableTemplate not in generated views
   - ✅ LocalDateTable not in generated views
   - ✅ "Customer Exposure Summary" still present (not hidden)
   - ✅ No joins to hidden tables in model.lkml

2. **Derived Table SQL**
   - ✅ "Customer Exposure Summary" has `derived_table_sql` populated
   - ✅ Generated view.lkml has `derived_table` block
   - ✅ SQL is valid BigQuery syntax
   - ✅ Fields reference `${TABLE}` correctly (now TABLE = derived_table)

3. **Error Handling**
   - ✅ Tables with parse errors marked as manual
   - ✅ Tables with conversion failures marked as manual
   - ✅ Message explains why conversion failed

---

## Files to Modify

1. `src/powerbi_to_looker/models/canonical.py` - Add formula_ast fields
2. `src/powerbi_to_looker/parser_normalizer/semantic/tables.py` - Parse formulas
3. `src/powerbi_to_looker/transformer/views/builder.py` - Filter hidden, generate derived_table_sql
4. `src/powerbi_to_looker/transformer/explores/builder.py` - Filter hidden table joins

---

## Risks & Considerations

1. **Hidden table fields lost**: Fields referencing hidden tables won't be in any view. This is acceptable since they're system fields.

2. **Table resolution map**: Need to build map of physical table names → SQL table names for formula conversion.

3. **SUMMARIZE subquery format**: `_convert_summarize` returns subquery in parens `(SELECT ...)`. Need to strip parens for `derived_table_sql`.

4. **Backward compatibility**: Existing canonical models without `formula_ast` will still work (fields are Optional).

---

## Implementation Order

1. ✅ Create plan (this document)
2. ⏳ Implement Part 1: Filter hidden tables
3. ⏳ Test Part 1
4. ⏳ Implement Part 2: Add derived_table_sql
5. ⏳ Test Part 2
6. ⏳ Integration test with real data
