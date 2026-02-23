# Formula Converter v2 Replacement Plan

**Status:** Pending approval  
**Date:** 2024  
**Goal:** Replace current formula_converter.py with Claude v2 implementation

---

## Overview

Replace the current formula converter (v1, ~215 lines) with the more comprehensive Claude v2 version (~1114 lines) that includes:
- VAR/RETURN block support
- CALCULATE function (partial)
- SUMMARIZE conversion
- 15+ additional function handlers
- Better partial conversion tracking
- Performance improvements

---

## Files to Replace

### 1. Core Implementation
- **Source:** `claude/formula_converter.py`
- **Target:** `src/powerbi_to_looker/transformer/views/formula_converter.py`
- **Action:** Complete file replacement
- **Lines:** ~1114 lines

### 2. Configuration
- **Source:** `claude/function_mapping (1).yaml`
- **Target:** `src/powerbi_to_looker/config/function_mapping.yaml`
- **Action:** Complete file replacement
- **Lines:** ~539 lines

---

## Files to Update

### 3. Test File
- **File:** `tests/transformer/test_formula_converter.py`
- **Change:** Update `test_calculate_is_unsupported()` test
- **Reason:** CALCULATE is now partially supported in v2, not fully unsupported
- **Action:** Modify test to verify partial support instead of manual status

**Current test (lines 15-20):**
```python
def test_calculate_is_unsupported():
    ast = {"type": "FunctionCall", "name": "CALCULATE", "args": []}
    result = convert_with_status(ast)
    assert result["conversion_status"] == "manual"
    assert result["bq_formula"] is None
    assert "CALCULATE" in (result.get("message") or "")
```

**New test (after v2):**
```python
def test_calculate_is_partially_supported():
    # CALCULATE with no filters - should convert
    ast = {"type": "FunctionCall", "name": "CALCULATE", 
           "args": [{"type": "FunctionCall", "name": "SUM", 
                    "args": [{"type": "ColumnRef", "column": "Revenue"}]}]}
    result = convert_with_status(ast)
    assert result["conversion_status"] in ("auto", "partial")
    assert result["bq_formula"] is not None
    assert "SUM" in result["bq_formula"]
```

---

## Verification Steps

### 4. Run Tests
- **Command:** `pytest tests/transformer/test_formula_converter.py -v`
- **Expected:** All tests pass (after test update)

### 5. Run Integration Tests
- **Command:** `pytest tests/transformer/test_formula_converter_real.py -v`
- **Expected:** All tests pass

### 6. Check Imports
- **Files to check:**
  - `src/powerbi_to_looker/transformer/views/builder.py`
  - `scripts/show_formula_outputs.py`
  - `tests/transformer/test_formula_converter_real.py`
- **Expected:** All imports work (API is compatible)

---

## Architecture: SUMMARIZE Context Clarification

**Important:** SUMMARIZE appears in different contexts and is handled differently:

| Context | Handler | Output | Status |
|---------|---------|--------|--------|
| **Formula/Measure** | `formula_converter.py` | Subquery: `(SELECT ... GROUP BY ...)` | Partial |
| **VAR Block** | `formula_converter.py` | CTE: `WITH var AS (SELECT ... GROUP BY ...)` | Partial |
| **Table Definition** (calculated table) | `view/builder.py` | `derived_table_sql` in ArtifactView | **Not yet implemented** |

**Current State:**
- ✅ v2 formula_converter handles SUMMARIZE in formulas/VAR blocks
- ⚠️ Table-level SUMMARIZE (calculated tables) is not yet handled (see `builder.py` line 176: "Calculated table: derived_table_sql in a later pass")

**This replacement only affects formula/measure/VAR contexts, not table-level handling.**

---

## API Compatibility

✅ **Fully Compatible** - No breaking changes:
- `convert(ast, resolution_map, config)` → returns `str`
- `convert_with_status(ast, resolution_map)` → returns `dict`
- `clean_ref_name(name)` → returns `str`

---

## New Features in v2

1. **VAR/RETURN Support**
   - Inline scalar variables
   - CTE for chained variables
   - Manual flag for table functions
   - Special handling for SUMMARIZE in VAR blocks (converts to CTE)

2. **CALCULATE Handler** (partial)
   - Supports: no filters, ALL(table), ALLEXCEPT, FILTER conditions
   - Marks as partial when converted
   - Used in formulas/measures

3. **SUMMARIZE Handler** (partial) ⚠️ **Context-Specific**
   - **When used in formulas/measures:** Converts to GROUP BY subquery
   - **When used in VAR blocks:** Converts to CTE (WITH clause)
   - **When used at table level (calculated tables):** NOT handled here - should be in view builder → `derived_table_sql`
   - Marks as partial
   - **Architecture Note:** Table-level SUMMARIZE conversion is a separate concern (see `builder.py` line 176: "Calculated table: derived_table_sql in a later pass")

4. **Additional Node Types**
   - UnaryOp (-expr, NOT expr)
   - InExpr (col IN {...})
   - VarRef, VarExpr

5. **More Function Handlers**
   - SWITCH, COALESCE, SELECTEDVALUE
   - SUMX, AVERAGEX, MINX, MAXX, COUNTX, COUNTAX
   - COUNTBLANK, DISTINCTCOUNTNOBLANK
   - EOMONTH, DATEDIFF, DATEADD, WEEKDAY
   - FORMAT, TEXT, REPLACE, CONCATENATEX
   - IFERROR

6. **Performance**
   - Config caching with `@lru_cache`

---

## Risk Assessment

### Low Risk ✅
- API is fully compatible
- Existing code using formula_converter will work
- Tests can be updated incrementally

### Medium Risk ⚠️
- Test `test_calculate_is_unsupported()` needs update
- CALCULATE behavior changes (from manual to partial)
- More complex codebase (~5x larger)
- **SUMMARIZE context:** Handler in formula_converter is for formulas/VAR blocks only; table-level SUMMARIZE (calculated tables) needs separate handling in view builder (currently not implemented)

### Mitigation
- Run all tests before and after
- Keep claude/ directory as backup
- Review test failures carefully

---

## Implementation Steps

1. ✅ Create this plan document
2. ⏳ **Wait for approval**
3. ⏳ Backup current files (optional - git handles this)
4. ⏳ Replace `formula_converter.py`
5. ⏳ Replace `function_mapping.yaml`
6. ⏳ Update `test_calculate_is_unsupported()` test
7. ⏳ Run `pytest tests/transformer/test_formula_converter.py -v`
8. ⏳ Run `pytest tests/transformer/test_formula_converter_real.py -v`
9. ⏳ Verify imports in dependent files
10. ⏳ Document any breaking changes (none expected)

---

## Rollback Plan

If issues arise:
1. Revert commits via git
2. Or restore from `claude/` directory backup
3. Current v1 code is preserved in git history

---

## Approval

- [ ] Plan approved
- [ ] Ready to proceed with implementation

**Next Step:** Once approved, implementation will begin with file replacements.
