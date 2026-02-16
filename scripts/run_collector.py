"""Integration: full collector flow (list -> download -> parse). One folder per report; track success/failed.

Env (optional if using defaults): PBI_TENANT_ID, PBI_CLIENT_ID, PBI_CLIENT_SECRET.
Workspace: PBI_WORKSPACE_ID (id) or PBI_WORKSPACE_NAME (name; resolved via Groups API).
Optional: PBI_TOOLS_EXE (path to pbi-tools executable; needed for parse step).
CLI: --output-dir, --list-only, --download-only, --workspace-name, --skip-name-contains.

If env is not set, script falls back to archive defaults for local testing.
Some reports (e.g. "Dashboard Usage Metrics Report") are not exportable and return 404; use --skip-name-contains to skip them by name.
Run from repo root: uv run python scripts/run_collector.py [--output-dir ./out] [--list-only | --download-only] [--workspace-name "My Workspace"]
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure package is on path when run as script
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from powerbi_to_looker.collector import Collector, CollectorProtocol  # noqa: E402
from powerbi_to_looker.collector.powerbi import get_token, get_workspace_id_by_name  # noqa: E402

# Fallback from archive for local testing (env PBI_* overrides these)
DEFAULT_CREDENTIALS = {
    "tenant_id": "a812643e-dcca-45b3-bde2-ef646799d843",
    "client_id": "8ee9bf2b-e49f-4cb4-90f8-bfd9fd47af17",
    "client_secret": "MD48Q~7nQTc2f8oVsgn.Y3q9osWc3~4rkQGtVc2g",
}
DEFAULT_WORKSPACE_ID = "5945fc8b-1fb7-48a5-873a-0a35ea442166"  # Powerbi-POC
DEFAULT_WORKSPACE_NAME = "Orders & Sales"


def _credentials() -> dict[str, str]:
    if os.environ.get("PBI_ACCESS_TOKEN"):
        return {"access_token": os.environ["PBI_ACCESS_TOKEN"]}
    tenant = os.environ.get("PBI_TENANT_ID") or DEFAULT_CREDENTIALS["tenant_id"]
    client = os.environ.get("PBI_CLIENT_ID") or DEFAULT_CREDENTIALS["client_id"]
    secret = os.environ.get("PBI_CLIENT_SECRET") or DEFAULT_CREDENTIALS["client_secret"]
    if not secret:
        raise SystemExit(
            "Set PBI_CLIENT_SECRET (or PBI_TENANT_ID, PBI_CLIENT_ID, PBI_CLIENT_SECRET) for API auth."
        )
    return {"tenant_id": tenant, "client_id": client, "client_secret": secret}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Integration: list reports, download .pbix (one folder per report), run pbi-tools parse."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("collector_output"),
        help="Base directory for downloads (default: collector_output); each report in output_dir/<report_id>/",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list reports and print JSON; no download or parse.",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="List and download .pbix only; do not run pbi-tools parse.",
    )
    parser.add_argument(
        "--workspace-name",
        type=str,
        default=None,
        help="Power BI workspace name (resolved to id via API). Overridden by PBI_WORKSPACE_ID.",
    )
    parser.add_argument(
        "--skip-name-contains",
        type=str,
        action="append",
        default=[],
        metavar="TEXT",
        help="Skip download for reports whose name contains TEXT (case-insensitive). Can be repeated. E.g. --skip-name-contains 'Usage Metrics'.",
    )
    args = parser.parse_args()

    credentials = _credentials()
    workspace_id = os.environ.get("PBI_WORKSPACE_ID")
    workspace_name = args.workspace_name or os.environ.get("PBI_WORKSPACE_NAME")
    if not workspace_id and workspace_name:
        token = get_token(credentials)
        workspace_id = get_workspace_id_by_name(workspace_name, token)
        if not workspace_id:
            raise SystemExit(f"No workspace found with name: {workspace_name!r}")
    if not workspace_id:
        workspace_id = DEFAULT_WORKSPACE_ID

    collector: CollectorProtocol = Collector()
    reports = collector.list(workspace_id=workspace_id, credentials=credentials)
    print(json.dumps({"workspace_id": workspace_id, "count": len(reports), "reports": reports}, indent=2))

    if args.list_only:
        return

    pbi_tools_exe = os.environ.get("PBI_TOOLS_EXE")
    if not args.download_only and not pbi_tools_exe:
        print("PBI_TOOLS_EXE not set; skipping parse step.", file=sys.stderr)

    output_dir = args.output_dir.resolve()
    successful = []
    failed = []
    skipped = []
    skip_substrings = [s.lower() for s in args.skip_name_contains]
    for r in reports:
        report_id = r.get("id")
        name = r.get("name") or "report"
        if not report_id:
            failed.append({"name": name, "error": "missing id"})
            continue
        if skip_substrings and any(sub in name.lower() for sub in skip_substrings):
            skipped.append({"id": report_id, "name": name})
            continue
        report_folder = output_dir / report_id
        report_folder.mkdir(parents=True, exist_ok=True)
        try:
            path_or_bytes = collector.download(
                report_id,
                workspace_id=workspace_id,
                credentials=credentials,
                output_dir=report_folder,
                report_name=name,
            )
            successful.append({"id": report_id, "name": name, "path": str(path_or_bytes)})
            if not args.download_only and pbi_tools_exe:
                pbix_path = path_or_bytes if isinstance(path_or_bytes, str) else report_folder
                collector.parse(pbix_path, report_folder, pbi_tools_exe)
        except Exception as e:
            failed.append({"id": report_id, "name": name, "error": str(e)})

    print("Successful:", len(successful))
    print("Failed:", len(failed))
    if skipped:
        print("Skipped (by name):", len(skipped))
        print(json.dumps({"skipped": skipped}, indent=2))
    if failed:
        print(json.dumps({"failed": failed}, indent=2))


if __name__ == "__main__":
    main()
