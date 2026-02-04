"""Smoke test: MigrationEngine.migrate_metadata runs end-to-end and writes .lkml files."""

import tempfile
from pathlib import Path

import pytest

from powerbi_to_looker import MigrationEngine


def test_migrate_metadata_stub_runs_and_writes_lkml():
    """Run pipeline with stub metadata; assert no error and at least one .view.lkml and .model.lkml."""
    engine = MigrationEngine()
    with tempfile.TemporaryDirectory() as tmp:
        result = engine.migrate_metadata(
            metadata={"source_system": "powerbi", "datasource_name": "Test"},
            output_dir=tmp,
        )
        assert "files_written" in result
        assert "views" in result
        assert "model" in result
        assert result["output_dir"] == tmp

        files = [Path(p) for p in result["files_written"]]
        view_files = [f for f in files if f.suffix == ".lkml" and ".view." in f.name]
        model_files = [f for f in files if f.suffix == ".lkml" and ".model." in f.name]

        assert len(view_files) >= 1, "Expected at least one .view.lkml"
        assert len(model_files) == 1, "Expected exactly one .model.lkml"

        for p in result["files_written"]:
            assert Path(p).exists(), f"File should exist: {p}"
            assert Path(p).stat().st_size > 0, f"File should be non-empty: {p}"


def test_migrate_file_from_dict_via_temp_json():
    """migrate_file with a JSON path loads file and runs pipeline."""
    engine = MigrationEngine()
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "meta.json"
        json_path.write_text('{"source_system": "powerbi", "datasource_name": "FromFile"}', encoding="utf-8")
        out_dir = Path(tmp) / "out"
        result = engine.migrate_file(str(json_path), str(out_dir))
        assert len(result["files_written"]) >= 2
        assert (out_dir / "model.model.lkml").exists()
