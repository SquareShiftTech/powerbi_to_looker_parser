"""Tests for sections_query: build queryState and sortDefinition from prototypeQuery + projections."""

from powerbi_to_looker.parser_normalizer.report_parser.sections_query import (
    build_query_state,
    build_sort_definition,
    build_visual_query,
)


def test_build_query_state_column_and_measure():
    """Projections with Category (column) and Y (aggregation) -> queryState with Column and Measure."""
    projections = {
        "Category": [{"queryRef": "dim_courses.course_type", "active": True}],
        "Y": [
            {"queryRef": "Sum(fact_enrollments.external_marks)"},
            {"queryRef": "Sum(fact_enrollments.internal_marks)"},
        ],
    }
    prototype = {
        "From": [{"Name": "d", "Entity": "dim_courses", "Type": 0}, {"Name": "f", "Entity": "fact_enrollments", "Type": 0}],
        "Select": [
            {"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "course_type"}, "Name": "dim_courses.course_type"},
            {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "external_marks"}}, "Function": 0}, "Name": "Sum(fact_enrollments.external_marks)"},
            {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "internal_marks"}}, "Function": 0}, "Name": "Sum(fact_enrollments.internal_marks)"},
        ],
    }
    out = build_query_state(projections, prototype)
    assert "Category" in out
    assert len(out["Category"]["projections"]) == 1
    assert out["Category"]["projections"][0]["field"]["Column"]["Property"] == "course_type"
    assert out["Category"]["projections"][0]["field"]["Column"]["Expression"]["SourceRef"]["Entity"] == "dim_courses"
    assert "Y" in out
    assert len(out["Y"]["projections"]) == 2
    assert out["Y"]["projections"][0]["field"]["Measure"]["Property"] == "external_marks"
    assert out["Y"]["projections"][1]["field"]["Measure"]["Property"] == "internal_marks"


def test_build_sort_definition_from_order_by():
    """OrderBy with Direction 2 and Aggregation -> sortDefinition Descending."""
    prototype = {
        "From": [{"Name": "f", "Entity": "fact_enrollments"}],
        "OrderBy": [
            {
                "Direction": 2,
                "Expression": {
                    "Aggregation": {
                        "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "external_marks"}},
                        "Function": 0,
                    }
                },
            }
        ],
    }
    out = build_sort_definition(prototype)
    assert out is not None
    assert out["sort"]
    assert out["sort"][0]["direction"] == "Descending"
    assert out["sort"][0]["field"]["Measure"]["Property"] == "external_marks"
    assert out["sort"][0]["field"]["Measure"]["Expression"]["SourceRef"]["Entity"] == "fact_enrollments"


def test_build_visual_query_integration():
    """build_visual_query returns queryState + sortDefinition from config singleVisual."""
    config = {
        "singleVisual": {
            "visualType": "hundredPercentStackedBarChart",
            "projections": {
                "Category": [{"queryRef": "dim_courses.course_type", "active": True}],
                "Y": [{"queryRef": "Sum(fact_enrollments.external_marks)"}],
            },
            "prototypeQuery": {
                "From": [{"Name": "d", "Entity": "dim_courses"}, {"Name": "f", "Entity": "fact_enrollments"}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "course_type"}, "Name": "dim_courses.course_type"},
                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "external_marks"}}, "Function": 0}, "Name": "Sum(fact_enrollments.external_marks)"},
                ],
                "OrderBy": [{"Direction": 2, "Expression": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "external_marks"}}, "Function": 0}}}],
            },
        },
    }
    out = build_visual_query(config)
    assert "queryState" in out
    assert "sortDefinition" in out
    assert "Category" in out["queryState"]
    assert len(out["queryState"]["Category"]["projections"]) == 1
    assert len(out["queryState"]["Y"]["projections"]) == 1
    assert out["sortDefinition"]["sort"][0]["direction"] == "Descending"
