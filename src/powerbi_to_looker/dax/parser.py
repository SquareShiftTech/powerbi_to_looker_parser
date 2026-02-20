"""DAX parser: load dax.lark and parse DAX expressions into a clean AST.

Used by calc_field to attach formula_ast or formula_parse_error to canonical Field.
Grammar lives next to this module (dax.lark).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from lark import Lark, Transformer
from pydantic import BaseModel

_PACKAGE_DIR = Path(__file__).resolve().parent


# ============================================================
# AST NODE DEFINITIONS (Pydantic)
# ============================================================

class Number(BaseModel):
    type: Literal["Number"] = "Number"
    value: float


class String(BaseModel):
    type: Literal["String"] = "String"
    value: str


class Boolean(BaseModel):
    type: Literal["Boolean"] = "Boolean"
    value: bool


class Blank(BaseModel):
    type: Literal["Blank"] = "Blank"


class ColumnRef(BaseModel):
    type: Literal["ColumnRef"] = "ColumnRef"
    table: str | None = None
    column: str
    hierarchy_level: str | None = None  # e.g. [Date].[Date] -> level "Date"


class TableRef(BaseModel):
    type: Literal["TableRef"] = "TableRef"
    name: str


class VarRef(BaseModel):
    type: Literal["VarRef"] = "VarRef"
    name: str


class VarBinding(BaseModel):
    type: Literal["VarBinding"] = "VarBinding"
    name: str
    expr: Any


class VarExpr(BaseModel):
    type: Literal["VarExpr"] = "VarExpr"
    bindings: list[VarBinding]
    return_expr: Any


class FunctionCall(BaseModel):
    type: Literal["FunctionCall"] = "FunctionCall"
    name: str
    args: list[Any]


class BinOp(BaseModel):
    type: Literal["BinOp"] = "BinOp"
    op: str
    left: Any
    right: Any


class UnaryOp(BaseModel):
    type: Literal["UnaryOp"] = "UnaryOp"
    op: str
    operand: Any


class InOp(BaseModel):
    type: Literal["InOp"] = "InOp"
    expr: Any
    values: list[Any]
    negated: bool = False


class MultiColInOp(BaseModel):
    type: Literal["MultiColInOp"] = "MultiColInOp"
    columns: list[ColumnRef]
    rows: list[list[Any]]
    negated: bool = False


class TableConstructor(BaseModel):
    type: Literal["TableConstructor"] = "TableConstructor"
    rows: list[list[Any]]


class IntervalKeyword(BaseModel):
    type: Literal["IntervalKeyword"] = "IntervalKeyword"
    unit: str


class MeasureDef(BaseModel):
    type: Literal["MeasureDef"] = "MeasureDef"
    name: str
    expr: Any


# ============================================================
# TRANSFORMER
# ============================================================

class DAXTransformer(Transformer):

    def start(self, items):
        return items[0]

    def measure_def(self, items):
        return MeasureDef(name=str(items[0]), expr=items[1])

    def measure_name(self, items):
        return str(items[0]).strip("'[]")

    def expr(self, items):
        return items[0]

    def var_expr(self, items):
        bindings = [i for i in items if isinstance(i, VarBinding)]
        return_expr = items[-1]
        return VarExpr(bindings=bindings, return_expr=return_expr)

    def var_binding(self, items):
        return VarBinding(name=str(items[0]), expr=items[1])

    def or_op(self, items):      return BinOp(op="||", left=items[0], right=items[1])
    def and_op(self, items):     return BinOp(op="&&", left=items[0], right=items[1])
    def not_op(self, items):     return UnaryOp(op="NOT", operand=items[0])
    def eq(self, items):         return BinOp(op="=", left=items[0], right=items[1])
    def neq(self, items):       return BinOp(op="<>", left=items[0], right=items[1])
    def lt(self, items):        return BinOp(op="<", left=items[0], right=items[1])
    def gt(self, items):        return BinOp(op=">", left=items[0], right=items[1])
    def lte(self, items):       return BinOp(op="<=", left=items[0], right=items[1])
    def gte(self, items):       return BinOp(op=">=", left=items[0], right=items[1])
    def concat_op(self, items): return BinOp(op="&", left=items[0], right=items[1])
    def add(self, items):       return BinOp(op="+", left=items[0], right=items[1])
    def sub(self, items):       return BinOp(op="-", left=items[0], right=items[1])
    def mul(self, items):       return BinOp(op="*", left=items[0], right=items[1])
    def div(self, items):       return BinOp(op="/", left=items[0], right=items[1])
    def power(self, items):     return BinOp(op="^", left=items[0], right=items[1])
    def neg(self, items):       return UnaryOp(op="-", operand=items[0])
    def pos(self, items):       return UnaryOp(op="+", operand=items[0])

    def or_expr(self, items):    return items[0]
    def and_expr(self, items):   return items[0]
    def not_expr(self, items):   return items[0]
    def cmp_expr(self, items):   return items[0]
    def in_expr(self, items):    return items[0]
    def concat_expr(self, items): return items[0]
    def add_expr(self, items):   return items[0]
    def mul_expr(self, items):   return items[0]
    def unary_expr(self, items): return items[0]
    def power_expr(self, items): return items[0]
    def atom(self, items):       return items[0]
    def arg(self, items):        return items[0]

    def in_op(self, items):
        return InOp(expr=items[0], values=items[1], negated=False)

    def not_in_op(self, items):
        return InOp(expr=items[0], values=items[1], negated=True)

    def set_expr(self, items):
        return items

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

    def hierarchy_suffix(self, items):
        """Return the hierarchy level name (COL_NAME after .[ ). Lark omits literals, so items = [COL_NAME]."""
        return str(items[0])

    def qualified_col_ref(self, items):
        # Lark omits "[" and "]" from tree; children are table_name, COL_NAME [, hierarchy_suffix]
        table = str(items[0]).strip("'")
        col = str(items[1])
        level = items[2] if len(items) > 2 else None
        level = str(level) if level is not None else None
        return ColumnRef(table=table, column=col, hierarchy_level=level)

    def unqualified_col_ref(self, items):
        # Children are COL_NAME [, hierarchy_suffix]
        col = str(items[0])
        level = items[1] if len(items) > 1 else None
        level = str(level) if level is not None else None
        return ColumnRef(table=None, column=col, hierarchy_level=level)

    def table_ref(self, items):
        return TableRef(name=str(items[0]).strip("'"))

    def table_name(self, items):
        return str(items[0])

    def var_ref(self, items):
        return VarRef(name=str(items[0]))

    def func_name(self, items):
        return str(items[0])

    def func_no_args(self, items):
        return FunctionCall(name=str(items[0]).upper(), args=[])

    def func_with_args(self, items):
        name = str(items[0]).upper()
        # Lark omits "(" and ")"; children are [func_name, arg_list]. arg_list returns a list.
        raw = items[1] if len(items) > 1 else None
        if raw is None:
            args = []
        elif isinstance(raw, list):
            args = raw
        else:
            args = [raw]
        return FunctionCall(name=name, args=args)

    def arg_list(self, items):
        return list(items)

    def interval_year(self, _):    return IntervalKeyword(unit="YEAR")
    def interval_quarter(self, _): return IntervalKeyword(unit="QUARTER")
    def interval_month(self, _):   return IntervalKeyword(unit="MONTH")
    def interval_week(self, _):    return IntervalKeyword(unit="WEEK")
    def interval_day(self, _):     return IntervalKeyword(unit="DAY")
    def interval_hour(self, _):    return IntervalKeyword(unit="HOUR")
    def interval_minute(self, _):  return IntervalKeyword(unit="MINUTE")
    def interval_second(self, _):  return IntervalKeyword(unit="SECOND")

    def table_constructor(self, items):
        return TableConstructor(rows=list(items))

    def tc_tuple_row(self, items):
        return list(items)

    def tc_scalar_row(self, items):
        return [items[0]]

    def literal(self, items):
        return items[0]

    def number(self, items):
        return Number(value=float(items[0]))

    def string(self, items):
        raw = str(items[0])
        return String(value=raw[1:-1].replace('""', '"'))

    def true_lit(self, _):
        return Boolean(value=True)

    def false_lit(self, _):
        return Boolean(value=False)

    def blank_lit(self, _):
        return Blank()


# ============================================================
# PARSER FACTORY & PARSE
# ============================================================

def _get_grammar_path() -> Path:
    p = _PACKAGE_DIR / "dax.lark"
    if not p.exists():
        raise FileNotFoundError(f"Grammar not found: {p}")
    return p


def make_parser(grammar_path: Path | None = None) -> Lark:
    path = grammar_path or _get_grammar_path()
    grammar = path.read_text(encoding="utf-8")
    return Lark(
        grammar,
        parser="earley",
        ambiguity="resolve",
        propagate_positions=False,
    )


def parse(dax: str, grammar_path: Path | None = None) -> Any:
    """Parse DAX string into an AST (Pydantic nodes). Raises on parse error."""
    parser = make_parser(grammar_path)
    tree = parser.parse(dax.strip())
    return DAXTransformer().transform(tree)


def _ast_to_dict(ast: Any) -> dict[str, Any]:
    """Convert AST (Pydantic or nested structure) to JSON-serializable dict."""
    if hasattr(ast, "model_dump"):
        return ast.model_dump()
    if isinstance(ast, list):
        return {"_list": [_ast_to_dict(x) for x in ast]}
    if isinstance(ast, dict):
        return {k: _ast_to_dict(v) for k, v in ast.items()}
    return ast


def parse_formula(formula: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse a DAX formula. Safe: never raises.

    Returns:
        (ast_dict, error_message). On success: (ast_dict, None). On failure: (None, short error string).
        Empty/whitespace formula -> (None, None).
    """
    if not formula or not formula.strip():
        return (None, None)
    try:
        ast = parse(formula.strip())
        # AST root is always a Pydantic model from our grammar
        if hasattr(ast, "model_dump"):
            return (ast.model_dump(), None)
        # Fallback for any non-model root (e.g. raw list)
        return (_ast_to_dict(ast), None)
    except Exception as e:
        msg = str(e).strip()
        if "\n" in msg:
            msg = msg.split("\n")[0]
        if len(msg) > 200:
            msg = msg[:197] + "..."
        return (None, msg or "Parse error")
