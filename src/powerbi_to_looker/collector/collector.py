"""Implementation (generic name; Power BI today). Single extract: pbix → folder via pbi-tools."""

import re
from pathlib import Path
from typing import Any

from powerbi_to_looker.collector.extract import extract_to_folder
from powerbi_to_looker.collector.interface import CollectorProtocol
from powerbi_to_looker.collector.powerbi import auth, powerbi_api
from powerbi_to_looker.collector.powerbi.parse import run_pbi_tools


def _resolve_workspace_id(
    workspace_id: str | None,
    workspace_name: str | None,
    credentials: dict[str, str],
) -> str | None:
    """Return workspace_id if set; else resolve workspace_name to id via API. Raise if name given but not found."""
    if workspace_id is not None:
        return workspace_id
    if not workspace_name or not workspace_name.strip():
        return None
    token = auth.get_token(credentials)
    resolved = powerbi_api.get_workspace_id_by_name(workspace_name.strip(), token)
    if resolved is None:
        raise ValueError(f"No workspace found with name: {workspace_name!r}")
    return resolved


# Safe filename for .pbix: no path chars, limit length
_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')
_MAX_FILENAME_LENGTH = 200


def _safe_pbix_filename(report_name: str, report_id: str) -> str:
    """Derive a safe .pbix filename from report name and id."""
    name = (report_name or "report").strip()
    name = _INVALID_FILENAME_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip() or "report"
    if len(name) > _MAX_FILENAME_LENGTH - 10:
        name = name[:_MAX_FILENAME_LENGTH - 10]
    return f"{name}_{report_id[:8]}.pbix"


class Collector(CollectorProtocol):
    """Metadata collector: list, download, extract, collect. All credentials/workspace_id/pbi_tools_exe from caller."""

    def __init__(self, max_workers: int = 1, **kwargs: Any) -> None:
        self.max_workers = max_workers

    def list(
        self,
        *,
        workspace_id: str | None = None,
        workspace_name: str | None = None,
        credentials: dict[str, str],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Return list of report/dataset identifiers. Pass workspace_id or workspace_name (resolved via API)."""
        resolved_id = _resolve_workspace_id(workspace_id, workspace_name, credentials)
        token = auth.get_token(credentials)
        return powerbi_api.list_reports(resolved_id, token)

    def download(
        self,
        item_id: str,
        *,
        workspace_id: str | None = None,
        workspace_name: str | None = None,
        credentials: dict[str, str],
        output_dir: str | Path | None = None,
        report_name: str | None = None,
        **kwargs: Any,
    ) -> bytes | str:
        """Fetch .pbix for one report. Pass workspace_id or workspace_name (resolved via API). Returns bytes or path if output_dir set."""
        resolved_id = _resolve_workspace_id(workspace_id, workspace_name, credentials)
        token = auth.get_token(credentials)
        content = powerbi_api.export_report(item_id, resolved_id, token)
        if output_dir is None:
            return content
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        filename = _safe_pbix_filename(report_name or "report", item_id)
        path = out / filename
        path.write_bytes(content)
        return str(path)

    def parse(
        self,
        pbix_path: str | Path,
        output_path: str | Path,
        pbi_tools_exe: str | Path,
        **kwargs: Any,
    ) -> None:
        """Run pbi-tools extract on .pbix; write to output_path. pbi_tools_exe from caller."""
        run_pbi_tools(pbix_path, output_path, pbi_tools_exe)

    def extract(
        self,
        blob: str | Path,
        output_path: str | Path,
        pbi_tools_exe: str | Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run pbi-tools on .pbix (blob = path); write parsed output to output_path. Exe from orchestrator.
        Returns {"output_path": str}."""
        path = Path(blob)
        if path.suffix.lower() != ".pbix":
            raise ValueError(f"extract requires .pbix path, got {blob!r}")
        out = Path(output_path)
        result_path = extract_to_folder(path, out, pbi_tools_exe)
        return {"output_path": result_path}

    def collect(
        self,
        item_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Download then extract (pbix → folder). Pass credentials, output_dir, pbi_tools_exe, report_name, etc. via kwargs.
        Only runs extract when output_dir and pbi_tools_exe are provided and download returns a path."""
        output_dir = kwargs.get("output_dir")
        report_folder = Path(output_dir) / item_id if output_dir is not None else None
        if report_folder is not None:
            kwargs = {**kwargs, "output_dir": report_folder}
        blob = self.download(item_id, **kwargs)
        pbi_tools_exe = kwargs.get("pbi_tools_exe")
        if isinstance(blob, str) and pbi_tools_exe and report_folder is not None:
            return self.extract(blob, report_folder, pbi_tools_exe, **kwargs)
        return {"output_path": None, "download": blob}
