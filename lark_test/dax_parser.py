"""
dax_parser.py
=============
Load dax.lark and parse DAX expressions into a clean AST.

Dependencies: lark, pydantic (see pyproject.toml).

Usage:
    uv run python lark_test/dax_parser.py
    # or from lark_test: python dax_parser.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lark import Lark, Transformer
from pydantic import BaseModel


# ============================================================
# AST NODE DEFINITIONS (Pydantic)
# ============================================================

class Number(BaseModel):
    value: float


class String(BaseModel):
    value: str


class Boolean(BaseModel):
    value: bool


class Blank(BaseModel):
    pass


class ColumnRef(BaseModel):
    table: str | None = None  # None if unqualified
    column: str


class TableRef(BaseModel):
    name: str


class VarRef(BaseModel):
    name: str


class VarBinding(BaseModel):
    name: str
    expr: Any


class VarExpr(BaseModel):
    bindings: list[VarBinding]
    return_expr: Any


class FunctionCall(BaseModel):
    name: str
    args: list[Any]


class BinOp(BaseModel):
    op: str
    left: Any
    right: Any


class UnaryOp(BaseModel):
    op: str
    operand: Any


class InOp(BaseModel):
    expr: Any
    values: list[Any]
    negated: bool = False


class MultiColInOp(BaseModel):
    columns: list[ColumnRef]
    rows: list[list[Any]]
    negated: bool = False


class TableConstructor(BaseModel):
    rows: list[list[Any]]


class IntervalKeyword(BaseModel):
    unit: str  # YEAR, MONTH, DAY etc


class MeasureDef(BaseModel):
    name: str
    expr: Any


# ============================================================
# TRANSFORMER
# Maps grammar rules -> AST nodes above
# ============================================================

class DAXTransformer(Transformer):

    # --- Top level -------------------------------------------
    def start(self, items):
        return items[0]

    def measure_def(self, items):
        return MeasureDef(name=str(items[0]), expr=items[1])

    def measure_name(self, items):
        return str(items[0]).strip("'[]")

    # --- Expressions -----------------------------------------
    def expr(self, items):
        return items[0]

    def var_expr(self, items):
        bindings = [i for i in items if isinstance(i, VarBinding)]
        return_expr = items[-1]
        return VarExpr(bindings=bindings, return_expr=return_expr)

    def var_binding(self, items):
        return VarBinding(name=str(items[0]), expr=items[1])

    # Binary operators
    def or_op(self, items):      return BinOp(op="||", left=items[0], right=items[1])
    def and_op(self, items):     return BinOp(op="&&", left=items[0], right=items[1])
    def not_op(self, items):     return UnaryOp(op="NOT", operand=items[0])
    def eq(self, items):         return BinOp(op="=", left=items[0], right=items[1])
    def neq(self, items):        return BinOp(op="<>", left=items[0], right=items[1])
    def lt(self, items):         return BinOp(op="<", left=items[0], right=items[1])
    def gt(self, items):         return BinOp(op=">", left=items[0], right=items[1])
    def lte(self, items):        return BinOp(op="<=", left=items[0], right=items[1])
    def gte(self, items):        return BinOp(op=">=", left=items[0], right=items[1])
    def concat_op(self, items):  return BinOp(op="&", left=items[0], right=items[1])
    def add(self, items):        return BinOp(op="+", left=items[0], right=items[1])
    def sub(self, items):        return BinOp(op="-", left=items[0], right=items[1])
    def mul(self, items):        return BinOp(op="*", left=items[0], right=items[1])
    def div(self, items):        return BinOp(op="/", left=items[0], right=items[1])
    def power(self, items):      return BinOp(op="^", left=items[0], right=items[1])
    def neg(self, items):        return UnaryOp(op="-", operand=items[0])
    def pos(self, items):        return UnaryOp(op="+", operand=items[0])

    # Pass-through rules (single child, no AST node needed)
    def or_expr(self, items):    return items[0]
    def and_expr(self, items):   return items[0]
    def not_expr(self, items):   return items[0]
    def cmp_expr(self, items):   return items[0]
    def in_expr(self, items):    return items[0]
    def concat_expr(self, items):return items[0]
    def add_expr(self, items):   return items[0]
    def mul_expr(self, items):   return items[0]
    def unary_expr(self, items): return items[0]
    def power_expr(self, items): return items[0]
    def atom(self, items):       return items[0]
    def arg(self, items):        return items[0]

    # --- IN / NOT IN -----------------------------------------
    def in_op(self, items):
        return InOp(expr=items[0], values=items[1], negated=False)

    def not_in_op(self, items):
        return InOp(expr=items[0], values=items[1], negated=True)

    def set_expr(self, items):
        return items   # list of rows

    def tuple_row(self, items):
        return list(items)

    def scalar_row(self, items):
        return items[0]

    def multi_in_op(self, items):
        cols = [i for i in items if isinstance(i, ColumnRef)]
        rows = items[len(cols)]
        return MultiColInOp(columns=cols, rows=rows, negated=False)

    def multi_not_in_op(self, items):
        cols = [i for i in items if isinstance(i, ColumnRef)]
        rows = items[len(cols)]
        return MultiColInOp(columns=cols, rows=rows, negated=True)

    # --- References ------------------------------------------
    def qualified_col_ref(self, items):
        table = str(items[0]).strip("'")
        col   = str(items[1])
        return ColumnRef(table=table, column=col)

    def unqualified_col_ref(self, items):
        return ColumnRef(table=None, column=str(items[0]))

    def table_ref(self, items):
        return TableRef(name=str(items[0]).strip("'"))

    def table_name(self, items):
        return str(items[0])

    def var_ref(self, items):
        return VarRef(name=str(items[0]))

    # --- Functions -------------------------------------------
    def func_no_args(self, items):
        return FunctionCall(name=str(items[0]), args=[])

    def func_with_args(self, items):
        name = str(items[0])
        args = list(items[1:])
        return FunctionCall(name=name, args=args)

    def arg_list(self, items):
        return list(items)

    # --- Interval keywords -----------------------------------
    def interval_year(self, _):    return IntervalKeyword(unit="YEAR")
    def interval_quarter(self, _): return IntervalKeyword(unit="QUARTER")
    def interval_month(self, _):   return IntervalKeyword(unit="MONTH")
    def interval_week(self, _):    return IntervalKeyword(unit="WEEK")
    def interval_day(self, _):     return IntervalKeyword(unit="DAY")
    def interval_hour(self, _):    return IntervalKeyword(unit="HOUR")
    def interval_minute(self, _):  return IntervalKeyword(unit="MINUTE")
    def interval_second(self, _):  return IntervalKeyword(unit="SECOND")

    # --- Table constructor -----------------------------------
    def table_constructor(self, items):
        return TableConstructor(rows=list(items))

    def tc_tuple_row(self, items):
        return list(items)

    def tc_scalar_row(self, items):
        return [items[0]]

    # --- Literals --------------------------------------------
    def literal(self, items):
        return items[0]

    def number(self, items):
        return Number(value=float(items[0]))

    def string(self, items):
        raw = str(items[0])
        # strip surrounding quotes and unescape "" -> "
        return String(value=raw[1:-1].replace('""', '"'))

    def true_lit(self, _):
        return Boolean(value=True)

    def false_lit(self, _):
        return Boolean(value=False)

    def blank_lit(self, _):
        return Blank()


# ============================================================
# PARSER FACTORY
# ============================================================

_SCRIPT_DIR = Path(__file__).resolve().parent


def _resolve_grammar_path(grammar_path: str) -> Path:
    """Resolve grammar path relative to this script's directory; fallback to dax (1).lark if needed."""
    p = _SCRIPT_DIR / grammar_path
    if p.exists():
        return p
    if grammar_path == "dax.lark":
        fallback = _SCRIPT_DIR / "dax (1).lark"
        if fallback.exists():
            return fallback
    return p


