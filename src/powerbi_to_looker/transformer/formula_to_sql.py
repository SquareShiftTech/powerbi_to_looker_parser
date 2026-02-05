"""Pattern-based DAX formula → LookML SQL. Resolves [Name] to ${lookml_name} via name map."""

import re
from typing import Any

from powerbi_to_looker.transformer.dimensions import sanitize_name


def _normalize(s: str) -> str:
    return (s or "").strip().replace("\n", " ").replace("\r", " ")


def _ref_to_lookml(ref: str, name_map: dict[str, str], config: dict[str, Any]) -> str:
    """Map a DAX reference [Name] or Table[Col] to LookML ${name}."""
    ref = ref.strip().strip("[]")
    # Table[Col] -> use Col as display name for lookup
    if "[" in ref and "]" in ref:
        m = re.search(r"\[([^\]]+)\]", ref)
        if m:
            ref = m.group(1).strip()
    # Try exact, then case-insensitive
    if ref in name_map:
        return f"${{{name_map[ref]}}}"
    for k, v in name_map.items():
        if k.lower() == ref.lower():
            return f"${{{v}}}"
    # Fallback: sanitize ref and use as-is (may be wrong if not in view)
    return f"${{{sanitize_name(ref, config)}}}"


def dax_to_lookml_sql(
    formula: str,
    name_map: dict[str, str],
    config: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Convert DAX formula to LookML SQL using pattern matching and name_map.

    name_map: Power BI display name (e.g. 'Total Sales') -> LookML field name (e.g. 'total_sales').

    Returns:
        (sql, measure_type) or (None, None) on failure. measure_type can be sum, count, count_distinct, avg, number, etc.
    """
    if not formula or not isinstance(formula, str):
        return None, None
    raw = _normalize(formula)
    if not raw:
        return None, None

    # Build name_map with sanitized keys for [Name] style refs (display name -> lookml_name)
    # name_map is already display -> lookml

    # DIVIDE ( [A], [B], 0 ): generic -> NULLIF; bigquery -> SAFE_DIVIDE + IFNULL
    divide_pat = re.compile(
        r"DIVIDE\s*\(\s*\[([^\]]+)\]\s*,\s*\[([^\]]+)\]\s*,\s*0\s*\)",
        re.IGNORECASE,
    )
    m = divide_pat.search(raw)
    if m:
        a, b = m.group(1).strip(), m.group(2).strip()
        a_sql = _ref_to_lookml(f"[{a}]", name_map, config)
        b_sql = _ref_to_lookml(f"[{b}]", name_map, config)
        dialect = (config.get("sql_dialect") or "generic").lower()
        if dialect == "bigquery":
            return f"IFNULL(SAFE_DIVIDE({a_sql}, {b_sql}), 0)", "number"
        return f"{a_sql} / NULLIF({b_sql}, 0)", "number"

    # SUM ( Table[Col] ) or SUM(Table[Col]) -> sum, ${col}
    sum_pat = re.compile(
        r"SUM\s*\(\s*(?:[\w\.]+\s*\[\s*([^\]]+)\s*\]|\[\s*([^\]]+)\s*\])\s*\)",
        re.IGNORECASE,
    )
    m = sum_pat.search(raw)
    if m:
        col = (m.group(1) or m.group(2) or "").strip()
        ref = _ref_to_lookml(f"[{col}]", name_map, config)
        return ref, "sum"

    # DISTINCTCOUNT ( Table[Col] ) -> count_distinct
    dc_pat = re.compile(
        r"DISTINCTCOUNT\s*\(\s*(?:[\w\.]+\s*\[\s*([^\]]+)\s*\]|\[\s*([^\]]+)\s*\])\s*\)",
        re.IGNORECASE,
    )
    m = dc_pat.search(raw)
    if m:
        col = (m.group(1) or m.group(2) or "").strip()
        ref = _ref_to_lookml(f"[{col}]", name_map, config)
        return ref, "count_distinct"

    # COUNT ( Table[Col] ) or Count(Table[Col])
    count_pat = re.compile(
        r"COUNT\s*\(\s*(?:[\w\.]+\s*\[\s*([^\]]+)\s*\]|\[\s*([^\]]+)\s*\])\s*\)",
        re.IGNORECASE,
    )
    m = count_pat.search(raw)
    if m:
        col = (m.group(1) or m.group(2) or "").strip()
        ref = _ref_to_lookml(f"[{col}]", name_map, config)
        return ref, "count"

    # AVERAGE ( Table[Col] ) -> avg
    avg_pat = re.compile(
        r"AVERAGE\s*\(\s*(?:[\w\.]+\s*\[\s*([^\]]+)\s*\]|\[\s*([^\]]+)\s*\])\s*\)",
        re.IGNORECASE,
    )
    m = avg_pat.search(raw)
    if m:
        col = (m.group(1) or m.group(2) or "").strip()
        ref = _ref_to_lookml(f"[{col}]", name_map, config)
        return ref, "average"

    # MIN / MAX
    min_pat = re.compile(
        r"MIN\s*\(\s*(?:[\w\.]+\s*\[\s*([^\]]+)\s*\]|\[\s*([^\]]+)\s*\])\s*\)",
        re.IGNORECASE,
    )
    m = min_pat.search(raw)
    if m:
        col = (m.group(1) or m.group(2) or "").strip()
        ref = _ref_to_lookml(f"[{col}]", name_map, config)
        return ref, "min"
    max_pat = re.compile(
        r"MAX\s*\(\s*(?:[\w\.]+\s*\[\s*([^\]]+)\s*\]|\[\s*([^\]]+)\s*\])\s*\)",
        re.IGNORECASE,
    )
    m = max_pat.search(raw)
    if m:
        col = (m.group(1) or m.group(2) or "").strip()
        ref = _ref_to_lookml(f"[{col}]", name_map, config)
        return ref, "max"

    # Unmatched: return None so caller keeps placeholder + description
    return None, None
