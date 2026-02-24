"""Optional: path sanitization, filename rules."""

import re


def sanitize_report_name_for_looker(report_id: str) -> str:
    """Convert report_id to a Looker-safe folder name (no spaces or special chars).

    Replaces spaces and problematic characters so generator_output folder names
    deploy to Looker without errors. Idempotent for already-clean names.
    """
    if not report_id:
        return "report"
    # Replace spaces and common problematic chars with underscore
    s = report_id.replace(" ", "_").replace("&", "and").replace("'", "").replace('"', "")
    # Strip other non-alphanumeric except underscore and hyphen
    s = re.sub(r"[^\w\-]", "_", s)
    # Collapse multiple underscores and strip leading/trailing underscores
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "report"
