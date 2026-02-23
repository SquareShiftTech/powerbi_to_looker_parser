"""Tables handler: raw["model"] -> TablesResult (tables, table_relationships, connection)."""

from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml
from powerbi_to_looker.dax.parser import parse_formula
from powerbi_to_looker.models.canonical import (
    Connection,
    Table,
    TableRelationship,
)
from powerbi_to_looker.parser_normalizer.semantic.protocol import TablesResult

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "powerbi_canonical_mapping.yaml"


def _get_config() -> dict[str, Any]:
    """Load Power BI -> canonical mapping config."""
    if _CONFIG_PATH.exists():
        return load_yaml(_CONFIG_PATH)
    return {}


def _infer_connection_provider_from_m(expression: list[str], config: dict[str, Any]) -> str:
    """Infer connection_provider from M expression lines. Returns canonical provider or 'unknown'."""
    provider_map = config.get("connection_provider") or {}
    default = provider_map.get("default", "unknown")
    text = " ".join(expression) if isinstance(expression, list) else str(expression)
    for pattern, provider in provider_map.items():
        if pattern == "default":
            continue
        if pattern in text:
            return provider
    return default


def _parse_m_for_connection(expression: list[str]) -> tuple[str, str, str]:
    """Best-effort parse M expression for server, database, schema. Returns (server, database, schema)."""
    server = ""
    database = ""
    schema = ""
    if not isinstance(expression, list):
        return server, database, schema
    for line in expression:
        s = line.strip()
        if "Source{[Name=" in s or ("[Name=" in s and "][Data]" in s and not database):
            # First Name= often database e.g. Source{[Name=\"tableau-to-looker-migration\"]}[Data]
            try:
                start = s.find('Name="') + 6
                end = s.find('"', start)
                if start > 5 and end > start:
                    database = s[start:end].replace('\\"', '"')
            except Exception:
                pass
        if 'Kind="Schema"' in s or "Kind=\\\"Schema\\\"" in s:
            # Schema line e.g. {[Name=\"Marketing_Campaign\",Kind=\"Schema\"]}
            try:
                start = s.find('Name="') + 6
                end = s.find('"', start)
                if start > 5 and end > start:
                    schema = s[start:end].replace('\\"', '"')
            except Exception:
                pass
    return server, database, schema


def can_handle(raw: dict[str, Any]) -> bool:
    """Return True if raw contains a model with tables."""
    model = raw.get("model") or raw
    if isinstance(model, dict) and "model" in model:
        model = model["model"]
    return isinstance(model, dict) and isinstance(model.get("tables"), list)


def run(raw: dict[str, Any]) -> TablesResult:
    """Build TablesResult from raw model: tables, table_relationships, connection."""
    config = _get_config()
    model_obj = raw.get("model") or raw
    if isinstance(model_obj, dict) and "model" in model_obj:
        model = model_obj["model"]
        db_name = model_obj.get("name", "")
    else:
        model = model_obj
        db_name = ""

    tables: list[Table] = []
    for t in model.get("tables") or []:
        table_name = t.get("name") or ""
        table_id = t.get("lineageTag") or table_name
        schema_val: str | None = None
        table_type: str | None = None
        formula_val: str | None = None
        for part in t.get("partitions") or []:
            src = part.get("source") or {}
            src_type = src.get("type")
            if src_type == "m" and isinstance(src.get("expression"), list):
                _server, _db, schema_val = _parse_m_for_connection(src["expression"])
                if schema_val:
                    break
            if src_type == "calculated":
                expr = src.get("expression")
                if isinstance(expr, list):
                    formula_val = "\n".join(str(line) for line in expr).strip() or None
                elif isinstance(expr, str):
                    formula_val = expr.strip() or None
                table_type = "calculated"
                break
        if table_type is None:
            # Has M partition(s) only or no partitions
            for part in t.get("partitions") or []:
                if (part.get("source") or {}).get("type") == "m":
                    table_type = "physical"
                    break
        
        # Parse formula AST for calculated tables
        formula_ast = None
        formula_parse_error = None
        if formula_val:
            formula_ast, formula_parse_error = parse_formula(formula_val)
        
        tables.append(
            Table(
                id=table_id,
                name=table_name,
                schema=schema_val,
                table_name=table_name,
                table_type=table_type,
                formula=formula_val,
                formula_ast=formula_ast,
                formula_parse_error=formula_parse_error,
                extended_properties={
                    "isHidden": t.get("isHidden"),
                    "hierarchies": t.get("hierarchies"),
                }
                if (t.get("isHidden") is not None or t.get("hierarchies"))
                else None,
            )
        )

    rel_config = config.get("relationship") or {}
    join_default = (rel_config.get("join_type") or {}).get("default", "LEFT")

    table_relationships: list[TableRelationship] = []
    for rel in model.get("relationships") or []:
        table_relationships.append(
            TableRelationship(
                from_table=rel.get("fromTable", ""),
                to_table=rel.get("toTable", ""),
                join_type=join_default,
                on_columns=[{"from": rel.get("fromColumn", ""), "to": rel.get("toColumn", "")}],
            )
        )

    # Connection from first partition with M source
    connection_type = "import"
    server = ""
    database = ""
    schema = ""
    connection_provider: str | None = "unknown"
    for t in model.get("tables") or []:
        for part in t.get("partitions") or []:
            src = part.get("source") or {}
            mode = part.get("mode", "import")
            if src.get("type") == "m":
                expr = src.get("expression") or []
                connection_provider = _infer_connection_provider_from_m(expr, config)
                server, database, schema = _parse_m_for_connection(expr)
                if mode == "directQuery":
                    connection_type = "direct_query"
                break
        else:
            continue
        break

    connection = Connection(
        type=connection_type,
        server=server,
        database=database,
        schema=schema or None,
        connection_provider=connection_provider,
    )

    return TablesResult(
        tables=tables,
        table_relationships=table_relationships,
        connection=connection,
    )
