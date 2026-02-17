"""Tests for parser_normalizer.loader."""

import pytest

from powerbi_to_looker.parser_normalizer.loader import discover_report_folders, load


def test_load_accepts_dict():
    raw = {"model": {"tables": []}, "report": {}}
    assert load(raw) is raw


def test_load_rejects_missing_dir(tmp_path):
    with pytest.raises(FileNotFoundError, match="Not a directory"):
        load(tmp_path / "nonexistent")


def test_discover_report_folders_empty(tmp_path):
    assert discover_report_folders(tmp_path) == []


def test_discover_report_folders_single_report(tmp_path):
    report_dir = tmp_path / "ReportName_id"
    report_dir.mkdir()
    (report_dir / "Model").mkdir()
    (report_dir / "Model" / "database.json").write_text("{}")
    # Root has no Model/database.json, so we discover children
    found = discover_report_folders(tmp_path)
    assert len(found) == 1
    assert found[0][0] == report_dir.name
    assert found[0][1] == report_dir
    # When path is the report folder itself (has Model/database.json), return that folder
    found_root = discover_report_folders(report_dir)
    assert len(found_root) == 1
    assert found_root[0][0] == report_dir.name
    assert found_root[0][1] == report_dir
