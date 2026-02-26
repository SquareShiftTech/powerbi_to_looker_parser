"""Convert DAX formula AST to BigQuery SQL. Uses resolution_map for unqualified column refs.

Conversion status levels:
    auto    -> fully converted, result is correct BQ SQL
    partial -> converted but approximation — reviewer should verify
    manual  -> cannot convert, human must rewrite

Node types handled:
    FunctionCall / func   -> _convert_function (yaml lookup + _HANDLERS)
    ColumnRef             -> _convert_column_ref
    TableRef              -> _convert_table_ref
    BinOp                 -> _convert_binop
    UnaryOp               -> _convert_unaryop
    Number/String/Boolean -> _convert_literal
    Blank                 -> NULL
    VarExpr               -> _convert_var_expr (VAR/RETURN blocks)
    VarRef                -> resolved via res_map
    InExpr                -> _convert_in_expr (col IN {v1, v2, ...})
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "function_mapping.yaml"

# ============================================================
# CONVERSION RESULT
# Wraps SQL + status so handlers can signal partial
# ============================================================

class ConversionResult:
    """Carries SQL + status from a handler that may be partial."""
    __slots__ = ("sql", "status", "message")

    def __init__(
        self,
        sql: str,
        status: str = "auto",
        message: str | None = None,
    ) -> None:
        self.sql = sql
        self.status = status          # "auto" | "partial" | "manual"
        self.message = message


# ============================================================
# CONFIG — cached at module level
# ============================================================

@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    try:
        return load_yaml(_CONFIG_PATH)
    except FileNotFoundError:
        return {}


def _get_config() -> dict[str, Any]:
    return _load_config()


def _unsupported_map(config: dict[str, Any]) -> dict[str, str]:
    """Return {FUNC_NAME: message} for all unsupported entries."""
    out: dict[str, str] = {}
    for item in config.get("unsupported") or []:
        if isinstance(item, dict):
            n = (item.get("name") or "").upper()
            m = item.get("message") or "Unsupported function"
            out[n] = m
    return out


# ============================================================
# NODE TYPE NORMALISATION
# ============================================================

def _normalize_node_type(ast: dict[str, Any]) -> str:
    """Map raw AST type string to canonical internal type."""
    t = (ast.get("type") or "").strip() if isinstance(ast.get("type"), str) else ""
    if t in ("FunctionCall", "func"):
        return "func"
    if t in ("ColumnRef", "column_ref"):
        return "column_ref"
    if t in ("TableRef", "table_ref"):
        return "table_ref"
    if t in ("BinOp", "binop"):
        return "binop"
    if t in ("UnaryOp", "unaryop"):
        return "unaryop"
    if t in ("Number", "String", "Boolean", "literal"):
        return "literal"
    if t in ("Blank", "blank"):
        return "blank"
    if t in ("VarExpr", "var_expr"):
        return "var_expr"
    if t in ("VarRef", "var_ref"):
        return "var_ref"
    if t in ("InExpr", "in_expr"):
        return "in_expr"
    # IntervalKeyword — treated as literal for _extract_interval
    if t in ("IntervalKeyword", "interval_keyword"):
        return "interval"
    return "func"   # safe default — will raise "Unknown function" if name missing


# ============================================================
# LEAF NODE CONVERTERS
# ============================================================

def _convert_table_ref(ast: dict[str, Any], res_map: dict[str, str] | None = None) -> str:
    """Convert table reference. Uses resolution map if provided (for table-level formulas)."""
    name = (ast.get("name") or "").strip()
    if not name:
        return ""
    
    # Check resolution map first (for table-level formulas)
    if res_map:
        resolved = res_map.get(name) or res_map.get(f"'{name}'")
        if resolved:
            return resolved
    
    # Fallback to cleaned name
    return clean_ref_name(name)


def _convert_column_ref(ast: dict[str, Any], res_map: dict[str, str]) -> str:
    """Unqualified [Col] -> ${field_name}  |  Table[Col] -> table.col"""
    table = ast.get("table")
    col = str(ast.get("column") or "").strip()
    if not table:
        resolved = res_map.get(col) or res_map.get(col.upper()) or clean_ref_name(col)
        return f"${{{resolved}}}"
    tbl = clean_ref_name(str(table))
    return f"{tbl}.{clean_ref_name(col)}"


def _convert_literal(ast: dict[str, Any]) -> str:
    if ast.get("type") in ("Blank", "blank"):
        return "NULL"
    v = ast.get("value")
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    return "NULL"


def _convert_var_ref(ast: dict[str, Any], res_map: dict[str, str]) -> str:
    """VarRef resolves against res_map populated by _convert_var_expr."""
    name = (ast.get("name") or "").strip()
    resolved = res_map.get(name) or res_map.get(name.upper())
    if resolved:
        return resolved
    # Not in res_map — VAR used outside its scope or not yet resolved
    return clean_ref_name(name)


def _convert_unaryop(
    ast: dict[str, Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
    convert_fn: Any,
) -> str:
    """Handle unary minus: -expr -> (-expr)"""
    op = (ast.get("op") or "").strip()
    operand = ast.get("operand") or ast.get("expr") or ast.get("right")
    operand_sql = convert_fn(operand, res_map, cfg) if operand else "NULL"
    if op == "-":
        return f"(-{operand_sql})"
    if op in ("NOT", "not", "!"):
        return f"(NOT {operand_sql})"
    return f"({op}{operand_sql})"


def _convert_in_expr(
    ast: dict[str, Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
    convert_fn: Any,
) -> str:
    """Handle col IN {v1, v2} and col NOT IN {v1, v2}"""
    col_node = ast.get("expr") or ast.get("column")
    values = ast.get("values") or ast.get("args") or []
    negated = ast.get("negated") or ast.get("not") or False

    col_sql = convert_fn(col_node, res_map, cfg) if col_node else "NULL"
    val_sqls = [convert_fn(v, res_map, cfg) for v in values]
    vals_str = ", ".join(val_sqls)

    op = "NOT IN" if negated else "IN"
    return f"({col_sql} {op} ({vals_str}))"


# ============================================================
# BINOP
# ============================================================

def _convert_binop(
    ast: dict[str, Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
    convert_fn: Any,
) -> str:
    op_map = cfg.get("operator_mapping") or {}
    op = (ast.get("op") or "").strip()
    left = convert_fn(ast.get("left"), res_map, cfg)
    right = convert_fn(ast.get("right"), res_map, cfg)
    bq_op = op_map.get(op) or op
    if bq_op == "POW":
        return f"POW({left}, {right})"
    return f"({left} {bq_op} {right})"


# ============================================================
# DIRECT TEMPLATE SUBSTITUTION
# ============================================================

def _apply_direct_template(
    template: str,
    args: list[Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
    convert_fn: Any,
) -> str:
    parts = [convert_fn(a, res_map, cfg) for a in args]
    out = template
    for i, p in enumerate(parts):
        out = out.replace("{" + str(i) + "}", p)
    out = re.sub(r"\{\d+\}", "NULL", out)
    return out


# ============================================================
# VAR / RETURN
# ============================================================

# Table-producing functions that make a VAR un-inlinable as scalar SQL
_TABLE_FUNCS = frozenset({
    "SUMMARIZE", "SUMMARIZECOLUMNS", "FILTER", "ADDCOLUMNS",
    "SELECTCOLUMNS", "CROSSJOIN", "UNION", "INTERSECT", "EXCEPT",
    "TOPN", "VALUES", "DISTINCT", "GENERATE", "GENERATEALL",
    "NATURALLEFTOUTERJOIN", "NATURALINNERJOIN",
})


def _expr_contains_table_func(node: Any) -> str | None:
    """Return first table-func name found in node tree, or None."""
    if not isinstance(node, dict):
        return None
    name = (node.get("name") or "").upper()
    if name in _TABLE_FUNCS:
        return name
    for v in node.values():
        if isinstance(v, dict):
            found = _expr_contains_table_func(v)
            if found:
                return found
        elif isinstance(v, list):
            for item in v:
                found = _expr_contains_table_func(item)
                if found:
                    return found
    return None


def _expr_references_var(node: Any, var_names: frozenset[str]) -> bool:
    """Return True if node tree contains a VarRef whose name is in var_names."""
    if not isinstance(node, dict):
        return False
    t = (node.get("type") or "").strip()
    if t in ("VarRef", "var_ref"):
        if (node.get("name") or "").upper() in var_names:
            return True
    for v in node.values():
        if isinstance(v, dict) and _expr_references_var(v, var_names):
            return True
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and _expr_references_var(item, var_names):
                    return True
    return False


def _convert_var_expr(
    ast: dict[str, Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
) -> ConversionResult:
    """Convert VAR/RETURN block.

    Cases:
        1. Any binding uses a table function -> manual
        2. Any binding references another VAR -> CTE (WITH clause), partial
        3. All bindings are pure scalars -> inline into RETURN expr, auto
    """
    bindings = ast.get("bindings") or []
    return_expr = ast.get("return_expr")

    if not bindings:
        # No VAR — just a RETURN expression
        try:
            sql = _convert_node(return_expr, res_map, cfg)
            return ConversionResult(sql, "auto")
        except ValueError as e:
            return ConversionResult("", "manual", str(e))

    var_names = frozenset(
        (b.get("name") or "").upper() for b in bindings
    )

    # Case 1 — any binding produces a table -> manual
    for b in bindings:
        table_func = _expr_contains_table_func(b.get("expr") or {})
        if table_func:
            # Special case: SUMMARIZE can be attempted as partial
            if table_func == "SUMMARIZE":
                return _convert_var_with_summarize(bindings, return_expr, res_map, cfg)
            return ConversionResult(
                "",
                "manual",
                f"VAR {b.get('name')} uses {table_func} which produces a virtual table "
                f"— rewrite as Looker derived table or BigQuery subquery.",
            )

    # Case 2 — chained VARs -> CTE
    needs_cte = any(
        _expr_references_var(b.get("expr") or {}, var_names)
        for b in bindings
    )

    if needs_cte:
        return _convert_var_as_cte(bindings, return_expr, var_names, res_map, cfg)

    # Case 3 — all scalar, inline
    return _convert_var_inline(bindings, return_expr, res_map, cfg)


def _convert_var_inline(
    bindings: list[dict],
    return_expr: Any,
    res_map: dict[str, str],
    cfg: dict[str, Any],
) -> ConversionResult:
    """Inline each VAR value directly into RETURN expression."""
    extended = dict(res_map)
    for b in bindings:
        name = b.get("name") or ""
        sql = _convert_node(b.get("expr"), extended, cfg)
        extended[name] = sql
        extended[name.upper()] = sql
    sql = _convert_node(return_expr, extended, cfg)
    return ConversionResult(sql, "auto")


def _convert_var_as_cte(
    bindings: list[dict],
    return_expr: Any,
    var_names: frozenset[str],
    res_map: dict[str, str],
    cfg: dict[str, Any],
) -> ConversionResult:
    """Emit WITH clause for chained VAR bindings."""
    cte_parts = []
    extended = dict(res_map)
    for b in bindings:
        name = b.get("name") or ""
        sql = _convert_node(b.get("expr"), extended, cfg)
        cte_parts.append(f"{name} AS (SELECT {sql} AS value)")
        extended[name] = f"{name}.value"
        extended[name.upper()] = f"{name}.value"
    return_sql = _convert_node(return_expr, extended, cfg)
    ctes = ",\n".join(cte_parts)
    full_sql = f"WITH {ctes}\nSELECT {return_sql}"
    return ConversionResult(
        full_sql,
        "partial",
        "VAR/RETURN converted to CTE — verify column references are correct in your query context.",
    )


def _convert_var_with_summarize(
    bindings: list[dict],
    return_expr: Any,
    res_map: dict[str, str],
    cfg: dict[str, Any],
) -> ConversionResult:
    """Attempt to convert VAR blocks that use SUMMARIZE.
    Emits a subquery CTE and marks partial.
    """
    extended = dict(res_map)
    cte_parts = []

    for b in bindings:
        name = b.get("name") or ""
        expr = b.get("expr") or {}
        func_name = (expr.get("name") or "").upper()

        if func_name == "SUMMARIZE":
            try:
                subquery = _convert_summarize_to_subquery(expr, extended, cfg)
                cte_parts.append(f"{name} AS ({subquery})")
                extended[name] = name
                extended[name.upper()] = name
            except ValueError as e:
                return ConversionResult("", "manual", str(e))
        else:
            sql = _convert_node(expr, extended, cfg)
            extended[name] = sql
            extended[name.upper()] = sql

    return_sql = _convert_node(return_expr, extended, cfg)

    if cte_parts:
        ctes = ",\n".join(cte_parts)
        full_sql = f"WITH {ctes}\nSELECT {return_sql}"
    else:
        full_sql = return_sql

    return ConversionResult(
        full_sql,
        "partial",
        "SUMMARIZE converted to subquery — verify GROUP BY columns and aggregations are correct.",
    )


# ============================================================
# SUMMARIZE HANDLER
# ============================================================

def _convert_summarize_to_subquery(
    ast: dict[str, Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
) -> str:
    """Convert SUMMARIZE(table, col1, col2, 'label', expr, ...) to SELECT subquery.

    Args layout:
        args[0]         = table ref
        args[1..n]      = alternating: column_ref | (string_label, expr) pairs

    Output:
        SELECT col1, col2, expr AS label
        FROM table
        GROUP BY col1, col2
    """
    args = ast.get("args") or []
    if not args:
        raise ValueError("SUMMARIZE requires at least 1 argument (table)")

    table_sql = _convert_node(args[0], res_map, cfg)
    group_cols: list[str] = []
    select_exprs: list[str] = []
    i = 1

    while i < len(args):
        node = args[i]
        node_type = _normalize_node_type(node)

        # Column ref -> groupby column
        if node_type == "column_ref":
            col_sql = _convert_node(node, res_map, cfg)
            group_cols.append(col_sql)
            select_exprs.append(col_sql)
            i += 1

        # String literal -> label for next expression
        elif node_type == "literal" and isinstance(node.get("value"), str):
            label = clean_ref_name(node.get("value") or "")
            if i + 1 >= len(args):
                raise ValueError(
                    f"SUMMARIZE label '{label}' has no corresponding expression"
                )
            expr_sql = _convert_node(args[i + 1], res_map, cfg)
            select_exprs.append(f"{expr_sql} AS {label}")
            i += 2

        else:
            # Unknown arg shape
            raise ValueError(
                f"SUMMARIZE argument at position {i} is not a column ref or label — "
                f"rewrite manually."
            )

    group_clause = ", ".join(group_cols)
    select_clause = ", ".join(select_exprs)
    sql = f"SELECT {select_clause} FROM {table_sql}"
    if group_cols:
        sql += f" GROUP BY {group_clause}"
    return sql


def _convert_summarize(
    args: list[Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
    convert_fn: Any,
) -> ConversionResult:
    """SUMMARIZE as a standalone function call (outside VAR).
    Returns subquery wrapped in parens. Status = partial.
    """
    ast = {"name": "SUMMARIZE", "args": args}
    subquery = _convert_summarize_to_subquery(ast, res_map, cfg)
    return ConversionResult(
        f"({subquery})",
        "partial",
        "SUMMARIZE converted to subquery — verify GROUP BY columns and aggregations are correct.",
    )


# ============================================================
# CODE HANDLERS
# Each: (args, res_map, cfg, convert_fn) -> str
# Raise ValueError for unrecoverable cases.
# Return ConversionResult if status needs to be partial.
# ============================================================

def _convert_switch(args, res_map, cfg, convert_fn):
    """SWITCH(TRUE(), c1, v1, c2, v2, else) or SWITCH(expr, m1, v1, m2, v2, else)"""
    if not args:
        raise ValueError("SWITCH requires at least 1 argument")
    first = args[0]
    is_true_mode = (
        isinstance(first, dict)
        and (first.get("name") or "").upper() == "TRUE"
    )
    branches = args[1:]
    parts = ["CASE"]
    if not is_true_mode:
        parts.append(convert_fn(first, res_map, cfg))
    i = 0
    while i < len(branches) - 1:
        cond = convert_fn(branches[i], res_map, cfg)
        val = convert_fn(branches[i + 1], res_map, cfg)
        parts.append(f"WHEN {cond} THEN {val}")
        i += 2
    if i < len(branches):
        parts.append(f"ELSE {convert_fn(branches[i], res_map, cfg)}")
    parts.append("END")
    return " ".join(parts)


def _convert_coalesce(args, res_map, cfg, convert_fn):
    """COALESCE(a, b, c, ...) -> COALESCE(a, b, c, ...)"""
    parts = [convert_fn(a, res_map, cfg) for a in args]
    return f"COALESCE({', '.join(parts)})"


def _convert_selectedvalue(args, res_map, cfg, convert_fn):
    """SELECTEDVALUE(col) -> MAX(col)  [partial — loses slicer context]
       SELECTEDVALUE(col, alt) -> COALESCE(MAX(col), alt)
    """
    if not args:
        raise ValueError("SELECTEDVALUE requires at least 1 argument")
    col = convert_fn(args[0], res_map, cfg)
    if len(args) >= 2:
        alt = convert_fn(args[1], res_map, cfg)
        sql = f"COALESCE(MAX({col}), {alt})"
    else:
        sql = f"MAX({col})"
    return ConversionResult(
        sql,
        "partial",
        "SELECTEDVALUE approximated as MAX() — loses Power BI slicer filter context.",
    )


def _make_iteratorx_handler(agg_func: str):
    """Factory for SUMX, AVERAGEX, MINX, MAXX, COUNTX, COUNTAX."""
    def handler(args, res_map, cfg, convert_fn):
        if len(args) < 2:
            raise ValueError(f"{agg_func}X requires 2 arguments (table, expr)")
        expr = convert_fn(args[1], res_map, cfg)
        sql = f"{agg_func}({expr})"
        return ConversionResult(
            sql,
            "partial",
            f"{agg_func}X table context dropped — result is {agg_func}(expr) "
            f"across all rows. Verify this matches intent.",
        )
    handler.__name__ = f"_convert_{agg_func.lower()}x"
    return handler


def _convert_countblank(args, res_map, cfg, convert_fn):
    """COUNTBLANK(col) -> COUNTIF(col IS NULL)"""
    if not args:
        raise ValueError("COUNTBLANK requires 1 argument")
    col = convert_fn(args[0], res_map, cfg)
    return f"COUNTIF({col} IS NULL)"


def _convert_distinctcountnoblank(args, res_map, cfg, convert_fn):
    """DISTINCTCOUNTNOBLANK(col) -> COUNT(DISTINCT CASE WHEN col IS NOT NULL THEN col END)"""
    if not args:
        raise ValueError("DISTINCTCOUNTNOBLANK requires 1 argument")
    col = convert_fn(args[0], res_map, cfg)
    return f"COUNT(DISTINCT CASE WHEN {col} IS NOT NULL THEN {col} END)"


def _convert_eomonth(args, res_map, cfg, convert_fn):
    """EOMONTH(date, months) -> LAST_DAY(DATE_ADD(date, INTERVAL months MONTH))"""
    if not args:
        raise ValueError("EOMONTH requires at least 1 argument")
    date = convert_fn(args[0], res_map, cfg)
    months = convert_fn(args[1], res_map, cfg) if len(args) > 1 else "0"
    return f"LAST_DAY(DATE_ADD({date}, INTERVAL {months} MONTH))"


_INTERVAL_MAP = {
    "DAY": "DAY", "MONTH": "MONTH", "YEAR": "YEAR",
    "QUARTER": "QUARTER", "WEEK": "WEEK",
    "HOUR": "HOUR", "MINUTE": "MINUTE", "SECOND": "SECOND",
}


def _extract_interval(node: dict[str, Any]) -> str:
    """Extract BQ interval unit from IntervalKeyword, literal, or name node."""
    raw = (
        node.get("value")
        or node.get("name")
        or "DAY"
    )
    return _INTERVAL_MAP.get(str(raw).upper().strip(), "DAY")


def _convert_datediff(args, res_map, cfg, convert_fn):
    """DATEDIFF(start, end, interval) -> DATE_DIFF(end, start, interval)
       DAX arg order is start, end — BigQuery is reversed.
    """
    if len(args) < 2:
        raise ValueError("DATEDIFF requires at least 2 arguments")
    start = convert_fn(args[0], res_map, cfg)
    end = convert_fn(args[1], res_map, cfg)
    interval = _extract_interval(args[2]) if len(args) > 2 else "DAY"
    return f"DATE_DIFF({end}, {start}, {interval})"


def _convert_dateadd(args, res_map, cfg, convert_fn):
    """DATEADD(dates, n, interval) -> DATE_ADD(date, INTERVAL n unit)
       Partial — loses time intelligence calendar semantics.
    """
    if len(args) < 2:
        raise ValueError("DATEADD requires at least 2 arguments")
    date = convert_fn(args[0], res_map, cfg)
    n = convert_fn(args[1], res_map, cfg)
    interval = _extract_interval(args[2]) if len(args) > 2 else "DAY"
    sql = f"DATE_ADD({date}, INTERVAL {n} {interval})"
    return ConversionResult(
        sql,
        "partial",
        "DATEADD converted to DATE_ADD — loses time intelligence calendar context. "
        "Verify result is correct for your date table.",
    )


def _convert_weekday(args, res_map, cfg, convert_fn):
    """WEEKDAY(date, return_type)
       return_type 1: Sunday=1 (default BQ DAYOFWEEK)
       return_type 2: Monday=1
       return_type 3: Monday=0
    """
    if not args:
        raise ValueError("WEEKDAY requires at least 1 argument")
    date = convert_fn(args[0], res_map, cfg)
    return_type = 1
    if len(args) > 1:
        raw = args[1].get("value")
        if raw is not None:
            try:
                return_type = int(raw)
            except (TypeError, ValueError):
                pass
    if return_type == 2:
        return f"MOD(EXTRACT(DAYOFWEEK FROM {date}) + 5, 7) + 1"
    if return_type == 3:
        return f"MOD(EXTRACT(DAYOFWEEK FROM {date}) + 5, 7)"
    return f"EXTRACT(DAYOFWEEK FROM {date})"


_FORMAT_MAP = {
    "MMMM": "%B", "MMM": "%b", "MM": "%m", "M": "%-m",
    "YYYY": "%Y", "YY": "%y", "DD": "%d", "D": "%-d",
    "YYYY-MM-DD": "%Y-%m-%d", "DD/MM/YYYY": "%d/%m/%Y",
    "MM/DD/YYYY": "%m/%d/%Y", "HH:MM:SS": "%H:%M:%S", "HH:MM": "%H:%M",
}


def _convert_format(args, res_map, cfg, convert_fn):
    """FORMAT(value, format_string)
       Known date formats -> FORMAT_DATE
       Numeric/unknown -> FORMAT (approximate, partial)
    """
    if not args:
        raise ValueError("FORMAT requires at least 1 argument")
    val = convert_fn(args[0], res_map, cfg)
    if len(args) < 2:
        return f"CAST({val} AS STRING)"
    fmt_node = args[1]
    fmt_str = str(fmt_node.get("value") or "").strip().strip('"').strip("'")
    bq_fmt = _FORMAT_MAP.get(fmt_str.upper())
    if bq_fmt:
        return f"FORMAT_DATE('{bq_fmt}', {val})"
    # Unknown format — approximate
    sql = f"FORMAT('{fmt_str}', {val})"
    return ConversionResult(
        sql,
        "partial",
        f"FORMAT with format string '{fmt_str}' approximated — verify output matches expected format.",
    )


def _convert_text(args, res_map, cfg, convert_fn):
    """TEXT(value, format) — same logic as FORMAT."""
    return _convert_format(args, res_map, cfg, convert_fn)


def _convert_replace(args, res_map, cfg, convert_fn):
    """REPLACE(text, start_pos, num_chars, new_text)
       -> CONCAT(LEFT(text, start-1), new_text, SUBSTR(text, start+num_chars))
    """
    if len(args) < 4:
        raise ValueError("REPLACE requires 4 arguments: text, start_pos, num_chars, new_text")
    text = convert_fn(args[0], res_map, cfg)
    start = convert_fn(args[1], res_map, cfg)
    length = convert_fn(args[2], res_map, cfg)
    new = convert_fn(args[3], res_map, cfg)
    return f"CONCAT(LEFT({text}, {start} - 1), {new}, SUBSTR({text}, {start} + {length}))"


def _convert_concatenatex(args, res_map, cfg, convert_fn):
    """CONCATENATEX(table, expr, delimiter) -> STRING_AGG(expr, delimiter)
       Partial — loses table iteration context.
    """
    if len(args) < 2:
        raise ValueError("CONCATENATEX requires at least 2 arguments")
    expr = convert_fn(args[1], res_map, cfg)
    delim = convert_fn(args[2], res_map, cfg) if len(args) > 2 else "','"
    sql = f"STRING_AGG({expr}, {delim})"
    return ConversionResult(
        sql,
        "partial",
        "CONCATENATEX table context dropped — result is STRING_AGG across all rows. "
        "Verify this matches intent.",
    )


def _convert_iferror(args, res_map, cfg, convert_fn):
    """IFERROR(expr, fallback) -> IFNULL(expr, fallback)
       Partial — IFNULL only catches NULL, not all DAX errors.
    """
    if len(args) < 2:
        raise ValueError("IFERROR requires 2 arguments")
    expr = convert_fn(args[0], res_map, cfg)
    fallback = convert_fn(args[1], res_map, cfg)
    sql = f"IFNULL({expr}, {fallback})"
    return ConversionResult(
        sql,
        "partial",
        "IFERROR approximated as IFNULL — only handles NULL values, "
        "not division-by-zero or type errors. Verify fallback logic.",
    )


# ============================================================
# CALCULATE HANDLER
# ============================================================

def _classify_calculate_filter(node: dict[str, Any]) -> str:
    """Classify a CALCULATE filter arg."""
    if not isinstance(node, dict):
        return "unknown"
    name = (node.get("name") or "").upper()
    node_type = _normalize_node_type(node)
    if name == "ALL":
        col_args = [
            a for a in (node.get("args") or [])
            if _normalize_node_type(a) == "column_ref"
        ]
        return "all_table" if not col_args else "unknown"
    if name == "ALLEXCEPT":
        return "allexcept"
    if name == "ALLSELECTED":
        return "allselected"
    if name == "KEEPFILTERS":
        return "keepfilters"
    if name == "FILTER":
        return "filter_condition"
    if node_type == "binop" and (node.get("op") or "") in (
        "=", ">", "<", ">=", "<=", "<>", "!="
    ):
        return "simple_condition"
    if node_type == "in_expr":
        return "simple_condition"
    return "unknown"


def _extract_calculate_condition(node, res_map, cfg, convert_fn):
    """Extract BQ WHERE condition string from a FILTER node or direct binop."""
    name = (node.get("name") or "").upper()
    if name == "FILTER":
        filter_args = node.get("args") or []
        if len(filter_args) >= 2:
            return convert_fn(filter_args[1], res_map, cfg)
        raise ValueError("FILTER node missing condition argument")
    return convert_fn(node, res_map, cfg)


def _wrap_with_case_when(expr_node, condition, res_map, cfg, convert_fn):
    """Wrap a simple aggregate with CASE WHEN condition."""
    node_type = _normalize_node_type(expr_node)
    
    # Handle column reference (measure reference) - apply condition directly
    if node_type == "column_ref":
        col_sql = convert_fn(expr_node, res_map, cfg)
        # For a measure reference, we can't know the aggregation, so wrap in CASE WHEN
        # This is a partial conversion - assumes the measure is an aggregation
        return f"CASE WHEN {condition} THEN {col_sql} ELSE NULL END"
    
    # Handle function calls
    name = (expr_node.get("name") or "").upper()
    inner_args = expr_node.get("args") or []

    agg_map = {
        "SUM": "SUM", "AVERAGE": "AVG", "AVG": "AVG",
        "MIN": "MIN", "MAX": "MAX",
        "COUNT": "COUNT", "COUNTA": "COUNT",
    }

    if name == "DISTINCTCOUNT" and inner_args:
        col_sql = convert_fn(inner_args[0], res_map, cfg)
        return f"COUNT(DISTINCT CASE WHEN {condition} THEN {col_sql} END)"

    if name in agg_map and inner_args:
        col_sql = convert_fn(inner_args[0], res_map, cfg)
        return f"{agg_map[name]}(CASE WHEN {condition} THEN {col_sql} END)"

    raise ValueError(
        f"CALCULATE inner expression '{name}' is not a recognised simple aggregate "
        f"— cannot auto-convert. Rewrite manually."
    )


def _convert_calculate(args, res_map, cfg, convert_fn):
    """Convert CALCULATE to BigQuery SQL.

    Supported patterns:
        1. No filters              -> convert expression directly
        2. ALL(table)              -> expr OVER ()
        3. ALLEXCEPT(table, cols)  -> expr OVER (PARTITION BY cols)
        4. FILTER(table, cond)     -> AGG(CASE WHEN cond THEN col END)
        5. simple binop/IN cond    -> AGG(CASE WHEN cond THEN col END)
        6. multiple conditions     -> AGG(CASE WHEN cond1 AND cond2 THEN col END)

    Raises ValueError for unrecognised patterns.
    """
    if not args:
        raise ValueError("CALCULATE requires at least 1 argument")

    expr_node = args[0]
    filter_args = args[1:]

    # Pattern 1 — no filters
    if not filter_args:
        return convert_fn(expr_node, res_map, cfg)

    filter_types = [_classify_calculate_filter(f) for f in filter_args]

    if "unknown" in filter_types:
        unrecognised = [
            (filter_args[i].get("name") or str(type(filter_args[i])))
            for i, t in enumerate(filter_types)
            if t == "unknown"
        ]
        raise ValueError(
            f"CALCULATE contains unrecognised filter(s): {unrecognised} — rewrite manually."
        )

    # Pattern 2 — ALL(table)
    if filter_types == ["all_table"]:
        expr_sql = convert_fn(expr_node, res_map, cfg)
        return f"{expr_sql} OVER ()"

    # Pattern 3 — ALLEXCEPT
    if filter_types == ["allexcept"]:
        allexcept_args = filter_args[0].get("args") or []
        partition_nodes = allexcept_args[1:]
        if not partition_nodes:
            raise ValueError("ALLEXCEPT requires at least one column argument")
        partition_cols = [convert_fn(c, res_map, cfg) for c in partition_nodes]
        expr_sql = convert_fn(expr_node, res_map, cfg)
        return f"{expr_sql} OVER (PARTITION BY {', '.join(partition_cols)})"

    if filter_types == ["allselected"]:
        allselected_args = filter_args[0].get("args") or []
        if not allselected_args:
            raise ValueError("ALLSELECTED requires at least one column argument")
        partition_cols = [convert_fn(c, res_map, cfg) for c in allselected_args]
        expr_sql = convert_fn(expr_node, res_map, cfg)
        return f"SUM({expr_sql}) OVER()"
    
    if filter_types == ["keepfilters"]:
        keepfilters_args = filter_args[0].get("args") or []
        if not keepfilters_args:
            raise ValueError("KEEPFILTERS requires at least one column argument")
        # KEEPFILTERS(condition) -> CASE WHEN condition THEN expr END (same as FILTER/simple)
        condition_sql = _extract_calculate_condition(keepfilters_args[0], res_map, cfg, convert_fn)
        return _wrap_with_case_when(expr_node, condition_sql, res_map, cfg, convert_fn)

    # Pattern 4, 5, 6 — FILTER / binop conditions
    if all(t in ("filter_condition", "simple_condition") for t in filter_types):
        conditions = [
            _extract_calculate_condition(f, res_map, cfg, convert_fn)
            for f in filter_args
        ]
        combined = " AND ".join(conditions)
        return _wrap_with_case_when(expr_node, combined, res_map, cfg, convert_fn)

    raise ValueError(
        f"CALCULATE has mixed filter types {filter_types} — pattern not supported. Rewrite manually."
    )


_HANDLERS: dict[str, Any] = {
    "SWITCH":               _convert_switch,
    "COALESCE":             _convert_coalesce,
    "SELECTEDVALUE":        _convert_selectedvalue,
    "SUMX":                 _make_iteratorx_handler("SUM"),
    "AVERAGEX":             _make_iteratorx_handler("AVG"),
    "MINX":                 _make_iteratorx_handler("MIN"),
    "MAXX":                 _make_iteratorx_handler("MAX"),
    "COUNTX":               _make_iteratorx_handler("COUNT"),
    "COUNTAX":              _make_iteratorx_handler("COUNT"),
    "COUNTBLANK":           _convert_countblank,
    "DISTINCTCOUNTNOBLANK": _convert_distinctcountnoblank,
    "EOMONTH":              _convert_eomonth,
    "DATEDIFF":             _convert_datediff,
    "DATEADD":              _convert_dateadd,
    "WEEKDAY":              _convert_weekday,
    "FORMAT":               _convert_format,
    "TEXT":                 _convert_text,
    "REPLACE":              _convert_replace,
    "CONCATENATEX":         _convert_concatenatex,
    "IFERROR":              _convert_iferror,
    "SUMMARIZE":            _convert_summarize,
    "CALCULATE":            _convert_calculate,
}


# ============================================================
# FUNCTION RESOLUTION
# ============================================================

def _convert_function(
    ast: dict[str, Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
    convert_fn: Any,
) -> str | ConversionResult:
    """Resolution order:
        1. unsupported  -> raise ValueError with message
        2. _HANDLERS    -> call code handler (may return ConversionResult)
        3. extract_map  -> EXTRACT(unit FROM arg)
        4. direct_map   -> template or FUNC(args)
        5. unknown      -> raise ValueError
    """
    name = (ast.get("name") or "").upper().strip()
    args = ast.get("args") or []
    unsupported = _unsupported_map(cfg)
    extract_map = cfg.get("extract_mapping") or {}
    direct = cfg.get("direct_mapping") or {}

    # 1. Unsupported
    if name in unsupported:
        raise ValueError(unsupported[name])

    # 2. Code handlers
    if name in _HANDLERS:
        return _HANDLERS[name](args, res_map, cfg, convert_fn)

    # 3. Extract mapping -> EXTRACT(unit FROM arg)
    if name in extract_map:
        unit = extract_map[name]
        if not unit:
            raise ValueError(f"Function {name} has no extract unit defined in yaml")
        if not args:
            raise ValueError(f"{name} requires at least 1 argument")
        arg_sql = convert_fn(args[0], res_map, cfg)
        return f"EXTRACT({unit} FROM {arg_sql})"

    # 4. Direct mapping
    if name in direct:
        template = direct[name]
        if template is None:
            raise ValueError(f"Function {name} has no BigQuery equivalent")
        if isinstance(template, str) and "{" in template:
            return _apply_direct_template(template, args, res_map, cfg, convert_fn)
        if isinstance(template, str) and not args:
            return template
        args_sql = ", ".join(convert_fn(a, res_map, cfg) for a in args)
        return f"{template}({args_sql})"

    # 5. Unknown
    raise ValueError(f"Unknown DAX function: {name}")


# ============================================================
# CORE CONVERT — walks any node
# ============================================================

def _convert_node(
    ast: dict[str, Any] | None,
    res_map: dict[str, str],
    cfg: dict[str, Any],
) -> str:
    """Internal recursive converter. Always returns str.
    Unwraps ConversionResult transparently — status propagation
    happens only at the convert_with_status boundary.
    """
    if ast is None:
        return "NULL"

    node_type = _normalize_node_type(ast)

    if node_type == "column_ref":
        return _convert_column_ref(ast, res_map)
    if node_type == "table_ref":
        return _convert_table_ref(ast, res_map)
    if node_type in ("literal", "blank", "interval"):
        return _convert_literal(ast)
    if node_type == "var_ref":
        return _convert_var_ref(ast, res_map)
    if node_type == "binop":
        return _convert_binop(ast, res_map, cfg, _convert_node)
    if node_type == "unaryop":
        return _convert_unaryop(ast, res_map, cfg, _convert_node)
    if node_type == "in_expr":
        return _convert_in_expr(ast, res_map, cfg, _convert_node)
    if node_type == "var_expr":
        result = _convert_var_expr(ast, res_map, cfg)
        if result.status == "manual":
            raise ValueError(result.message or "VAR/RETURN could not be converted")
        return result.sql
    if node_type == "func":
        result = _convert_function(ast, res_map, cfg, _convert_node)
        if isinstance(result, ConversionResult):
            if result.status == "manual":
                raise ValueError(result.message or "Function could not be converted")
            return result.sql
        return result

    return "NULL"


def convert(
    ast: dict[str, Any] | None,
    resolution_map: dict[str, str] | None = None,
    config: dict[str, Any] | None = None,
) -> str:
    """Convert DAX AST node to BigQuery SQL string.

    resolution_map: original field name -> cleaned field_name in view
                    (used to resolve unqualified column refs like [Total Revenue])
    Raises ValueError on unsupported/unknown functions.
    Use convert_with_status for the non-raising version.
    """
    return _convert_node(ast, resolution_map or {}, config or _get_config())


def clean_ref_name(name: str) -> str:
    """Lowercase, replace spaces/hyphens with underscores, strip non-alphanumeric."""
    s = (name or "").lower().strip().replace(" ", "_").replace("-", "_")
    return "".join(c for c in s if c.isalnum() or c == "_") or name


# ============================================================
# PUBLIC ENTRY POINT WITH STATUS
# ============================================================

def convert_with_status(
    ast: dict[str, Any] | None,
    resolution_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Convert DAX AST to BQ SQL. Never raises.

    Returns:
        {
            "conversion_status": "auto" | "partial" | "manual",
            "message":           None | str,
            "bq_formula":        str | None,
        }
    """
    res_map = resolution_map or {}
    cfg = _get_config()
    unsupported = _unsupported_map(cfg)

    out: dict[str, Any] = {
        "conversion_status": "auto",
        "message": None,
        "bq_formula": None,
    }

    if ast is None:
        out["bq_formula"] = "NULL"
        return out

    try:
        # Fast path: top-level unsupported function
        if _normalize_node_type(ast) == "func":
            name = (ast.get("name") or "").upper().strip()
            if name in unsupported:
                out["conversion_status"] = "manual"
                out["message"] = unsupported[name]
                return out

        # VAR/RETURN — handle separately to capture partial status
        if _normalize_node_type(ast) == "var_expr":
            result = _convert_var_expr(ast, res_map, cfg)
            out["conversion_status"] = result.status
            out["message"] = result.message
            out["bq_formula"] = result.sql if result.status != "manual" else None
            return out

        # All other nodes — use _convert_function to catch ConversionResult.partial
        node_type = _normalize_node_type(ast)
        if node_type == "func":
            raw = _convert_function(ast, res_map, cfg, _convert_node)
            if isinstance(raw, ConversionResult):
                out["conversion_status"] = raw.status
                out["message"] = raw.message
                out["bq_formula"] = raw.sql if raw.status != "manual" else None
                return out
            out["bq_formula"] = raw
            return out

        # Leaf nodes and other types
        out["bq_formula"] = _convert_node(ast, res_map, cfg)
        return out

    except ValueError as e:
        out["conversion_status"] = "manual"
        out["message"] = str(e)
        return out
    except Exception as e:
        out["conversion_status"] = "manual"
        out["message"] = str(e)[:300]
        return out
