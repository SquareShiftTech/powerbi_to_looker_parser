"""Collector unit tests: protocol, list, download, extract, collect, parse, run_pbi_tools. All in one file."""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from powerbi_to_looker.collector import Collector, CollectorProtocol
from powerbi_to_looker.collector.powerbi import get_workspace_id_by_name, list_groups
from powerbi_to_looker.collector.powerbi.parse import run_pbi_tools


# ---- Protocol ----
def test_collector_implements_protocol():
    """Collector has list, download, extract, collect and is usable as CollectorProtocol."""
    c = Collector()
    assert hasattr(c, "list")
    assert hasattr(c, "download")
    assert hasattr(c, "extract")
    assert hasattr(c, "collect")
    assert callable(c.list)
    assert callable(c.download)
    assert callable(c.extract)
    assert callable(c.collect)


# ---- list ----
def test_list_requires_credentials_and_workspace_id(credentials):
    """list() accepts credentials; with valid creds and workspace_id returns from API (mocked)."""
    with patch("powerbi_to_looker.collector.collector.auth.get_token", return_value="token"):
        with patch(
            "powerbi_to_looker.collector.collector.powerbi_api.list_reports",
            return_value=[{"id": "r1", "name": "R1", "datasetId": "d1"}],
        ):
            c = Collector()
            out = c.list(workspace_id="ws1", credentials=credentials)
            assert isinstance(out, list)
            assert len(out) == 1
            assert out[0]["id"] == "r1"
            assert out[0]["name"] == "R1"


def test_list_returns_list_of_dicts(credentials, sample_list_response):
    """Mock API response; assert return type and that each item has id, name."""
    with patch("powerbi_to_looker.collector.collector.auth.get_token", return_value="token"):
        with patch(
            "powerbi_to_looker.collector.collector.powerbi_api.list_reports",
            return_value=sample_list_response["value"],
        ):
            c = Collector()
            out = c.list(workspace_id="ws1", credentials=credentials)
            assert isinstance(out, list)
            for item in out:
                assert isinstance(item, dict)
                assert "id" in item
                assert "name" in item


# ---- powerbi_api: list_groups / get_workspace_id_by_name ----
def test_list_groups_returns_groups_from_api():
    """list_groups calls GET .../groups and returns value array."""
    with patch("powerbi_to_looker.collector.powerbi.powerbi_api.requests.get") as mget:
        mget.return_value.json.return_value = {
            "value": [
                {"id": "g1", "name": "Workspace A"},
                {"id": "g2", "name": "Powerbi-POC"},
            ]
        }
        mget.return_value.raise_for_status = MagicMock()
        mget.return_value.status_code = 200
        out = list_groups("token")
        assert len(out) == 2
        assert out[0]["id"] == "g1" and out[0]["name"] == "Workspace A"
        assert out[1]["id"] == "g2" and out[1]["name"] == "Powerbi-POC"


def test_get_workspace_id_by_name_returns_id_when_found():
    """get_workspace_id_by_name finds group by case-insensitive name and returns id."""
    with patch("powerbi_to_looker.collector.powerbi.powerbi_api.list_groups") as mlist:
        mlist.return_value = [
            {"id": "g1", "name": "Workspace A"},
            {"id": "g2", "name": "Powerbi-POC"},
        ]
        assert get_workspace_id_by_name("Powerbi-POC", "token") == "g2"
        assert get_workspace_id_by_name("powerbi-poc", "token") == "g2"
        assert get_workspace_id_by_name("  Powerbi-POC  ", "token") == "g2"


def test_get_workspace_id_by_name_returns_none_when_not_found():
    """get_workspace_id_by_name returns None when no matching name."""
    with patch("powerbi_to_looker.collector.powerbi.powerbi_api.list_groups") as mlist:
        mlist.return_value = [{"id": "g1", "name": "Other"}]
        assert get_workspace_id_by_name("Nonexistent", "token") is None


# ---- download ----
def test_download_returns_bytes_or_path(credentials):
    """Mock Export API; assert return is bytes when no output_dir, or str path when output_dir set."""
    with patch("powerbi_to_looker.collector.collector.auth.get_token", return_value="token"):
        with patch(
            "powerbi_to_looker.collector.collector.powerbi_api.export_report",
            return_value=b"pkzip_content",
        ):
            c = Collector()
            out = c.download("report-id", workspace_id="ws1", credentials=credentials)
            assert isinstance(out, bytes)
            assert out == b"pkzip_content"


