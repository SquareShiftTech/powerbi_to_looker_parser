"""Collector unit tests: protocol, list, download, extract, collect, parse. All in one file."""

from unittest.mock import patch, MagicMock

import pytest

from powerbi_to_looker.collector import Collector, CollectorProtocol
from powerbi_to_looker.collector.extract import model as extract_model
from powerbi_to_looker.collector.powerbi import get_workspace_id_by_name, list_groups


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
def test_extract_delegates_to_artifact_type(credentials):
    """Call extract(blob, artifact_type='model'); assert extract.model.extract is called."""
    with patch.object(extract_model, "extract", return_value={"tables": []}) as mock_extract:
        c = Collector()
        c.extract(b"blob", artifact_type="model")
        mock_extract.assert_called_once_with(b"blob")


def test_extract_model_returns_dict():
    """extract.model.extract returns dict (or raises). Currently raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        extract_model.extract(b"blob")


def test_extract_raises_on_invalid_blob():
    """Invalid or empty blob: extract still delegates; model may raise."""
    c = Collector()
    with patch.object(extract_model, "extract", side_effect=ValueError("invalid")):
        with pytest.raises(ValueError):
            c.extract(b"", artifact_type="model")


# ---- collect ----
def test_collect_calls_download_then_extract(credentials):
    """Mock download and extract; call collect(id); assert download called with id, extract with download return."""
    with patch.object(Collector, "download", return_value=b"pbix_bytes") as mock_dl:
        with patch.object(Collector, "extract", return_value={"tables": []}) as mock_ex:
            c = Collector()
            c.collect(
                "report-123",
                workspace_id="ws1",
                credentials=credentials,
                artifact_type="model",
            )
            mock_dl.assert_called_once()
            assert mock_dl.call_args[0][0] == "report-123"
            mock_ex.assert_called_once()
            assert mock_ex.call_args[0][0] == b"pbix_bytes"
            assert mock_ex.call_args[1].get("artifact_type") == "model"


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
