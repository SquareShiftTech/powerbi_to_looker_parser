"""Integration tests: loader + run_viz for sections-based report (Education)."""

from pathlib import Path

import pytest

from powerbi_to_looker.parser_normalizer.dashboard.orchestrator import run_viz
from powerbi_to_looker.parser_normalizer.loader import load

# Repo root: tests/parser_normalizer/report_parser/test_... -> ../../../ = repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_EDUCATION_PATH = _REPO_ROOT / "parsed_output" / "Education_24b04535"


@pytest.mark.skipif(not _EDUCATION_PATH.is_dir(), reason="Education parsed_output not present")
def test_load_education_produces_pages_and_page_order():
    """Load Education report (sections layout) -> non-empty pages_metadata.pageOrder and pages."""
    raw = load(str(_EDUCATION_PATH))
    assert raw.get("model")
    page_order = raw.get("pages_metadata") or {}
    page_order = page_order.get("pageOrder") or []
    assert len(page_order) >= 1
    pages = raw.get("pages") or {}
    assert len(pages) >= 1
    for pid in page_order:
        assert pid in pages
        assert "page" in pages[pid]
        assert "visuals" in pages[pid]


@pytest.mark.skipif(not _EDUCATION_PATH.is_dir(), reason="Education parsed_output not present")
def test_run_viz_education_produces_dashboard_with_visualizations():
    """Load Education -> run_viz -> dashboard_metadata has pages and visualizations."""
    raw = load(str(_EDUCATION_PATH))
    dashboard_metadata = run_viz(raw, report_id="Education_24b04535")
    assert dashboard_metadata.dashboards
    dash = dashboard_metadata.dashboards[0]
    assert dash.report_id == "Education_24b04535"
    assert len(dash.pages) >= 1
    # Should have at least one visualization from sections visuals
    assert len(dashboard_metadata.visualizations) >= 1
