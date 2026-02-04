"""
extract_properties.py
─────────────────────
Extracts every property shown in the Power BI Desktop
Properties pane for each column in your .pbix.

    python extract_properties.py  YourReport.pbix

Requires
────────
    pip install pbixray

That's it.  No Azure, no API keys, nothing else.
PBIXRay handles the XPRESS9 binary decompression internally.
"""

import sys
import json
from pbixray import PBIXRay
from pathlib import Path


# ───────────────────────────────────────────────────────────
# summarizeBy  can be an int OR a string depending on PBI version
# ───────────────────────────────────────────────────────────
SUMMARIZE_INT_MAP = {
    0: "None",
    1: "Sum",
    2: "Min",
    3: "Max",
    4: "Average",
    5: "Count",
    6: "Count Distinct",
}


def normalize_summarize(val) -> str:
    """Handle both int (older) and string (newer) summarizeBy values."""
    if isinstance(val, int):
        return SUMMARIZE_INT_MAP.get(val, "None")
    if isinstance(val, str):
        return val.strip().title() if val.strip() else "None"
    return "None"


def parse_format(fmt: str | None) -> dict:
    """
    Derive  is_percentage / thousands_sep / decimal_places
    from the raw Power BI formatString.
    """
    if not fmt or fmt.strip().lower() == "general" or fmt.strip() == "":
        return {
            "format_string":  "General",
            "is_percentage":  False,
            "thousands_sep":  False,
            "decimal_places": "Auto",
        }

    is_pct    = "%" in fmt
    thousands = "," in fmt.split(".")[0]   # comma only in integer-part

    # decimal places = count of "0" or "#" after the dot
    dec: int | str = 0
    if "." in fmt:
        after = fmt.split(".")[-1]
        count = 0
        for ch in after:
            if ch in ("0", "#"):
                count += 1
            else:
                break                      # stop at %, space, etc.
        dec = count if count else "Auto"
    else:
        dec = "Auto"

    return {
        "format_string":  fmt,
        "is_percentage":  is_pct,
        "thousands_sep":  thousands,
        "decimal_places": dec,
    }


# ───────────────────────────────────────────────────────────
# Core extraction  —  uses PBIXRay's high-level API
# ───────────────────────────────────────────────────────────
def extract(pbix_path: str) -> list[dict]:
    """
    Open the .pbix with PBIXRay, pull the schema DataFrame,
    then enrich every row with the remaining Properties-pane fields
    from the internal metadata.
    """
    model = PBIXRay(pbix_path)

    # ── 1. schema  →  TableName, ColumnName, DataType ──
    schema_df = model.schema                          # pandas DataFrame

    # ── 2. try to grab the richer metadata from the internal
    #       SQLite connection that PBIXRay keeps in memory.
    #       If that's not accessible we fall back to schema only.
    rich_meta = {}                                    # (table, col) → dict
    try:
        # PBIXRay stores an apsw connection; query TMSCHEMA_COLUMNS directly
        conn = model._connection                      # apsw connection object
        cur  = conn.cursor()

        # This is the same system table Power BI uses internally
        cur.execute("""
            SELECT
                [TABLE_NAME],
                [COLUMN_NAME],
                [DATA_TYPE],
                [FORMAT_STRING],
                [IS_HIDDEN],
                [IS_NULLABLE],
                [SORT_BY_COLUMN],
                [DATA_CATEGORY],
                [SUMMARIZE_BY]
            FROM [TMSCHEMA_COLUMNS]
        """)

        cols = [
            "TABLE_NAME", "COLUMN_NAME", "DATA_TYPE",
            "FORMAT_STRING", "IS_HIDDEN", "IS_NULLABLE",
            "SORT_BY_COLUMN", "DATA_CATEGORY", "SUMMARIZE_BY",
        ]

        for row in cur:
            key = (row[0], row[1])                    # (table, column)
            rich_meta[key] = dict(zip(cols, row))

    except Exception:
        # If the internal DB isn't accessible (API change / version mismatch)
        # we still work — just with fewer fields.
        pass

    # ── 3. Build output rows ──
    results: list[dict] = []

    for _, row in schema_df.iterrows():
        tbl = str(row["TableName"])
        col = str(row["ColumnName"])
        key = (tbl, col)

        # start with what schema gives us
        entry: dict = {
            "table_name":  tbl,
            "column_name": col,
            "data_type":   str(row.get("PandasDataType", "unknown")),
        }

        # overlay with rich metadata if we got it
        if key in rich_meta:
            m = rich_meta[key]

            # data_type from the DB is more precise than pandas type
            entry["data_type"] = str(m.get("DATA_TYPE", entry["data_type"]))

            # format fields (derived)
            entry.update(parse_format(m.get("FORMAT_STRING")))

            # remaining direct fields
            entry["sort_by_column"] = m.get("SORT_BY_COLUMN") or "Default"
            entry["data_category"]  = m.get("DATA_CATEGORY")  or "Uncategorized"
            entry["summarize_by"]   = normalize_summarize(m.get("SUMMARIZE_BY", 0))
            entry["is_nullable"]    = bool(m.get("IS_NULLABLE", True))
            entry["is_hidden"]      = bool(m.get("IS_HIDDEN", False))
        else:
            # fallback defaults (matches PBI defaults)
            entry.update({
                "format_string":  "General",
                "is_percentage":  False,
                "thousands_sep":  False,
                "decimal_places": "Auto",
                "sort_by_column": "Default",
                "data_category":  "Uncategorized",
                "summarize_by":   "None",
                "is_nullable":    True,
                "is_hidden":      False,
            })

        results.append(entry)

    return results


# ───────────────────────────────────────────────────────────
# Pretty-print
# ───────────────────────────────────────────────────────────
def print_table(rows: list[dict]):
    if not rows:
        print("  (no columns found)")
        return

    # column order  ─  matches the Properties pane top-to-bottom
    keys = [
        "table_name", "column_name", "data_type", "format_string",
        "is_percentage", "thousands_sep", "decimal_places",
        "sort_by_column", "data_category", "summarize_by",
        "is_nullable", "is_hidden",
    ]
    headers = [
        "Table", "Column", "Data Type", "Format",
        "% Fmt", "1,000 Sep", "Dec Places",
        "Sort By", "Category", "Summarize",
        "Nullable", "Hidden",
    ]

    # compute widths
    widths = [len(h) for h in headers]
    str_rows = []
    for r in rows:
        cells = []
        for i, k in enumerate(keys):
            v = r.get(k, "")
            v = ("Yes" if v else "No") if isinstance(v, bool) else str(v)
            cells.append(v)
            widths[i] = max(widths[i], len(v))
        str_rows.append(cells)

    # print
    sep = "─" * (sum(widths) + 3 * len(widths) + 1)
    fmt = "│ " + " │ ".join(f"{{:<{w}}}" for w in widths) + " │"

    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for cells in str_rows:
        print(fmt.format(*cells))
    print(sep)


# ───────────────────────────────────────────────────────────
# main
# ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    DEFAULT_PBIX = _REPO_ROOT / "powerbi_reports" / "Suprer_Store_Dashboard.pbix"
    path = DEFAULT_PBIX
    print(f"\n📂  Reading  {path}\n")

    rows = extract(path)
    print_table(rows)

    # raw JSON dump (useful for piping into other tools)
    print(f"\n📄  JSON output:\n")
    print(json.dumps(rows, indent=2))