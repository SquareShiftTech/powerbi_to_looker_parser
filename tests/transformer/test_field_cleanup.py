"""Tests for field name cleanup and deduplication."""

import pytest

from powerbi_to_looker.transformer.semantic.field_cleanup import (
    clean_field_name,
    deduplicate_field_names,
)


def test_spaces_to_underscores():
    assert clean_field_name("Sales Amount") == "sales_amount"


def test_hyphens_to_underscores():
    assert clean_field_name("Sales-Amount") == "sales_amount"


def test_uppercase_to_lowercase():
    assert clean_field_name("CustomerID") == "customerid"


def test_special_chars_stripped():
    # Strip special chars; ($) removed -> "revenue"
    assert clean_field_name("Revenue ($)") == "revenue"


def test_leading_digit_prefixed():
    assert clean_field_name("2024_sales") == "_2024_sales"


def test_reserved_word_appended():
    reserved = {"date", "count", "sum"}
    assert clean_field_name("date", reserved) == "date_field"
    assert clean_field_name("count", reserved) == "count_field"
    assert clean_field_name("sum", reserved) == "sum_field"


def test_already_clean_passes_through():
    assert clean_field_name("customer_id") == "customer_id"


def test_duplicate_names_get_uuid_suffix():
    fields = [
        {"name": "Revenue", "id": "aaa-bbb-ccc-4492"},
        {"name": "revenue", "id": "xxx-yyy-zzz-dc3b"},
    ]
    result = deduplicate_field_names(fields)
    # First occurrence keeps clean name; second gets _ + last 4 of UUID
    assert result[0]["field_name"] == "revenue"
    assert result[1]["field_name"] == "revenue_dc3b"
