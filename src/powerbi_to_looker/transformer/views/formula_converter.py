"""Convert DAX formula AST to BigQuery SQL. Uses resolution_map for unqualified column refs."""

import re
from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "function_mapping.yaml"


def _get_config() -> dict[str, Any]:
    try:
        return load_yaml(_CONFIG_PATH)
    except FileNotFoundError:
        return {}


def _unsupported_list(config: dict[str, Any]) -> dict[str, str]:
    """Return map function name -> message for unsupported."""
    out: dict[str, str] = {}
    for item in config.get("unsupported") or []:
        if isinstance(item, dict):
            n = (item.get("name") or "").upper()
            m = item.get("message") or "Unsupported"
            out[n] = m
    return out


def _normalize_node_type(ast: dict[str, Any]) -> str:
    """Return one of: column_ref, literal, blank, binop, table_ref, func."""
    t = (ast.get("type") or "").strip() if isinstance(ast.get("type"), str) else ""
    if t == "FunctionCall":
        return "func"
    if t == "ColumnRef":
        return "column_ref"
    if t == "TableRef":
        return "table_ref"
    if t == "BinOp":
        return "binop"
    if t in ("Number", "String", "Boolean"):
        return "literal"
    if t == "Blank":
        return "blank"
    return "func"  # default for unknown type


def _convert_table_ref(ast: dict[str, Any]) -> str:
    """Return BQ-safe table name for use in FROM clause."""
    name = (ast.get("name") or "").strip()
    return clean_ref_name(name) if name else ""


def _convert_column_ref(
    ast: dict[str, Any],
    res_map: dict[str, str],
) -> str:
    """Unqualified -> ${field_name}; qualified -> table.column."""
    table = ast.get("table")
    col = ast.get("column") or ""
    col_clean = str(col).strip()
    if not table or table is None:
        final = res_map.get(col_clean) or res_map.get(col) or clean_ref_name(col_clean)
        return f"${{{final}}}"
    tbl = str(table).strip().lower().replace(" ", "_").replace("-", "_")
    return f"{tbl}.{col_clean.lower()}"


def _convert_literal(ast: dict[str, Any]) -> str:
    """Number, string, boolean, blank -> BQ literal or NULL."""
    if ast.get("type") == "Blank":
        return "NULL"
    v = ast.get("value")
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    return "NULL"


def _apply_direct_template(
    template: str,
    args: list[Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
    convert_fn: Any,
) -> str:
    """Convert each arg with convert_fn and substitute {0}, {1}, ... in template.
    Any placeholder with no matching arg (e.g. optional 3rd arg) is replaced with NULL."""
    parts = [convert_fn(a, res_map, cfg) for a in args]
    out = template
    for i, p in enumerate(parts):
        out = out.replace("{" + str(i) + "}", p)
    # Replace any remaining placeholders (optional args) with NULL
    out = re.sub(r"\{\d+\}", "NULL", out)
    return out


def _convert_binop(
    ast: dict[str, Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
    convert_fn: Any,
) -> str:
    """Left/right via convert_fn; op from operator_mapping; return (left op right) or POW(left, right)."""
    op_map = cfg.get("operator_mapping") or {}
    op = (ast.get("op") or "").strip()
    left = convert_fn(ast.get("left"), res_map, cfg)
    right = convert_fn(ast.get("right"), res_map, cfg)
    bq_op = op_map.get(op) or op
    if bq_op == "POW":
        return f"POW({left}, {right})"
    return f"({left} {bq_op} {right})"


def _convert_function(
    ast: dict[str, Any],
    res_map: dict[str, str],
    cfg: dict[str, Any],
    convert_fn: Any,
) -> str:
    """Resolution order: unsupported -> extract_mapping -> direct_mapping -> unknown."""
    name = (ast.get("name") or "").upper().strip()
    args = ast.get("args") or []
    unsupported = _unsupported_list(cfg)
    extract_map = cfg.get("extract_mapping") or {}
    direct = cfg.get("direct_mapping") or {}

    if name in unsupported:
        raise ValueError(unsupported[name])
    if name in extract_map:
        unit = extract_map[name]
        if unit and len(args) >= 1:
            arg_sql = convert_fn(args[0], res_map, cfg)
            return f"EXTRACT({unit} FROM {arg_sql})"
    if name in direct:
        template = direct[name]
        if template is None:
            raise ValueError(f"Function {name} has no mapping")
        if isinstance(template, str) and "{" in template:
            return _apply_direct_template(template, args, res_map, cfg, convert_fn)
        if isinstance(template, str) and len(args) == 0:
            return template
        args_sql = ", ".join(convert_fn(a, res_map, cfg) for a in args)
        return f"{template}({args_sql})"
    raise ValueError(f"Unknown function: {name}")


def convert(
    ast: dict[str, Any] | None,
    resolution_map: dict[str, str] | None = None,
    config: dict[str, Any] | None = None,
) -> str:
    """Convert DAX AST node to BigQuery SQL. Unqualified column refs use resolution_map -> ${field_name}.

    resolution_map: original_name (or key used in DAX) -> final field_name in view.
    Raises on unsupported/unknown; use convert_with_status for conversion_status + message.
    """
    if ast is None:
        return "NULL"
    res_map = resolution_map or {}
    cfg = config or _get_config()
    node_type = _normalize_node_type(ast)

    if node_type == "column_ref":
        return _convert_column_ref(ast, res_map)
    if node_type == "table_ref":
        return _convert_table_ref(ast)
    if node_type in ("literal", "blank"):
        return _convert_literal(ast)
    if node_type == "binop":
        return _convert_binop(ast, res_map, cfg, convert)
    if node_type == "func":
        return _convert_function(ast, res_map, cfg, convert)
    return "NULL"


def clean_ref_name(name: str) -> str:
    """Lowercase and replace spaces/hyphens for column/table ref in SQL (no reserved-word suffix)."""
    s = (name or "").lower().strip().replace(" ", "_").replace("-", "_")
    return "".join(c for c in s if c.isalnum() or c == "_") or name


def convert_with_status(
    ast: dict[str, Any] | None,
    resolution_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Convert DAX AST to BQ SQL with conversion_status and message. Never raises."""
    res_map = resolution_map or {}
    cfg = _get_config()
    unsupported = _unsupported_list(cfg)
    out: dict[str, Any] = {"conversion_status": "auto", "message": None, "bq_formula": None}
    if ast is None:
        out["bq_formula"] = "NULL"
        return out
    name = (ast.get("name") or "").upper().strip() if ast.get("type") in ("FunctionCall", "func") else ""
    if name in unsupported:
        out["conversion_status"] = "manual"
        out["message"] = unsupported[name]
        return out
    try:
        sql = convert(ast, res_map, cfg)
        out["bq_formula"] = sql
        return out
    except ValueError as e:
        out["conversion_status"] = "manual"
        out["message"] = str(e)
        return out
    except Exception as e:
        out["conversion_status"] = "manual"
        out["message"] = str(e)[:200]
        return out
