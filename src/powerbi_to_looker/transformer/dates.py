"""Date/datetime handling for LookML dimensions."""

from typing import Any

from powerbi_to_looker.models.canonical import Field


def is_date_field(data_type: str) -> bool:
    """True if canonical data_type is date or datetime."""
    if not data_type:
        return False
    return (data_type or "").lower() in ("date", "datetime")


def get_date_info(data_type: str, config: dict[str, Any]) -> dict[str, Any] | None:
    """Return LookML date_info (datetype, timeframes) from config when data_type is date/datetime."""
    if not is_date_field(data_type):
        return None
    handling = config.get("date_handling") or {}
    return {
        "datetype": handling.get("datetype", "date"),
        "timeframes": handling.get("timeframes") or ["day", "week", "month", "quarter", "year"],
    }


def dimension_sql_for_date(
    source_column: str | None, field_name: str, config: dict[str, Any]
) -> str:
    """SQL expression for a date dimension. Optional wrapper from config."""
    col = source_column or field_name
    base = f"${{TABLE}}.{col}"
    handling = config.get("date_handling") or {}
    wrapper = handling.get("sql_wrapper")
    if wrapper and "%s" in wrapper:
        return wrapper.replace("%s", base)
    return base