def test_download_writes_to_output_dir_and_returns_path(credentials, tmp_path):
    """When output_dir is set, download writes .pbix and returns path."""
    with patch("powerbi_to_looker.collector.collector.auth.get_token", return_value="token"):
        with patch(
            "powerbi_to_looker.collector.collector.powerbi_api.export_report",
            return_value=b"pkzip_content",
        ):
            c = Collector()
            out = c.download(
                "report-id",
                workspace_id="ws1",
                credentials=credentials,
                output_dir=tmp_path,
                report_name="My Report",
            )
            assert isinstance(out, str)
            assert out.endswith(".pbix")
            assert (tmp_path / out.split("/")[-1].split("\\")[-1]).exists()


# ---- extract ----
def test_extract_calls_extract_to_folder_and_returns_output_path(tmp_path):
    """extract(pbix_path, output_path, pbi_tools_exe) calls extract_to_folder and returns dict with output_path."""
    pbix = tmp_path / "report.pbix"
    pbix.write_bytes(b"dummy")
    out_dir = tmp_path / "out"
    with patch("powerbi_to_looker.collector.collector.extract_to_folder", return_value=str(out_dir.resolve())) as mock_extract:
        c = Collector()
        result = c.extract(str(pbix), str(out_dir), "pbi-tools.exe")
        mock_extract.assert_called_once_with(pbix, out_dir, "pbi-tools.exe")
        assert result == {"output_path": str(out_dir.resolve())}


def test_extract_raises_on_non_pbix_path():
    """extract requires .pbix path; raises ValueError for other paths."""
    c = Collector()
    with pytest.raises(ValueError, match=".pbix path"):
        c.extract("/some/file.json", "/out", "pbi-tools.exe")


# ---- collect ----
def test_collect_calls_download_then_extract_when_output_dir_and_exe_provided(credentials, tmp_path):
    """When output_dir and pbi_tools_exe provided, collect calls download then extract with pbix path and output_path."""
    report_folder = tmp_path / "report-123"
    pbix_path = str(report_folder / "Report_abc12345.pbix")
    with patch.object(Collector, "download", return_value=pbix_path) as mock_dl:
        with patch.object(Collector, "extract", return_value={"output_path": str(report_folder)}) as mock_ex:
            c = Collector()
            c.collect(
                "report-123",
                workspace_id="ws1",
                credentials=credentials,
                output_dir=tmp_path,
                pbi_tools_exe="pbi-tools.exe",
            )
            mock_dl.assert_called_once()
            assert mock_dl.call_args[0][0] == "report-123"
            assert mock_dl.call_args[1].get("output_dir") == report_folder
            mock_ex.assert_called_once()
            assert mock_ex.call_args[0][0] == pbix_path
            assert mock_ex.call_args[0][1] == report_folder
            assert mock_ex.call_args[0][2] == "pbi-tools.exe"


def test_collect_returns_download_only_when_no_pbi_tools_exe(credentials):
    """When pbi_tools_exe not provided, collect does not call extract; returns download result."""
    with patch.object(Collector, "download", return_value="/path/to/report.pbix") as mock_dl:
        with patch.object(Collector, "extract") as mock_ex:
            c = Collector()
            result = c.collect(
                "report-123",
                workspace_id="ws1",
                credentials=credentials,
                output_dir="/out",
            )
            mock_dl.assert_called_once()
            mock_ex.assert_not_called()
            assert result["output_path"] is None
            assert result["download"] == "/path/to/report.pbix"


# ---- parse ----
def test_parse_receives_pbi_tools_exe_from_caller(tmp_path):
    """Parse method accepts pbi_tools_exe; when exe missing, raises FileNotFoundError."""
    c = Collector()
    with patch("powerbi_to_looker.collector.collector.run_pbi_tools") as mock_run:
        c.parse(tmp_path / "x.pbix", tmp_path, "/nonexistent/pbi-tools.exe")
        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert str(args[2]) == "/nonexistent/pbi-tools.exe"


