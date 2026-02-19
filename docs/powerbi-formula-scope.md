---

## Formula Categories Required

### **1. Aggregation Functions**
Return aggregated values from tables.
- `SUM()`, `AVERAGE()`, `COUNT()`, `COUNTA()`, `COUNTROWS()`
- `MIN()`, `MAX()`, `DISTINCTCOUNT()`

**Examples needed:** 2-3 formulas

---

### **2. Iterator Functions** 
Perform row-by-row calculations over tables.
- `SUMX()`, `AVERAGEX()`, `COUNTX()`
- `MINX()`, `MAXX()`, `RANKX()`

**Examples needed:** 2-3 formulas

---

### **3. Filter Functions**
Modify filter context or filter tables.
- `FILTER()`, `ALL()`, `ALLEXCEPT()`, `ALLSELECTED()`
- `CALCULATE()`, `CALCULATETABLE()`
- `VALUES()`, `DISTINCT()`, `KEEPFILTERS()`

**Examples needed:** 3-4 formulas

---

### **4. Date and Time Functions**
Work with dates and extract date parts.
- `YEAR()`, `MONTH()`, `DAY()`, `DATE()`
- `TODAY()`, `NOW()`, `DATEDIFF()`, `EOMONTH()`

**Examples needed:** 2-3 formulas

---

### **5. Time Intelligence Functions**
Calculate over time periods.
- `DATESYTD()`, `DATESMTD()`, `DATESQTD()`
- `SAMEPERIODLASTYEAR()`, `PREVIOUSYEAR()`, `NEXTYEAR()`
- `DATEADD()`, `PARALLELPERIOD()`, `DATESBETWEEN()`
- `TOTALYTD()`, `TOTALMTD()`, `TOTALQTD()`

**Examples needed:** 3-4 formulas

---

### **6. Logical Functions**
Conditional logic and boolean operations.
- `IF()`, `IFERROR()`, `SWITCH()`
- `AND()`, `OR()`, `NOT()`, `TRUE()`, `FALSE()`

**Examples needed:** 2-3 formulas

---

### **7. Text Functions**
String manipulation and formatting.
- `CONCATENATE()`, `COMBINEVALUES()`, `UPPER()`, `LOWER()`
- `LEFT()`, `RIGHT()`, `MID()`, `LEN()`
- `SEARCH()`, `FIND()`, `SUBSTITUTE()`, `REPLACE()`
- `FORMAT()`, `TRIM()`

**Examples needed:** 2-3 formulas

---

### **8. Mathematical Functions**
Numeric calculations and transformations.
- `ROUND()`, `ROUNDUP()`, `ROUNDDOWN()`, `TRUNC()`
- `ABS()`, `POWER()`, `SQRT()`, `EXP()`, `LN()`, `LOG()`
- `MOD()`, `QUOTIENT()`, `DIVIDE()`
- `CEILING()`, `FLOOR()`, `INT()`

**Examples needed:** 2-3 formulas

---

### **9. Statistical Functions**
Statistical analysis and distributions.
- `STDEV.P()`, `STDEV.S()`, `VAR.P()`, `VAR.S()`
- `MEDIAN()`, `PERCENTILE.INC()`, `PERCENTILE.EXC()`
- `RANKX()`, `TOPN()`

**Examples needed:** 2-3 formulas

---

### **10. Information Functions**
Test data types and states.
- `ISBLANK()`, `ISERROR()`, `ISLOGICAL()`
- `ISNUMBER()`, `ISTEXT()`
- `HASONEVALUE()`, `HASONEFILTER()`, `ISFILTERED()`
- `SELECTEDVALUE()`, `USERNAME()`, `USERPRINCIPALNAME()`

**Examples needed:** 2-3 formulas

---

### **11. Relationship Functions**
Navigate relationships between tables.
- `RELATED()`, `RELATEDTABLE()`
- `USERELATIONSHIP()`, `CROSSFILTER()`
- `TREATAS()`

**Examples needed:** 2-3 formulas

---

### **12. Table Manipulation Functions**
Create or modify tables.
- `SUMMARIZE()`, `SUMMARIZECOLUMNS()`, `ADDCOLUMNS()`, `SELECTCOLUMNS()`
- `GROUPBY()`, `ROW()`
- `UNION()`, `INTERSECT()`, `EXCEPT()`, `CROSSJOIN()`, `NATURALINNERJOIN()`, `NATURALLEFTOUTERJOIN()`
- `TOPN()`, `SAMPLE()`
- `GENERATESERIES()`, `CALENDAR()`, `CALENDARAUTO()`, `DATATABLE()`

**Examples needed:** 3-4 formulas

---

### **13. Parent-Child (Hierarchy) Functions**
Work with hierarchical data.
- `PATH()`, `PATHITEM()`, `PATHLENGTH()`
- `PATHCONTAINS()`, `PATHITEMREVERSE()`

**Examples needed:** 1-2 formulas (if used)

---

### **14. Financial Functions**
Financial calculations (Excel-like).
- `PMT()`, `PPMT()`, `IPMT()`
- `PV()`, `FV()`, `RATE()`, `NPER()`

