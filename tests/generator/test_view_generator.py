"""Tests for generator view output."""

import pytest
from pathlib import Path

from powerbi_to_looker.models.artifact import (
    ArtifactField,
    ArtifactView,
    SemanticLayerArtifact,
    ConversionSummary,
    ArtifactExplore,
)
from powerbi_to_looker.generator.writer import write


@pytest.fixture
def minimal_artifact():
    """Minimal artifact with one view and one dimension, one measure."""
    view = ArtifactView(
        view_name="sales",
        label="Sales",
        source_table="sales",
        view_type="physical",
        sql_table_name="`proj.sc.sales`",
        derived_table_sql=None,
        fields=[
            ArtifactField(
                field_name="revenue",
                original_name="Revenue",
                field_type="dimension",
                looker_type="number",
                label="Revenue",
                description=None,
                sql="${TABLE}.revenue",
                value_format=None,
                timeframes=None,
                hidden=False,
                tags=[],
                conversion_status="auto",
                message=None,
                original_formula=None,
                bq_formula=None,
            ),
            ArtifactField(
                field_name="total_revenue",
                original_name="Total Revenue",
                field_type="measure",
                looker_type="sum",
                label="Total Revenue",
                description=None,
                sql="${TABLE}.revenue",
                value_format="usd",
                timeframes=None,
                hidden=False,
                tags=[],
                conversion_status="auto",
                message=None,
                original_formula="SUM(sales[revenue])",
                bq_formula="SUM(sales.revenue)",
            ),
        ],
    )
    return SemanticLayerArtifact(
        project_name="test_project",
        database="proj",
        schema="sc",
        views=[view],
        explores=[ArtifactExplore(explore_name="sales", label="Sales", joins=[])],
        conversion_summary=ConversionSummary(total_fields=2, auto=2, partial=0, manual=0),
    )


def test_one_view_file_per_view(minimal_artifact, tmp_path):
    write(minimal_artifact, tmp_path)
    view_files = list((tmp_path / "views").glob("*.view.lkml"))
    assert len(view_files) == len(minimal_artifact.views)


def test_view_file_contains_correct_view_name(minimal_artifact, tmp_path):
    write(minimal_artifact, tmp_path)
    content = (tmp_path / "views" / "sales.view.lkml").read_text()
    assert "view: sales" in content


def test_measure_has_two_step_pattern(minimal_artifact, tmp_path):
    write(minimal_artifact, tmp_path)
    content = (tmp_path / "views" / "sales.view.lkml").read_text()
    assert "dimension: total_revenue_measure" in content
    assert "measure: total_revenue" in content
    assert "total_revenue_measure" in content


def test_original_dax_comment_present(minimal_artifact, tmp_path):
    write(minimal_artifact, tmp_path)
    content = (tmp_path / "views" / "sales.view.lkml").read_text()
    assert "# Original DAX:" in content
