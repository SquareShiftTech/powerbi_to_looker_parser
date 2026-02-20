"""Convert DAX formula AST to BigQuery SQL. Uses resolution_map for unqualified column refs."""

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


def convert(
    ast: dict[str, Any] | None,
    resolution_map: dict[str, str] | None = None,
    config: dict[str, Any] | None = None,
) -> str:
    """Convert DAX AST node to BigQuery SQL string. Unqualified column refs use resolution_map -> ${field_name}.

    resolution_map: original_name (or key used in DAX) -> final field_name in view.
    Raises on unsupported/unknown; use convert_with_status for conversion_status + message.
    """
    if ast is None:
        return "NULL"
    res_map = resolution_map or {}
    cfg = config or _get_config()
    direct = cfg.get("direct_mapping") or {}
    extract_map = cfg.get("extract_mapping") or {}
    op_map = cfg.get("operator_mapping") or {}
    unsupported = _unsupported_list(cfg)

    def _type(t: Any) -> str:
        return (t or "").strip() if isinstance(t, str) else ""

    node_type = _type(ast.get("type"))
    # Normalize: support both Pydantic (FunctionCall) and test (func) style
    if node_type == "FunctionCall":
        node_type = "func"
    elif node_type == "ColumnRef":
        node_type = "column_ref"
    elif node_type == "BinOp":
        node_type = "binop"
    elif node_type in ("Number", "String", "Boolean", "Blank"):
        node_type = "literal" if node_type in ("Number", "String", "Boolean") else "blank"

    if node_type == "column_ref" or ast.get("type") == "ColumnRef":
        table = ast.get("table")
        col = ast.get("column") or ""
        col_clean = str(col).strip()
        if not table or table is None:
            # Unqualified: resolve to final field_name
            final = res_map.get(col_clean) or res_map.get(col) or clean_ref_name(col_clean)
            return f"${{{final}}}"
        tbl = str(table).strip().lower().replace(" ", "_").replace("-", "_")
        return f"{tbl}.{col_clean.lower()}"
    if node_type == "blank" or ast.get("type") == "Blank":
        return "NULL"
    if node_type == "literal" or ast.get("type") in ("Number", "String", "Boolean"):
        v = ast.get("value")
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str):
            return "'" + v.replace("'", "''") + "'"
        return "NULL"
    if node_type == "binop" or ast.get("type") == "BinOp":
        op = ast.get("op") or ""
        left = convert(ast.get("left"), res_map, cfg)
        right = convert(ast.get("right"), res_map, cfg)
        bq_op = op_map.get(op) or op
        if bq_op == "POW":
            return f"POW({left}, {right})"
        return f"({left} {bq_op} {right})"
    if node_type == "func" or ast.get("type") == "FunctionCall":
        name = (ast.get("name") or "").upper().strip()
        args = ast.get("args") or []
        if name == "BLANK" and not args:
            return "NULL"
        if name in unsupported:
            raise ValueError(unsupported[name])
        if name in extract_map:
            unit = extract_map[name]
            if unit and len(args) >= 1:
                arg_sql = convert(args[0], res_map, cfg)
                return f"EXTRACT({unit} FROM {arg_sql})"
        if name in direct:
            template = direct[name]
            if template is None:
                raise ValueError(f"Function {name} has no mapping")
            if isinstance(template, str) and "{" in template:
                parts = []
                for i, a in enumerate(args):
                    parts.append(convert(a, res_map, cfg))
                out = template
                for i, p in enumerate(parts):
                    out = out.replace("{" + str(i) + "}", p)
                return out
            args_sql = ", ".join(convert(a, res_map, cfg) for a in args)
            return f"{template}({args_sql})"
        # Unknown function
        raise ValueError(f"Unknown function: {name}")
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
