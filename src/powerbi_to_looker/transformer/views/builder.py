"""Build artifact views from metadata model: one view per table, with cleanup, resolution map, formula conversion."""

from pathlib import Path
from typing import Any

from powerbi_to_looker.common.yaml_loader import load_yaml
from powerbi_to_looker.models.artifact import ArtifactField, ArtifactView
from powerbi_to_looker.transformer.views.field_cleanup import clean_field_name, deduplicate_field_names
from powerbi_to_looker.transformer.views.field_type_mapping import infer_measure_type_from_formula_ast, map_field_type
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
        
        # Skip hidden system tables (DateTableTemplate, LocalDateTable)
        extended_props = t.get("extended_properties") or {}
        is_hidden = extended_props.get("isHidden", False)
        if is_hidden:
            continue  # Skip hidden tables
        
        table_type = (t.get("table_type") or "physical").strip().lower()
        view_name = _clean_table_name(table_name, reserved)
        table_fields = by_table.get(table_name) or []

        # 1) Clean + deduplicate to get final field_name on each
        for x in table_fields:
            x["field_name"] = clean_field_name(x.get("name") or "", reserved)
        deduplicate_field_names(table_fields, name_key="name", id_key="id", reserved_words=reserved)

        # 2) Pass 1: Classify each field (two_step vs one_step measure vs dimension/dimension_group)
        for x in table_fields:
            data_type = x.get("data_type")
            aggregation = x.get("aggregation")
            orig_name = (x.get("name") or "").strip()
            type_info = map_field_type(data_type, aggregation, orig_name)
            canonical_field_type = (x.get("field_type") or "").strip().lower()
            if canonical_field_type in ("measure", "dimension", "dimension_group"):
                field_type = canonical_field_type
            else:
                field_type = type_info["field_type"]
            dt_lower = (data_type or "").strip().lower()
            if field_type == "dimension" and dt_lower in ("datetime", "date", "time"):
                field_type = "dimension_group"
            if field_type == "measure":
                x["_measure_pattern"] = "two_step" if aggregation else "one_step"
            else:
                x["_measure_pattern"] = None
            x["_field_type"] = field_type
            x["_looker_type"] = type_info["looker_type"]
            x["_timeframes"] = type_info.get("timeframes")
            x["_value_format"] = type_info.get("value_format")
            x["_conversion_status"] = type_info.get("conversion_status") or "auto"
            if field_type == "measure" and not aggregation and x.get("formula_ast"):
                inferred = infer_measure_type_from_formula_ast(x["formula_ast"])
                if inferred:
                    x["_looker_type"] = inferred
                else:
                    x["_looker_type"] = type_info.get("looker_type") or "number"

        # 3) Resolution map for formula refs: two_step -> ${field_name_measure}, one_step/dimension -> ${field_name}
        resolution_map: dict[str, str] = {}
        for x in table_fields:
            orig = (x.get("name") or "").strip()
            if not orig or orig in resolution_map:
                continue
            fname = x.get("field_name") or ""
            resolution_map[orig] = fname + "_measure" if x.get("_measure_pattern") == "two_step" else fname

        # 4) Pass 2: Build ArtifactField for each (formula translation uses resolution_map)
        artifact_fields: list[ArtifactField] = []
        for x in table_fields:
            fname = x.get("field_name") or ""
            orig_name = (x.get("name") or "").strip()
            formula_ast = x.get("formula_ast")
            formula = x.get("formula")
            source_column = (x.get("source_column") or "").strip()
            is_calculated = x.get("is_calculated") or False
            field_type = x["_field_type"]
            measure_pattern = x.get("_measure_pattern")
            looker_type = x["_looker_type"]
            if measure_pattern == "one_step":
                looker_type = "number"
            timeframes = x.get("_timeframes")
            value_format = x.get("_value_format")
            conversion_status = x.get("_conversion_status") or "auto"
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
                    measure_pattern=measure_pattern,
                )
            )

        # 5) Field ordering: dimensions -> dimension_groups -> measures
        def _order_key(f: ArtifactField) -> tuple[int, str]:
            if f.field_type == "dimension":
                return (0, f.field_name)
            if f.field_type == "dimension_group":
                return (1, f.field_name)
            return (2, f.field_name)

        artifact_fields.sort(key=_order_key)

        # 6) View-level sql_table_name / derived_table_sql
        sql_table_name = None
        derived_table_sql = None
        conversion_status = "auto"
        message = None
        
        if table_type == "physical":
            sql_table_name = _sql_table_name(database, schema, table_name)
        elif table_type == "calculated":
            # Use formula_ast from canonical model (already parsed)
            formula_ast = t.get("formula_ast")
            formula_parse_error = t.get("formula_parse_error")
            
            if formula_parse_error:
                conversion_status = "manual"
                message = f"Formula parse error: {formula_parse_error}"
            elif formula_ast:
                # Build resolution map for table-level conversion
                # Map table names to their SQL table names for formula conversion
                table_res_map = {}
                for other_table in tables:
                    other_table_name = (other_table.get("table_name") or other_table.get("name") or "").strip()
                    if other_table_name and other_table.get("table_type") == "physical":
                        sql_name = _sql_table_name(database, schema, other_table_name)
                        table_res_map[other_table_name] = sql_name
                        # Also add with quotes (DAX uses 'table_name')
                        table_res_map[f"'{other_table_name}'"] = sql_name
                
                # Convert formula AST to SQL
                result = convert_with_status(formula_ast, table_res_map)
                bq_sql = result.get("bq_formula")
                status = result.get("conversion_status", "auto")
                msg = result.get("message")
                
                if bq_sql and status in ("auto", "partial"):
                    # Remove outer parens if present (SUMMARIZE returns subquery in parens)
                    if bq_sql.startswith("(") and bq_sql.endswith(")"):
                        derived_table_sql = bq_sql[1:-1]
                    else:
                        derived_table_sql = bq_sql
                    conversion_status = status
                    message = msg
                else:
                    conversion_status = "manual"
                    message = msg or "Formula conversion failed or returned manual status"
            else:
                conversion_status = "manual"
                message = "No formula AST available (formula may be empty or not parsed)"

        views.append(
            ArtifactView(
                view_name=view_name,
                label=table_name,
                source_table=table_name,
                view_type=table_type,
                sql_table_name=sql_table_name,
                derived_table_sql=derived_table_sql,
                conversion_status=conversion_status,
                message=message,
                fields=artifact_fields,
            )
        )
    return views
