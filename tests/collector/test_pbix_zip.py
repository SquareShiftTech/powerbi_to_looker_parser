"""Tests for Report extraction from .pbix zip fallback."""

import zipfile
from pathlib import Path

import pytest

from powerbi_to_looker.collector.powerbi.pbix_zip import extract_report_from_pbix


def test_extract_report_from_pbix_extracts_report_entries(tmp_path: Path) -> None:
    """When .pbix zip has Report/ entries, they are extracted into out_folder."""
    pbix = tmp_path / "report.pbix"
    with zipfile.ZipFile(pbix, "w") as zf:
        zf.writestr("Report/Layout", '{"name":"Layout"}')
        zf.writestr("DataModelSchema", "ignored")
        zf.writestr("Report/Sections/section1/config.json", "{}")
    out = tmp_path / "parsed"
    out.mkdir()

    n = extract_report_from_pbix(pbix, out)

    assert n == 2
    assert (out / "Report" / "Layout").read_text() == '{"name":"Layout"}'
    assert (out / "Report" / "Sections" / "section1" / "config.json").read_text() == "{}"
    assert not (out / "DataModelSchema").exists()


def test_extract_report_from_pbix_missing_file_raises(tmp_path: Path) -> None:
    """Missing .pbix path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found"):
        extract_report_from_pbix(tmp_path / "missing.pbix", tmp_path)
