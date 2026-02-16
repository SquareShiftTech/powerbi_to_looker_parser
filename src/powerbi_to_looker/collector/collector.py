"""Implementation (generic name; Power BI today). Delegates to extract.model, extract.report, extract.dashboard."""

import re
from pathlib import Path
from typing import Any

from powerbi_to_looker.collector.interface import CollectorProtocol
from powerbi_to_looker.collector.powerbi import auth, powerbi_api
from powerbi_to_looker.collector.powerbi.parse import run_pbi_tools
from powerbi_to_looker.collector.extract import model as extract_model, report as extract_report, dashboard as extract_dashboard

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
        credentials: dict[str, str],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Return list of report/dataset identifiers. credentials and workspace_id from caller."""
        token = auth.get_token(credentials)
        return powerbi_api.list_reports(workspace_id, token)

    def download(
        self,
        item_id: str,
        *,
        workspace_id: str | None = None,
        credentials: dict[str, str],
        output_dir: str | Path | None = None,
        report_name: str | None = None,
        **kwargs: Any,
    ) -> bytes | str:
        """Fetch .pbix for one report. Returns bytes or path if output_dir set. Raises on API error."""
        token = auth.get_token(credentials)
        content = powerbi_api.export_report(item_id, workspace_id, token)
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
        blob: bytes | str,
        artifact_type: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Turn blob into structured metadata. Delegates to extract.model/report/dashboard by artifact_type."""
        if artifact_type == "model":
            return extract_model.extract(blob)
        if artifact_type == "report":
            return extract_report.extract(blob)
        if artifact_type == "dashboard":
            return extract_dashboard.extract(blob)
        # Default to model when not specified
        return extract_model.extract(blob)

    def collect(
        self,
        item_id: str,
        artifact_type: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """download then extract. Pass credentials, workspace_id, etc. via kwargs."""
        blob = self.download(item_id, **kwargs)
        return self.extract(blob, artifact_type=artifact_type, **kwargs)
