"""Orchestrates the migration pipeline: Collector -> Canonical -> Transformer -> Generator."""

from pathlib import Path
from typing import Any

from powerbi_to_looker.collector import collect, collect_from_dict_or_path
from powerbi_to_looker.canonical import build_metadata_model
from powerbi_to_looker.transformer import to_lookml_terms
from powerbi_to_looker.generator import generate


class MigrationEngine:
    """Runs the full Power BI to LookML semantic layer migration."""

    def _run_pipeline(self, raw: dict[str, Any], output_dir: str) -> dict[str, Any]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        canonical_model = build_metadata_model(raw)
        lookml_terms = to_lookml_terms(canonical_model)
        files_written = generate(lookml_terms, str(output_path))
        return {
            "views": lookml_terms.get("views", []),
            "model": lookml_terms.get("model"),
            "output_dir": str(output_path),
            "files_written": files_written,
        }

    def migrate(
        self,
        workspace_id: str,
        report_name: str,
        credentials: dict[str, str],
        pbix_path: str | Path,
        output_dir: str,
        *,
        scan_timeout: int = 300,
    ) -> dict[str, Any]:
        """Run full pipeline: collect from API + .pbix, then canonical -> transformer -> generator.

        Args:
            workspace_id: Power BI workspace id.
            report_name: Report/dataset name.
            credentials: tenant_id, client_id, client_secret (or access_token).
            pbix_path: Path to .pbix file.
            output_dir: Directory to write .view.lkml and .model.lkml.
            scan_timeout: Scanner API timeout in seconds.

        Returns:
            Result dict with views, model, output_dir, files_written.
        """
        raw = collect(workspace_id, report_name, credentials, pbix_path, scan_timeout=scan_timeout)
        return self._run_pipeline(raw, output_dir)

    def migrate_metadata(self, metadata: dict, output_dir: str) -> dict[str, Any]:
        """Run pipeline from in-memory Power BI metadata (e.g. from API or JSON).

        Args:
            metadata: Raw Power BI metadata dict.
            output_dir: Directory to write .view.lkml and .model.lkml.

        Returns:
            Result dict with keys: views, model, output_dir, files_written.
        """
        raw = collect_from_dict_or_path(metadata)
        return self._run_pipeline(raw, output_dir)

    def migrate_file(self, path: str, output_dir: str) -> dict[str, Any]:
        """Run pipeline from a JSON metadata file path.

        Args:
            path: Path to Power BI metadata JSON file.
            output_dir: Directory to write LookML files.

        Returns:
            Same as migrate_metadata.
        """
        raw = collect_from_dict_or_path(path)
        return self._run_pipeline(raw, output_dir)