def test_parse_runs_subprocess_with_given_exe(tmp_path):
    """Mock subprocess; call parse(..., pbi_tools_exe='...'); assert run_pbi_tools called with exe path."""
    c = Collector()
    with patch("powerbi_to_looker.collector.collector.run_pbi_tools") as mock_run:
        c.parse(tmp_path / "a.pbix", tmp_path, "pbi-tools.exe")
        mock_run.assert_called_once_with(
            tmp_path / "a.pbix",
            tmp_path,
            "pbi-tools.exe",
        )


# ---- run_pbi_tools (powerbi/parse.py) ----
def test_run_pbi_tools_success_uses_extract_folder_and_model_serialization_raw(tmp_path):
    """run_pbi_tools calls subprocess with extract, -extractFolder, -modelSerialization Raw."""
    pbix = tmp_path / "report.pbix"
    pbix.write_bytes(b"x")
    out = tmp_path / "out"
    exe = tmp_path / "pbi-tools.exe"
    exe.write_bytes(b"x")
    with patch("powerbi_to_looker.collector.powerbi.parse.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_pbi_tools(pbix, out, exe)
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == str(exe)
        assert call_args[1] == "extract"
        assert call_args[2] == str(pbix)
        assert "-extractFolder" in call_args
        assert str(out) in call_args
        assert "-modelSerialization" in call_args
        assert "Raw" in call_args


def test_run_pbi_tools_raises_called_process_error_on_nonzero_exit(tmp_path):
    """When pbi-tools exits non-zero, run_pbi_tools raises CalledProcessError with stderr and stdout."""
    pbix = tmp_path / "report.pbix"
    pbix.write_bytes(b"x")
    out = tmp_path / "out"
    exe = tmp_path / "pbi-tools.exe"
    exe.write_bytes(b"x")
    with patch("powerbi_to_looker.collector.powerbi.parse.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="out", stderr="pbi-tools error message")
        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            run_pbi_tools(pbix, out, exe)
        e = exc_info.value
        assert e.returncode == 1
        assert e.stderr == "pbi-tools error message"
        assert e.stdout == "out"


def test_run_pbi_tools_raises_file_not_found_for_missing_exe(tmp_path):
    """run_pbi_tools raises FileNotFoundError when exe path does not exist."""
    pbix = tmp_path / "report.pbix"
    pbix.write_bytes(b"x")
    out = tmp_path / "out"
    with pytest.raises(FileNotFoundError, match="pbi-tools executable not found"):
        run_pbi_tools(pbix, out, tmp_path / "nonexistent.exe")


def test_run_pbi_tools_raises_file_not_found_for_missing_pbix(tmp_path):
    """run_pbi_tools raises FileNotFoundError when .pbix path does not exist."""
    exe = tmp_path / "pbi-tools.exe"
    exe.write_bytes(b"x")
    with pytest.raises(FileNotFoundError, match="PBIX file not found"):
        run_pbi_tools(tmp_path / "missing.pbix", tmp_path / "out", exe)


def test_parse_failure_includes_exit_code_stderr_stdout_in_failed_entry(tmp_path):
    """When parse raises CalledProcessError, script-style handling includes exit_code, stderr, stdout in failed item."""
    (tmp_path / "report.pbix").write_bytes(b"x")
    parsed_dir = tmp_path / "parsed"
    collector = Collector()
    err = subprocess.CalledProcessError(1, ["pbi-tools"], output="pbi-tools stdout", stderr="pbi-tools stderr")
    with patch.object(collector, "parse", side_effect=err):
        parse_failed: list[dict] = []
        for pbix_path in sorted(tmp_path.glob("*.pbix")):
            try:
                collector.parse(pbix_path, parsed_dir / pbix_path.stem, "pbi-tools.exe")
            except subprocess.CalledProcessError as e:
                parse_failed.append({
                    "pbix": str(pbix_path),
                    "error": str(e),
                    "exit_code": e.returncode,
                    "stderr": (e.stderr or "").strip() or None,
                    "stdout": (e.stdout or "").strip() or None,
                })
        assert len(parse_failed) == 1
        assert parse_failed[0]["exit_code"] == 1
        assert parse_failed[0]["stderr"] == "pbi-tools stderr"
        assert parse_failed[0]["stdout"] == "pbi-tools stdout"
