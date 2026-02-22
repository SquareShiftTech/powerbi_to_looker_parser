"""Field name cleanup and within-view deduplication. Used before building resolution map."""

import re
from typing import Any


def clean_field_name(name: str, reserved_words: set[str] | None = None) -> str:
    """Clean a single field name for Looker: lowercase, spaces/hyphens to underscore, strip special chars.

    - If name starts with a digit, prefix with underscore.
    - If result is in reserved_words, append _field.
    """
    if not name or not isinstance(name, str):
        return ""
    reserved = reserved_words or set()
    # Lowercase
    s = name.lower().strip()
    # Replace spaces and hyphens with underscore
    s = s.replace(" ", "_").replace("-", "_")
    # Strip all special characters except underscore
    s = re.sub(r"[^a-z0-9_]", "", s)
    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return ""
    # Leading digit -> prefix underscore
    if s[0].isdigit():
        s = "_" + s
    # Reserved word -> append _field
    if s in reserved:
        s = s + "_field"
    return s


def deduplicate_field_names(
    fields: list[dict[str, Any]],
    name_key: str = "name",
    id_key: str = "id",
    reserved_words: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Assign unique field_name to each field. First occurrence keeps clean name; duplicates get _ + last 4 of UUID.

    Expects each item to have name_key (original name) and id_key (UUID string).
    Adds 'field_name' to each item (cleaned, then deduplicated). Mutates and returns the same list.
    """
    reserved = reserved_words or set()
    seen: dict[str, int] = {}
    for f in fields:
        raw = f.get(name_key) or ""
        fid = f.get(id_key) or ""
        base = clean_field_name(raw, reserved)
        if not base:
            f["field_name"] = base
            continue
        suffix = ""
        if base in seen:
            seen[base] += 1
            # Use last 4 chars of UUID (strip hyphens first)
            uid = (fid or "").replace("-", "")[-4:] if fid else str(seen[base])
            suffix = "_" + uid.lower()
        else:
            seen[base] = 0
        f["field_name"] = base + suffix
    return fields