**Examples needed:** 1-2 formulas (if used)

---

### **15. Variables (VAR/RETURN)**
Store intermediate calculations.
```dax
VAR VariableName = Expression
VAR AnotherVariable = Expression
RETURN FinalExpression
```

**Examples needed:** 3-4 formulas with variables

---

### **16. Operators**
Mathematical, comparison, and logical operators.
- **Arithmetic:** `+`, `-`, `*`, `/`
- **Comparison:** `=`, `<>`, `>`, `<`, `>=`, `<=`
- **Logical:** `&&` (AND), `||` (OR)
- **Other:** `IN`, `&` (text concatenation)

**Examples needed:** Included in other formulas

---

## Complex Formula Combinations

### **17. Complex Formulas - Level 1 (Medium)**
Combinations of 2-3 different function types.

**Examples:**
- Aggregation + Filter: `CALCULATE(SUM([Sales]), FILTER(...))`
- Time Intelligence + Aggregation: `TOTALYTD(SUM([Sales]), [Date])`
- Conditional + Aggregation: `IF(SUM([Sales]) > 1000, "High", "Low")`
- Iterator + Filter: `SUMX(FILTER(...), [Amount])`
- Variable + Aggregation: `VAR Total = SUM([Sales]) RETURN Total * 0.1`

**Examples needed:** 5-6 formulas

---

### **18. Complex Formulas - Level 2 (Advanced)**
Combinations of 4-6 different function types with nesting.

**Examples:**
- Variable + Calculate + Filter + Time Intelligence:
  ```dax
  VAR CurrentSales = CALCULATE(SUM([Sales]), DATESYTD([Date]))
  VAR PriorSales = CALCULATE(SUM([Sales]), DATESYTD(DATEADD([Date], -1, YEAR)))
  RETURN DIVIDE(CurrentSales - PriorSales, PriorSales, 0)
  ```
- Multiple Iterators + Filters + Conditionals
- Table Functions + Aggregations + Relationships
- Nested CALCULATE with multiple filters

**Examples needed:** 5-6 formulas

---

### **19. Complex Formulas - Level 3 (Expert)**
Highly complex combinations with deep nesting (5+ levels).

**Examples:**
- Multiple Variables + Multiple CALCULATE + Iterator + Time Intelligence + Conditionals
- Advanced table manipulation with SUMMARIZE + ADDCOLUMNS + FILTER + aggregations
- Complex ranking/statistical formulas with context transitions
- Multi-level nested IF or SWITCH with calculations
- Multiple relationship navigations with filters

**Examples needed:** 3-4 formulas

---

## Special Cases

### **20. Formulas with Comments**
```dax
// This is a single line comment
VAR Sales = SUM([Sales]) /* inline comment */
/* 
Multi-line comment
explaining complex logic
*/
RETURN Sales * 1.1
```

**Examples needed:** 2-3 formulas

---

### **21. Formulas with Special Characters**
- Table names with spaces: `'Sales Data'[Amount]`
- Column names with spaces: `[Sales Amount]`
- Special characters in names: `'Sales-2024'[Value]`

**Examples needed:** 2-3 formulas

---

### **22. Measure vs Calculated Column Formulas**
- **Measures:** Calculated at query time, use aggregations
- **Calculated Columns:** Calculated row-by-row at refresh time

**Examples needed:** 2-3 of each type

---

## Sample Collection Requirements

### For Each Formula Example, Provide:

1. **Formula Name:** The name of the measure/column
2. **Formula Type:** Which category(ies) it belongs to
3. **Complete DAX Code:** Full formula as written in PowerBI
4. **Context:** Measure or Calculated Column?
5. **Business Purpose:** What business question does it answer?
6. **Tables/Columns Used:** List of data model elements referenced
7. **Complexity Level:** Simple, Medium, Advanced, or Expert

---

## Prioritization

### **High Priority** (Must Have)
- Categories 1-6: Aggregation, Iterator, Filter, Date/Time, Time Intelligence, Logical
- Complex Formulas Level 1 & 2
- Variables

### **Medium Priority** (Should Have)
- Categories 7-12: Text, Math, Statistical, Information, Relationship, Table Manipulation
- Complex Formulas Level 3

### **Low Priority** (Nice to Have)
- Categories 13-14: Hierarchy, Financial
- Special cases

---

## Total Sample Count

| Category | Samples Needed |
|----------|----------------|
| Simple Functions (1-14) | 30-40 formulas |
| Variables | 3-4 formulas |
| Complex Level 1 | 5-6 formulas |
| Complex Level 2 | 5-6 formulas |
| Complex Level 3 | 3-4 formulas |
| Special Cases | 4-6 formulas |
| **TOTAL** | **50-70 formulas** |

---

## Delivery Format

Please provide samples in a spreadsheet with columns:
- Formula Name
- Category
- DAX Code
- Measure/Column
- Business Purpose
- Tables Used
- Complexity Level

---

## Questions?

Contact: [Your Name/Team]
[8:54 AM]Please see if it covers all