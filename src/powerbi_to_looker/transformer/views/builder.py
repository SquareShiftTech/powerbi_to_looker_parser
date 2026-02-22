"""Build artifact views from metadata model: one view per table, with cleanup, resolution map, formula conversion."""

from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml
from powerbi_to_looker.models.artifact import ArtifactField, ArtifactView
from powerbi_to_looker.transformer.views.field_cleanup import clean_field_name, deduplicate_field_names
from powerbi_to_looker.transformer.views.field_type_mapping import map_field_type
from powerbi_to_looker.transformer.views.formula_converter import convert_with_status

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "looker_reserved_words.yaml"


def _reserved_words() -> set[str]:
    try:
        cfg = load_yaml(_CONFIG_PATH)
        return set(cfg.get("reserved_words") or [])
    except FileNotFoundError:
        return set()


def _clean_table_name(name: str, reserved: set[str]) -> str:
    """Clean table name for view_name (same rules as field cleanup)."""
    return clean_field_name(name, reserved)


def _sql_table_name(database: str, schema: str, table_name: str) -> str:
    """Backtick-quoted full table name for BigQuery."""
    d = (database or "").strip()
    s = (schema or "").strip()
    t = (table_name or "").strip()
    if not t:
        return ""
    if d and s:
        return f"`{d}.{s}.{t}`"
    if s:
        return f"`{s}.{t}`"
    return f"`{t}`"


def build_views(
    tables: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    connection: dict[str, Any],
    reserved: set[str] | None = None,
) -> list[ArtifactView]:
    """Build one ArtifactView per table. Fields grouped by source_table; cleanup then dedupe; resolution map for formulas."""
    reserved = reserved or _reserved_words()
    database = connection.get("database") or ""
    schema = connection.get("schema") or ""

    # Group fields by source_table
    by_table: dict[str, list[dict[str, Any]]] = {}
    for f in fields:
        st = (f.get("source_table") or "").strip()
        if st not in by_table:
            by_table[st] = []
        by_table[st].append(dict(f))

    views: list[ArtifactView] = []
    for t in tables:
        table_name = (t.get("table_name") or t.get("name") or "").strip()
        if not table_name:
            continue
        table_type = (t.get("table_type") or "physical").strip().lower()
        view_name = _clean_table_name(table_name, reserved)
        table_fields = by_table.get(table_name) or []

        # 1) Clean + deduplicate to get final field_name on each
        for x in table_fields:
            x["field_name"] = clean_field_name(x.get("name") or "", reserved)
        deduplicate_field_names(table_fields, name_key="name", id_key="id", reserved_words=reserved)

        # 2) Resolution map: original name -> final field_name (first occurrence wins)
        resolution_map: dict[str, str] = {}
        for x in table_fields:
            orig = (x.get("name") or "").strip()
            if orig and orig not in resolution_map:
                resolution_map[orig] = x.get("field_name") or ""

        # 3) Build ArtifactField for each
        artifact_fields: list[ArtifactField] = []
        for x in table_fields:
            fname = x.get("field_name") or ""
            orig_name = (x.get("name") or "").strip()
            data_type = x.get("data_type")
            aggregation = x.get("aggregation")
            formula_ast = x.get("formula_ast")
            formula = x.get("formula")
            source_column = (x.get("source_column") or "").strip()
            is_calculated = x.get("is_calculated") or False

            type_info = map_field_type(data_type, aggregation, orig_name)
            field_type = type_info["field_type"]
            looker_type = type_info["looker_type"]
            timeframes = type_info.get("timeframes")
            value_format = type_info.get("value_format")
            conversion_status = type_info.get("conversion_status") or "auto"
            message = None
            sql = ""
            bq_formula = None

            # SQL for dimension/dimension_group: ${TABLE}.column or expression
            if field_type in ("dimension", "dimension_group"):
                if formula_ast and is_calculated:
                    result = convert_with_status(formula_ast, resolution_map)
                    conversion_status = result.get("conversion_status") or conversion_status
                    message = result.get("message")
                    bq_formula = result.get("bq_formula")
                    _col = (source_column or fname).replace("[", "").replace("]", "").strip()
                    if not _col.replace("_", "").replace(" ", "").isalnum() or " " in _col:
                        _col_safe = "`" + _col.replace("`", "\\`") + "`"
                    else:
                        _col_safe = _col
                    sql = bq_formula if bq_formula else f"${{TABLE}}.{_col_safe}"
                else:
                    col = source_column.replace("[", "").replace("]", "").strip() if source_column else fname
                    # BigQuery/Looker: column names with spaces or special chars need backticks
                    if not col.replace("_", "").replace(" ", "").isalnum() or " " in col:
                        col_safe = "`" + col.replace("`", "\\`") + "`"
                    else:
                        col_safe = col
                    sql = f"${{TABLE}}.{col_safe}"
            else:
                # measure
                if formula_ast:
                    result = convert_with_status(formula_ast, resolution_map)
                    conversion_status = result.get("conversion_status") or conversion_status
                    message = result.get("message")
                    bq_formula = result.get("bq_formula")
                    sql = bq_formula if bq_formula else ""
                else:
                    col = source_column.replace("[", "").replace("]", "").strip() if source_column else fname
                    if not col.replace("_", "").replace(" ", "").isalnum() or " " in col:
                        col_safe = "`" + col.replace("`", "\\`") + "`"
                    else:
                        col_safe = col
                    sql = f"${{TABLE}}.{col_safe}"

            artifact_fields.append(
                ArtifactField(
                    field_name=fname,
                    original_name=orig_name,
                    field_type=field_type,
                    looker_type=looker_type,
                    label=orig_name,
                    description=None,
                    sql=sql or "",
                    value_format=value_format,
                    timeframes=timeframes,
                    hidden=False,
                    tags=[],
                    conversion_status=conversion_status,
                    message=message,
                    original_formula=formula,
                    bq_formula=bq_formula,
                )
            )

        # 4) Field ordering: dimensions -> dimension_groups -> measures; alphabetical within group
        def _order_key(f: ArtifactField) -> tuple[int, str]:
            if f.field_type == "dimension":
                return (0, f.field_name)
            if f.field_type == "dimension_group":
                return (1, f.field_name)
            return (2, f.field_name)

        artifact_fields.sort(key=_order_key)

        # 5) View-level sql_table_name / derived_table_sql
        sql_table_name = None
        derived_table_sql = None
        if table_type == "physical":
            sql_table_name = _sql_table_name(database, schema, table_name)
        # Calculated table: derived_table_sql in a later pass if formula is simple; else manual

        views.append(
            ArtifactView(
                view_name=view_name,
                label=table_name,
                source_table=table_name,
                view_type=table_type,
                sql_table_name=sql_table_name,
                derived_table_sql=derived_table_sql,
                conversion_status="auto",
                message=None,
                fields=artifact_fields,
            )
        )
    return views
