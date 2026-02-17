"""Integration script: Step 1 list+download → Step 2 parse → Step 3 canonical (per-report).

Orchestration follows Option B (per-report loop) so an API layer can reuse the same steps.
See plan/integration_script_orchestration.md.

Step 1 — List and download .pbix into --output-dir (requires Power BI API creds + workspace).
Step 2 — Parse all .pbix in --output-dir → --parsed-output-dir (one subdir per report).
Step 3 — For each report: load → semantic → write canonical (metadata_model.json or _error.json).

Env: PBI_TENANT_ID, PBI_CLIENT_ID, PBI_CLIENT_SECRET; PBI_WORKSPACE_ID or PBI_WORKSPACE_NAME.
Optional: PBI_TOOLS_EXE.

Run from repo root:
  uv run python scripts/run_integration.py                 # default: no download; use existing .pbix
  uv run python scripts/run_integration.py --download       # run step 1 (list and download)
  uv run python scripts/run_integration.py --skip-canonical # stop after parse
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from powerbi_to_looker.collector import Collector, CollectorProtocol  # noqa: E402
from powerbi_to_looker.collector.powerbi.pbix_zip import extract_report_from_pbix  # noqa: E402
from powerbi_to_looker.parser_normalizer import discover_report_folders, load  # noqa: E402
from powerbi_to_looker.parser_normalizer.semantic.orchestrator import run as run_semantic  # noqa: E402


def _default_pbi_tools_exe() -> str | None:
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
            if (d / "pbi-tools.exe").exists():
                return str(d / "pbi-tools.exe")
    return None


# Same defaults as run_collector.py for credentials and workspace
DEFAULT_CREDENTIALS = {
    "tenant_id": "a812643e-dcca-45b3-bde2-ef646799d843",
    "client_id": "8ee9bf2b-e49f-4cb4-90f8-bfd9fd47af17",
    "client_secret": "MD48Q~7nQTc2f8oVsgn.Y3q9osWc3~4rkQGtVc2g",
}
DEFAULT_WORKSPACE_NAME = "P2L_Devop"

_MAX_STEM_LEN = 35


def _short_stem(stem: str) -> str:
    if len(stem) <= _MAX_STEM_LEN:
        return stem
    return stem[: _MAX_STEM_LEN - 9] + "_" + stem[-8:]


def _credentials() -> dict[str, str]:
    """Same logic as run_collector: env overrides, else DEFAULT_CREDENTIALS."""
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


def step1_download(
    output_dir: Path,
    workspace_id: str | None,
    workspace_name: str | None,
    skip_name_contains: list[str],
) -> tuple[int, int]:
    """List and download .pbix into output_dir. Returns (ok_count, fail_count)."""
    collector: CollectorProtocol = Collector()
    creds = _credentials()
    reports = collector.list(
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        credentials=creds,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    skip = [s.lower() for s in skip_name_contains]
    ok, fail = 0, 0
    for r in reports:
        rid, name = r.get("id"), r.get("name") or "report"
        if not rid:
            fail += 1
            continue
        if skip and any(s in name.lower() for s in skip):
            continue
        try:
            path_or_bytes = collector.download(
                rid, workspace_id=workspace_id, workspace_name=workspace_name,
                credentials=creds, output_dir=output_dir, report_name=name,
            )
            if isinstance(path_or_bytes, str) and Path(path_or_bytes).exists():
                ok += 1
            else:
                fail += 1
        except Exception:
            fail += 1
    return ok, fail


def step2_parse(
    pbix_dir: Path,
    parsed_output_dir: Path,
    pbi_tools_exe: str | None,
) -> tuple[int, int]:
    """Parse all .pbix in pbix_dir into parsed_output_dir. Returns (ok_count, fail_count)."""
    if not pbi_tools_exe:
        return 0, 0
    collector: CollectorProtocol = Collector()
    parsed_output_dir.mkdir(parents=True, exist_ok=True)
    pbix_files = sorted(pbix_dir.glob("*.pbix"))
    ok, fail = 0, 0
    for pbix_path in pbix_files:
        if not pbix_path.is_file():
            continue
        out_folder = parsed_output_dir / _short_stem(pbix_path.stem)
        out_folder.mkdir(parents=True, exist_ok=True)
        try:
            collector.parse(pbix_path, out_folder, pbi_tools_exe)
            if not (out_folder / "Report").exists():
                extract_report_from_pbix(pbix_path, out_folder)
            ok += 1
        except (subprocess.CalledProcessError, Exception):
            fail += 1
    return ok, fail


def _write_canonical_error(report_out: Path, report_id: str, error: str, stage: str) -> None:
    """Write _error.json for a failed report (load or semantic)."""
    err = {"success": False, "report_id": report_id, "error": error, "stage": stage}
    with open(report_out / "_error.json", "w", encoding="utf-8") as f:
        json.dump(err, f, indent=2)


def process_one_report_canonical(
    report_path: Path,
    report_id: str,
    canonical_output_dir: Path,
) -> dict[str, Any]:
    """
    Run canonical mapping for one report: load → semantic → write metadata_model.json.
    Returns manifest entry: {report_id, success, error?, stage?, metadata_model?}.
    Reusable by API orchestration layer.
    """
    entry: dict[str, Any] = {"report_id": report_id, "success": False}
    report_out = canonical_output_dir / report_id
    report_out.mkdir(parents=True, exist_ok=True)

    try:
        raw = load(str(report_path))
    except Exception as e:
        entry["error"] = str(e)
        entry["stage"] = "load"
        _write_canonical_error(report_out, report_id, str(e), "load")
        return entry

    try:
        metadata_model = run_semantic(raw)
    except Exception as e:
        entry["error"] = str(e)
        entry["stage"] = "semantic"
        _write_canonical_error(report_out, report_id, str(e), "semantic")
        return entry

    try:
        out_file = report_out / "metadata_model.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(
                metadata_model.model_dump(mode="json"),
                f,
                indent=2,
                default=str,
            )
        entry["success"] = True
        entry["metadata_model"] = str(out_file.relative_to(canonical_output_dir))
    except Exception as e:
        entry["error"] = str(e)
        entry["stage"] = "semantic"
        _write_canonical_error(report_out, report_id, str(e), "semantic")
    return entry


def step3_canonical(parsed_output_dir: Path, canonical_output_dir: Path) -> tuple[int, int]:
    """
    Per-report canonical loop (Option B): discover folders → for each report run
    process_one_report_canonical → write _manifest.json. Returns (ok_count, fail_count).
    """
    canonical_output_dir.mkdir(parents=True, exist_ok=True)
    report_folders = discover_report_folders(parsed_output_dir)
    if not report_folders:
        return 0, 0

    manifest: list[dict[str, Any]] = []
    for report_id, report_path in report_folders:
        entry = process_one_report_canonical(report_path, report_id, canonical_output_dir)
        manifest.append(entry)

    manifest_file = canonical_output_dir / "_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    ok = sum(1 for e in manifest if e.get("success"))
    fail = len(manifest) - ok
    return ok, fail


def main() -> None:
    p = argparse.ArgumentParser(description="Integration: download → parse → canonical.")
    p.add_argument("--output-dir", type=Path, default=Path("collector_output"), help=".pbix folder (default: collector_output)")
    p.add_argument("--parsed-output-dir", type=Path, default=Path("parsed_output"), help="Parsed output folder (default: parsed_output)")
    p.add_argument("--canonical-output-dir", type=Path, default=Path("canonical_output"), help="Canonical output folder (default: canonical_output)")
    p.add_argument("--download", action="store_true", help="Run step 1 (list and download .pbix). Default: skip step 1.")
    p.add_argument("--skip-canonical", action="store_true", help="Stop after step 2 (parse only)")
    p.add_argument("--workspace-name", type=str, default=os.environ.get("PBI_WORKSPACE_NAME") or DEFAULT_WORKSPACE_NAME)
    p.add_argument("--skip-name-contains", type=str, action="append", default=[], metavar="TEXT")
    args = p.parse_args()

    output_dir = args.output_dir.resolve()
    parsed_dir = args.parsed_output_dir.resolve()
    canonical_dir = args.canonical_output_dir.resolve()

    workspace_id = os.environ.get("PBI_WORKSPACE_ID")
    workspace_name = args.workspace_name

    # Step 1 — Download (default: skipped)
    if args.download and (workspace_id or workspace_name):
        print("Step 1: List and download .pbix ...")
        ok1, fail1 = step1_download(output_dir, workspace_id, workspace_name, args.skip_name_contains)
        print(f"  Download: {ok1} ok, {fail1} failed")
    else:
        if not args.download and not output_dir.exists():
            print(f"Output dir missing: {output_dir}. Use --output-dir or pass --download to run step 1.", file=sys.stderr)
            sys.exit(1)
        print("Step 1: Skipped (use --download to list and download).")

    # Step 2 — Parse
    print("Step 2: Parse .pbix -> parsed output ...")
    pbi_tools = os.environ.get("PBI_TOOLS_EXE") or _default_pbi_tools_exe()
    if not pbi_tools:
        print("  PBI_TOOLS_EXE not set; skipping parse.", file=sys.stderr)
    else:
        ok2, fail2 = step2_parse(output_dir, parsed_dir, pbi_tools)
        print(f"  Parse: {ok2} ok, {fail2} failed")

    # Step 3 — Canonical
    if args.skip_canonical:
        print("Step 3: Skipped (--skip-canonical).")
        return
    print("Step 3: Canonical mapping ...")
    ok3, fail3 = step3_canonical(parsed_dir, canonical_dir)
    print(f"  Canonical: {ok3} ok, {fail3} failed")
    if fail3:
        print(f"  Manifest: {canonical_dir / '_manifest.json'}")


if __name__ == "__main__":
    main()