def make_parser(grammar_path: str = "dax.lark") -> Lark:
    path = _resolve_grammar_path(grammar_path)
    grammar = path.read_text(encoding="utf-8")
    return Lark(
        grammar,
        parser="earley",
        ambiguity="resolve",
        propagate_positions=False,
    )


def parse(dax: str, grammar_path: str = "dax.lark") -> Any:
    parser = make_parser(grammar_path)
    tree = parser.parse(dax.strip())
    return DAXTransformer().transform(tree)


# ============================================================
# TESTS — covering every case in the grammar
# ============================================================

def run_tests():
    grammar_path = "dax.lark"  # resolved via _resolve_grammar_path (tries dax (1).lark if missing)

    test_cases = [
        # ---- Literals ----
        ("Integer",            "42"),
        ("Decimal",            "3.14"),
        ("Scientific",         "1.5E-10"),
        ("String",             '"hello"'),
        ("String escaped",     '"He said ""hello"""'),
        ("TRUE",               "TRUE"),
        ("FALSE",              "FALSE"),
        ("BLANK",              "BLANK()"),

        # ---- References ----
        ("Unqualified col",    "[Sales Amount]"),
        ("Qualified col",      "Sales[Amount]"),
        ("Quoted table col",   "'My Table'[My Column]"),
        ("Table ref",          "Sales"),
        ("Var ref",            "_myVar"),

        # ---- Arithmetic ----
        ("Add",                "[Sales] + [Cost]"),
        ("Sub",                "[Sales] - [Cost]"),
        ("Mul",                "[Qty] * [Price]"),
        ("Div",                "[Sales] / [Units]"),
        ("Precedence",         "[A] + [B] * [C]"),
        ("Parens",             "([A] + [B]) * [C]"),
        ("Unary neg",          "-[Sales]"),
        ("Power",              "[A] ^ 2"),

        # ---- String concat ----
        ("Concat",             '[First] & " " & [Last]'),

        # ---- Comparison ----
        ("Eq",                 "[Year] = 2024"),
        ("Neq",                "[Color] <> \"Red\""),
        ("Lt",                 "[Sales] < 1000"),
        ("Lte",                "[Sales] <= 1000"),
        ("Gt",                 "[Sales] > 0"),
        ("Gte",                "[Sales] >= 500"),

        # ---- Logical ----
        ("AND &&",             "[A] > 0 && [B] > 0"),
        ("OR ||",              "[A] > 0 || [B] > 0"),
        ("NOT",                "NOT [IsDeleted]"),
        ("AND keyword",        "[A] > 0 AND [B] > 0"),
        ("OR keyword",         "[A] > 0 OR [B] > 0"),

        # ---- IN / NOT IN ----
        ("IN scalar",          '[Color] IN {"Red", "Blue", "Green"}'),
        ("NOT IN",             '[Color] NOT IN {"Red"}'),

        # ---- Functions ----
        ("No args",            "TODAY()"),
        ("Single arg",         "SUM([Sales Amount])"),
        ("Multi arg",          "DIVIDE([Sales], [Units], 0)"),
        ("Nested",             "DIVIDE(SUM([Sales]), SUM([Units]))"),
        ("BLANK arg",          "IF(ISBLANK([Sales]), 0, [Sales])"),
        ("Dotted name",        "PERCENTILE.INC([Values], 0.9)"),
        ("T.INV.2T",           "T.INV.2T([P], [DF])"),

        # ---- IF / SWITCH ----
        ("IF",                 'IF([Sales] > 0, "Pos", "Zero")'),
        ("IFERROR",            "IFERROR([Sales] / [Units], 0)"),
        ("SWITCH TRUE",        'SWITCH(TRUE(), [Sales]>1000, "High", [Sales]>500, "Mid", "Low")'),

        # ---- CALCULATE ----
        ("CALCULATE basic",    "CALCULATE([Sales], Sales[Year] = 2024)"),
        ("CALCULATE multi",    "CALCULATE([Sales], ALL(Product), KEEPFILTERS(Product[Color]=\"Red\"))"),

        # ---- Iterators ----
        ("SUMX",               "SUMX(Sales, Sales[Qty] * Sales[Price])"),
        ("AVERAGEX",           "AVERAGEX(Customer, [LTV])"),
        ("RANKX",              "RANKX(ALL(Product), [Sales])"),
        ("MAXX nested",        "MAXX(FILTER(Sales, Sales[Year]=2024), Sales[Amount])"),

        # ---- Time intelligence ----
        ("DATEADD",            "DATEADD('Date'[Date], -1, YEAR)"),
        ("PARALLELPERIOD",     "PARALLELPERIOD('Date'[Date], -1, MONTH)"),
        ("TOTALYTD",           "TOTALYTD([Sales], 'Date'[Date])"),
        ("SAMEPERIODLASTYEAR", "SAMEPERIODLASTYEAR('Date'[Date])"),
        ("DATESBETWEEN",       "DATESBETWEEN('Date'[Date], [StartDate], [EndDate])"),

        # ---- VAR / RETURN ----
        ("VAR simple",
            """
            VAR TotalSales = SUM([Sales Amount])
            RETURN TotalSales
            """),

        ("VAR multi",
            """
            VAR Sales = SUM([Sales Amount])
            VAR Cost  = SUM([Cost Amount])
            RETURN Sales - Cost
            """),

        ("VAR nested inside SUMX",
            """
            SUMX(
                Sales,
                VAR LineTotal = Sales[Qty] * Sales[Price]
                RETURN LineTotal * 0.9
            )
            """),

        ("VAR with FILTER",
            """
            VAR FilteredSales = FILTER(Sales, Sales[Year] = 2024)
            VAR Total         = SUMX(FilteredSales, Sales[Amt])
            RETURN DIVIDE(Total, [Units], 0)
            """),

        # ---- Table constructor ----
        ("Table constructor scalar",       '{1, 2, 3}'),
        ("Table constructor tuples",       '{("Red", 1), ("Blue", 2)}'),

        # ---- Measure definition ----
        ("Measure def",        "Total Sales = SUM([Sales Amount])"),
        ("Measure def var",
            """
            Gross Margin =
            VAR Sales = [Total Sales]
            VAR Cost  = [Total Cost]
            RETURN DIVIDE(Sales - Cost, Sales)
            """),

        # ---- Comments ----
        ("Line comment //",
            """
            // This is a comment
            [Sales] + [Cost]
            """),

        ("Line comment --",
            """
            -- Calculate margin
            DIVIDE([Sales] - [Cost], [Sales])
            """),

        ("Block comment",
            """
            /* multi
               line
               comment */
            [Sales] * 1.1
            """),

        # ---- COUNT / COUNTA / COUNTROWS ----
        ("COUNT",              "COUNT(Sales[OrderID])"),
        ("COUNTA",             "COUNTA(Sales[Comments])"),
        ("COUNTROWS",          "COUNTROWS(Sales)"),
        ("COUNTX",             "COUNTX(Sales, Sales[OrderID])"),
        ("DISTINCTCOUNT",      "DISTINCTCOUNT(Sales[CustomerID])"),

        # ---- MAX / MIN ----
        ("MAX col",            "MAX(Sales[Amount])"),
        ("MIN col",            "MIN(Sales[Amount])"),
        ("MAX two args",       "MAX([Sales], [Budget])"),

        # ---- AVERAGE ----
        ("AVERAGE",            "AVERAGE(Sales[Amount])"),

        # ---- CONCATENATE / CONCATENATEX ----
        ("CONCATENATE",        'CONCATENATE([First], [Last])'),
        ("CONCATENATEX",       'CONCATENATEX(Sales, Sales[Name], ", ")'),

        # ---- CAST functions ----
        ("VALUE cast",         'VALUE("123")'),
        ("TEXT cast",          'TEXT([Amount], "0.00")'),
        ("FORMAT date",        'FORMAT([Date], "YYYY-MM-DD")'),
        ("DATE constructor",   "DATE(2024, 1, 15)"),
        ("INT cast",           "INT([Amount])"),

        # ---- COALESCE ----
        ("COALESCE",           "COALESCE([Sales], [Budget], 0)"),

        # ---- UPPER / LOWER ----
        ("UPPER",              "UPPER([ProductName])"),
        ("LOWER",              "LOWER([ProductName])"),

        # ---- ROUND ----
        ("ROUND",              "ROUND([Amount], 2)"),
        ("ROUNDUP",            "ROUNDUP([Amount], 2)"),
        ("ROUNDDOWN",          "ROUNDDOWN([Amount], 2)"),

        # ---- NULLIF pattern ----
        ("NULLIF via IF ISBLANK",  "IF(ISBLANK([Sales]), BLANK(), [Sales])"),
        ("NULLIF via comparison",  'IF([Status] = "Deleted", BLANK(), [Status])'),

        # ---- Text functions ----
        ("LEFT",               "LEFT([Name], 3)"),
        ("RIGHT",              "RIGHT([Name], 3)"),
        ("MID",                "MID([Name], 2, 5)"),
        ("LEN",                "LEN([Name])"),
        ("SUBSTITUTE",         'SUBSTITUTE([Name], "Old", "New")'),
        ("TRIM",               "TRIM([Name])"),

        # ---- Date functions (dual-role: also interval keywords) ----
        ("YEAR func",          "YEAR([Date])"),
        ("MONTH func",         "MONTH([Date])"),
        ("DAY func",           "DAY([Date])"),
        ("WEEKDAY",            "WEEKDAY([Date], 2)"),
        ("TODAY",              "TODAY()"),
        ("NOW",                "NOW()"),
        ("DATEDIFF DAY",       "DATEDIFF([Start], [End], DAY)"),
        ("DATEDIFF MONTH",     "DATEDIFF([Start], [End], MONTH)"),
        ("EOMONTH",            "EOMONTH([Date], 0)"),

        # ---- RELATED / RELATEDTABLE ----
        ("RELATED",            "RELATED('Product'[Category])"),
        ("RELATEDTABLE",       "RELATEDTABLE('Product')"),

        # ---- EARLIER ----
        ("EARLIER",            "FILTER(Sales, Sales[Amount] > EARLIER(Sales[Amount]))"),

        # ---- LOOKUPVALUE ----
        ("LOOKUPVALUE simple",
            "LOOKUPVALUE(Product[Price], Product[ID], Sales[ProductID])"),
        ("LOOKUPVALUE multi key",
            "LOOKUPVALUE(Product[Price], Product[ID], [ProdID], Product[Year], [Year])"),

        # ---- ALL variants ----
        ("ALL table",          "ALL(Sales)"),
        ("ALL column",         "ALL(Sales[Color])"),
        ("ALLEXCEPT",          "ALLEXCEPT(Sales, Sales[Year], Sales[Region])"),
        ("ALLSELECTED",        "ALLSELECTED(Sales[Color])"),

        # ---- CALCULATE modifiers ----
        ("KEEPFILTERS",
            'CALCULATE([Sales], KEEPFILTERS(Product[Color]="Red"))'),
        ("REMOVEFILTERS",
            "CALCULATE([Sales], REMOVEFILTERS('Date'))"),
        ("USERELATIONSHIP",
            "CALCULATE([Sales], USERELATIONSHIP(Sales[ShipDate], 'Date'[Date]))"),

        # ---- QTD / MTD ----
        ("TOTALQTD",           "TOTALQTD([Sales], 'Date'[Date])"),
        ("TOTALMTD",           "TOTALMTD([Sales], 'Date'[Date])"),
        ("DATESQTD",           "DATESQTD('Date'[Date])"),
        ("DATESMTD",           "DATESMTD('Date'[Date])"),
        ("DATESYTD",           "DATESYTD('Date'[Date])"),

        # ---- Moving average ----
        ("Moving average",
            """
            AVERAGEX(
                DATESINPERIOD('Date'[Date], MAX('Date'[Date]), -30, DAY),
                [Total Sales]
            )
            """),

        # ---- Cumulative total ----
        ("Cumulative total",
            """
            CALCULATE(
                [Total Sales],
                FILTER(
                    ALL('Date'[Date]),
                    'Date'[Date] <= MAX('Date'[Date])
                )
            )
            """),

        # ---- PERCENTILE ----
        ("PERCENTILE.INC",     "PERCENTILE.INC([Values], 0.9)"),
        ("PERCENTILE.EXC",     "PERCENTILE.EXC([Values], 0.1)"),

        # ---- Statistical ----
        ("MEDIAN",             "MEDIAN(Sales[Amount])"),
        ("MEDIANX",            "MEDIANX(Sales, Sales[Amount])"),
        ("STDEV.P",            "STDEV.P(Sales[Amount])"),

        # ---- Complex real-world example ----
        ("YTD with EARLIER",
            """
            VAR CurrentMonth = MAX('Date'[MonthNum])
            VAR YTD = CALCULATE(
                SUM([Sales Amount]),
                FILTER(
                    ALL('Date'),
                    'Date'[Year] = MAX('Date'[Year]) &&
                    'Date'[MonthNum] <= CurrentMonth
                )
            )
            RETURN YTD
            """),

        ("Running total",
            """
            CALCULATE(
                [Total Sales],
                FILTER(
                    ALL('Date'[Date]),
                    'Date'[Date] <= MAX('Date'[Date])
                )
            )
            """),

        ("Market share",
            """
            VAR CategorySales = [Total Sales]
            VAR AllSales = CALCULATE([Total Sales], ALL(Product))
            RETURN DIVIDE(CategorySales, AllSales, 0)
            """),
    ]

    parser = make_parser(grammar_path)
    transformer = DAXTransformer()

    passed = 0
    failed = 0
    errors = []

    print("=" * 60)
    print("DAX PARSER — TEST SUITE")
    print("=" * 60)

    for name, dax in test_cases:
        try:
            tree = parser.parse(dax.strip())
            ast  = transformer.transform(tree)

            if name == "Market share":
                print(ast)

            print(f"  OK   {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL {name}")
            print(f"       {e}")
            errors.append((name, str(e)))
            failed += 1

    print("=" * 60)
    print(f"  Passed: {passed}  |  Failed: {failed}")
    print("=" * 60)

    if errors:
        print("\nFailed cases:")
        for name, err in errors:
            print(f"\n  [{name}]\n  {err}")

    return failed == 0


# ============================================================
# DEMO — pretty print an AST
# ============================================================

def demo():
    dax = """
    VAR Sales  = SUM([Sales Amount])
    VAR Costs  = SUM([Cost Amount])
    VAR Margin = DIVIDE(Sales - Costs, Sales, 0)
    RETURN
        IF(Margin > 0.3, "Good", "Review")
    """

    print("\n" + "=" * 60)
    print("DEMO — Parse + AST")
    print("=" * 60)
    print("Input:")
    print(dax)

    result = parse(dax)
    print("AST:")
    print(result)


if __name__ == "__main__":
    all_passed = run_tests()
    demo()
