"""Integration: one folder for .pbix (downloaded or from other sources), then parse all.

Step 1 — List and download (download=True when Power BI API creds + workspace given):
  Store .pbix in a single local folder (flat, no report_id). Folder = --output-dir.

Step 2 — Parse:
  Read all .pbix from the folder; write parsed output to --parsed-output-dir, one subdir per .pbix.
  Uses pbi-tools -extractFolder, -modelSerialization Raw.

Env (for step 1): PBI_TENANT_ID, PBI_CLIENT_ID, PBI_CLIENT_SECRET; PBI_WORKSPACE_ID or PBI_WORKSPACE_NAME.
Optional: PBI_TOOLS_EXE (default: repo pbi-tools/pbi-tools.exe or pbi-tools/<ver>/pbi-tools.exe).
CLI: --output-dir, --parsed-output-dir, --list-only, --download-only, --workspace-name, --skip-name-contains, --no-download.

Run from repo root: uv run python scripts/run_collector.py [--no-download] [--output-dir collector_output] [--parsed-output-dir parsed_output]
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from powerbi_to_looker.collector import Collector, CollectorProtocol  # noqa: E402
from powerbi_to_looker.collector.powerbi.pbix_zip import extract_report_from_pbix  # noqa: E402


def _default_pbi_tools_exe() -> str | None:
    """Default pbi-tools exe: repo pbi-tools folder (versioned subdir or pbi-tools.exe at root)."""
    candidates = [
        _REPO_ROOT / "pbi-tools" / "pbi-tools.exe",
        _REPO_ROOT / "pbi-tools" / "pbi-tools.1.2.0" / "pbi-tools.exe",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    pbi_tools_dir = _REPO_ROOT / "pbi-tools"
    if pbi_tools_dir.exists():
        for d in pbi_tools_dir.iterdir():
            exe = d / "pbi-tools.exe"
            if exe.exists():
                return str(exe)
    return None


DEFAULT_CREDENTIALS = {
    "tenant_id": "a812643e-dcca-45b3-bde2-ef646799d843",
    "client_id": "8ee9bf2b-e49f-4cb4-90f8-bfd9fd47af17",
    "client_secret": "MD48Q~7nQTc2f8oVsgn.Y3q9osWc3~4rkQGtVc2g",
}
DEFAULT_WORKSPACE_NAME = "P2L_Devop"

# Windows path length; shorten parsed folder name when stem is long
_MAX_STEM_LEN = 35


def _short_parsed_folder_name(stem: str) -> str:
    """Shorten stem for parsed output folder to avoid path-too-long (e.g. DirectoryNotFoundException)."""
    if len(stem) <= _MAX_STEM_LEN:
        return stem
    return stem[: _MAX_STEM_LEN - 9] + "_" + stem[-8:]


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


def _run_step1_download(
    collector: CollectorProtocol,
    output_dir: Path,
    workspace_id: str | None,
    workspace_name: str | None,
    credentials: dict[str, str],
    skip_name_contains: list[str],
    download_only: bool,
) -> tuple[list[dict], list[dict], list[dict]]:
    """List and download .pbix into output_dir (flat, no report_id). Return successful, failed, skipped."""
    reports = collector.list(
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        credentials=credentials,
    )
    successful: list[dict] = []
    failed: list[dict] = []
    skipped: list[dict] = []
    skip_substrings = [s.lower() for s in skip_name_contains]
    output_dir.mkdir(parents=True, exist_ok=True)

    for r in reports:
        report_id = r.get("id")
        name = r.get("name") or "report"
        if not report_id:
            failed.append({"name": name, "error": "missing id"})
            continue
        if skip_substrings and any(sub in name.lower() for sub in skip_substrings):
            skipped.append({"id": report_id, "name": name})
            continue
        try:
            path_or_bytes = collector.download(
                report_id,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                credentials=credentials,
                output_dir=output_dir,
                report_name=name,
            )
            if isinstance(path_or_bytes, str):
                pbix_path = Path(path_or_bytes)
                if pbix_path.exists() and pbix_path.stat().st_size > 0:
                    successful.append({"id": report_id, "name": name, "path": path_or_bytes})
                else:
                    failed.append({"id": report_id, "name": name, "error": "file missing or empty"})
            else:
                failed.append({"id": report_id, "name": name, "error": "download returned bytes (no output_dir?)"})
        except Exception as e:
            failed.append({"id": report_id, "name": name, "error": str(e)})

    return successful, failed, skipped


def _run_step2_parse_all(
    collector: CollectorProtocol,
    pbix_dir: Path,
    parsed_output_dir: Path,
    pbi_tools_exe: str | None,
) -> tuple[list[dict], list[dict]]:
    """Find all .pbix in pbix_dir; parse each to parsed_output_dir/<short_stem>/."""
    parsed_ok: list[dict] = []
    parse_failed: list[dict] = []
    if not pbi_tools_exe:
        return parsed_ok, parse_failed

    parsed_output_dir.mkdir(parents=True, exist_ok=True)
    pbix_files = sorted(pbix_dir.glob("*.pbix"))
    for pbix_path in pbix_files:
        if not pbix_path.is_file():
            continue
        folder_name = _short_parsed_folder_name(pbix_path.stem)
        out_folder = (parsed_output_dir / folder_name).resolve()
        out_folder.mkdir(parents=True, exist_ok=True)
        try:
            collector.parse(pbix_path, out_folder, pbi_tools_exe)
            if not (out_folder / "Report").exists():
                extract_report_from_pbix(pbix_path, out_folder)
            parsed_ok.append({"pbix": str(pbix_path), "output_path": str(out_folder)})
        except subprocess.CalledProcessError as e:
            parse_failed.append({
                "pbix": str(pbix_path),
                "error": str(e),
                "exit_code": e.returncode,
                "stderr": (e.stderr or "").strip() or None,
                "stdout": (e.stdout or "").strip() or None,
            })
        except Exception as e:
            parse_failed.append({"pbix": str(pbix_path), "error": str(e)})

    return parsed_ok, parse_failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 1 (optional): list and download .pbix into folder. Step 2: parse all .pbix in folder."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("collector_output"),
        help="Folder for .pbix only. Flat: no report_id subdirs. (default: collector_output)",
    )
    parser.add_argument(
        "--parsed-output-dir",
        type=Path,
        default=Path("parsed_output"),
        help="Separate folder for parsed output; one subdir per .pbix. (default: parsed_output)",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list reports (requires workspace + creds); no download or parse.",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Step 1 only: list and download .pbix; do not parse.",
    )
    parser.add_argument(
        "--workspace-name",
        type=str,
        default="P2L_Devop",
        help="Power BI workspace name. Overridden by PBI_WORKSPACE_ID.",
    )
    parser.add_argument(
        "--skip-name-contains",
        type=str,
        action="append",
        default=[],
        metavar="TEXT",
        help="Skip download for reports whose name contains TEXT. Can be repeated.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        default=True,
        help="Skip step 1; only parse all .pbix in --output-dir (folder from other sources).",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    parsed_output_dir = args.parsed_output_dir.resolve()
    pbi_tools_exe = os.environ.get("PBI_TOOLS_EXE") or _default_pbi_tools_exe()

    workspace_id = os.environ.get("PBI_WORKSPACE_ID")
    workspace_name = args.workspace_name or os.environ.get("PBI_WORKSPACE_NAME")
    if workspace_id is None and not workspace_name:
        workspace_name = DEFAULT_WORKSPACE_NAME

    run_download = bool(workspace_id or workspace_name) and not args.no_download

    if run_download:
        credentials = _credentials()
        collector: CollectorProtocol = Collector()
        reports = collector.list(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            credentials=credentials,
        )
        workspace_display = workspace_name or workspace_id
        print(json.dumps({"workspace": workspace_display, "count": len(reports), "reports": reports}, indent=2))
        if args.list_only:
            return

        successful, failed, skipped = _run_step1_download(
            collector,
            output_dir,
            workspace_id,
            workspace_name,
            credentials,
            args.skip_name_contains,
            args.download_only,
        )
        print("Download successful:", len(successful))
        print("Download failed:", len(failed))
        if skipped:
            print("Skipped (by name):", len(skipped))
            print(json.dumps({"skipped": skipped}, indent=2))
        if failed:
            print(json.dumps({"failed": failed}, indent=2))

        if args.download_only:
            return
    else:
        if not output_dir.exists():
            print(f"Output dir does not exist: {output_dir}. Nothing to parse.", file=sys.stderr)
            sys.exit(1)
        collector = Collector()

    if pbi_tools_exe:
        parsed_ok, parse_failed = _run_step2_parse_all(collector, output_dir, parsed_output_dir, pbi_tools_exe)
        print("Parsed:", len(parsed_ok))
        if parse_failed:
            print("Parse failed:", len(parse_failed))
            print(json.dumps({"parse_failed": parse_failed}, indent=2))
    else:
        print("PBI_TOOLS_EXE not set and no default pbi-tools.exe found in repo; skipping parse step.", file=sys.stderr)


if __name__ == "__main__":
    main()
