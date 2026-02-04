"""Tests for collector: layout_loader, pbix_loader, merge, collect (with mocks)."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from powerbi_to_looker.collector.layout_loader import load_report_layout
from powerbi_to_looker.collector.merge import merge_api_and_pbix
from powerbi_to_looker.collector.pbix_loader import load_from_pbix
from powerbi_to_looker.collector.powerbi_collector import collect, collect_from_dict_or_path


# Path to a real .pbix in the repo (optional for tests that need it)
REPO_PBIX = Path(__file__).resolve().parents[2] / "powerbi_reports" / "Suprer_Store_Dashboard.pbix"


def test_merge_api_and_pbix_relationships_from_pbix():
    api_result = {
        "workspace_id": "ws1",
        "workspace_name": "WS",
        "report_name": "R1",
        "workspaces": [{"id": "ws1", "name": "WS", "datasets": [{"id": "ds1", "name": "R1", "relationships": []}], "reports": [], "dashboards": []}],
    }
    pbix_result = {
        "relationships": [
            {"FromTableName": "A", "FromColumnName": "id", "ToTableName": "B", "ToColumnName": "id", "Cardinality": "1:1", "CrossFilteringBehavior": "Single", "IsActive": 1},
        ],
        "dax_measures": [],
        "power_query": [],
        "rls": [],
    }
    report_layout = {"source_file": "/x.pbix", "report_level_filters": [], "pages": [], "slicers": []}
    merged = merge_api_and_pbix(api_result, pbix_result, report_layout)
    assert merged["relationships"] == [
        {"fromTable": "A", "fromColumn": "id", "toTable": "B", "toColumn": "id", "cardinality": "1:1", "crossFilteringBehavior": "Single", "isActive": True},
    ]
    assert merged["report_layout"] == report_layout
    assert merged["workspaces"][0]["datasets"][0]["relationships"] == merged["relationships"]


def test_merge_preserves_api_tables_and_columns():
    api_result = {
        "workspace_id": "w",
        "workspace_name": "W",
        "report_name": "R",
        "workspaces": [{"id": "w", "name": "W", "datasets": [{"id": "d", "name": "R", "tables": [{"name": "T1", "columns": [{"name": "c1", "dataType": "String"}]}]}], "reports": [], "dashboards": []}],
    }
    pbix_result = {"relationships": [], "dax_measures": [], "power_query": [], "rls": []}
    report_layout = {"source_file": "", "report_level_filters": [], "pages": [], "slicers": []}
    merged = merge_api_and_pbix(api_result, pbix_result, report_layout)
    assert merged["workspaces"][0]["datasets"][0]["tables"] == [{"name": "T1", "columns": [{"name": "c1", "dataType": "String"}]}]
    assert merged["report_layout"]["pages"] == []


def test_merge_attach_report_layout():
    api_result = {"workspace_id": "w", "workspace_name": "W", "report_name": "R", "workspaces": [{"id": "w", "datasets": [], "reports": [], "dashboards": []}]}
    pbix_result = {"relationships": [], "dax_measures": [], "power_query": [], "rls": []}
    report_layout = {"source_file": "/a.pbix", "report_level_filters": [], "pages": [{"id": "p1", "name": "Page1", "visuals": []}], "slicers": []}
    merged = merge_api_and_pbix(api_result, pbix_result, report_layout)
    assert merged["report_layout"]["pages"] == [{"id": "p1", "name": "Page1", "visuals": []}]


def test_collect_from_dict_or_path_dict():
    meta = {"workspace_id": "x", "report_name": "y"}
    assert collect_from_dict_or_path(meta) == meta


def test_collect_from_dict_or_path_json_file():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        f.write(b'{"report_name": "Test"}')
        path = f.name
    try:
        assert collect_from_dict_or_path(path) == {"report_name": "Test"}
    finally:
        Path(path).unlink(missing_ok=True)


def test_collect_from_dict_or_path_missing_file_raises():
    with pytest.raises(FileNotFoundError, match="Metadata file not found"):
        collect_from_dict_or_path("/nonexistent.json")


def test_collect_pbix_path_must_exist():
    with pytest.raises(FileNotFoundError, match="PBIX file not found"):
        collect("ws1", "R1", {"tenant_id": "t", "client_id": "c", "client_secret": "s"}, "/nonexistent.pbix")


@patch("powerbi_to_looker.collector.powerbi_collector.fetch_report_metadata")
@patch("powerbi_to_looker.collector.powerbi_collector.load_from_pbix")
@patch("powerbi_to_looker.collector.powerbi_collector.load_report_layout")
def test_collect_returns_single_dict(mock_layout, mock_pbix, mock_api):
    mock_api.return_value = {"workspace_id": "w", "workspace_name": "W", "report_name": "R", "workspaces": [{"id": "w", "datasets": [], "reports": [], "dashboards": []}]}
    mock_pbix.return_value = {"relationships": [], "tables": [], "dax_measures": [], "power_query": [], "rls": []}
    mock_layout.return_value = {"source_file": "x", "report_level_filters": [], "pages": [], "slicers": []}
    with tempfile.NamedTemporaryFile(suffix=".pbix", delete=False) as f:
        f.write(b"PK\x03\x04")  # minimal zip
        pbix = f.name
    try:
        result = collect("w", "R", {"tenant_id": "t", "client_id": "c", "client_secret": "s"}, pbix)
        assert isinstance(result, dict)
        assert result["workspace_id"] == "w"
        assert result["report_name"] == "R"
        assert "report_layout" in result
        assert "relationships" in result
    finally:
        Path(pbix).unlink(missing_ok=True)


@pytest.mark.skipif(not REPO_PBIX.exists(), reason="No fixture .pbix in powerbi_reports")
def test_layout_loader_returns_dict_with_pages_and_visuals():
    out = load_report_layout(REPO_PBIX)
    assert "source_file" in out
    assert "pages" in out
    assert "report_level_filters" in out
    assert "slicers" in out
    assert isinstance(out["pages"], list)
    for p in out["pages"]:
        assert "visuals" in p


@pytest.mark.skipif(not REPO_PBIX.exists(), reason="No fixture .pbix in powerbi_reports")
def test_pbix_loader_returns_tables_and_relationships():
    out = load_from_pbix(REPO_PBIX)
    assert "tables" in out
    assert "relationships" in out
    assert isinstance(out["tables"], list)
    assert isinstance(out["relationships"], list)


def test_pbix_loader_missing_file_raises():
    with pytest.raises(FileNotFoundError, match="PBIX file not found"):
        load_from_pbix("/nonexistent.pbix")


@pytest.mark.skipif(not REPO_PBIX.exists(), reason="No fixture .pbix in powerbi_reports")
def test_pbix_loader_relationships_have_expected_keys():
    out = load_from_pbix(REPO_PBIX)
    for rel in out["relationships"][:3]:
        assert "FromTableName" in rel or "fromTable" in str(rel)
        assert "ToTableName" in rel or "ToColumnName" in rel or "FromColumnName" in rel


def test_layout_loader_missing_layout_raises():
    with tempfile.NamedTemporaryFile(suffix=".pbix", delete=False) as f:
        f.write(b"not a zip")
        path = f.name
    try:
        with pytest.raises((ValueError, Exception)):
            load_report_layout(path)
    finally:
        Path(path).unlink(missing_ok=True)
