"""Standalone script to run collector, canonical, and optionally transformer + generator with real .pbix and Power BI API.

Real/manual testing: collector -> canonical [-> transformer -> generator]. Writes raw + canonical JSON; with --lookml-dir also writes .view.lkml and model.model.lkml.
Run: uv run python powerbi_to_looker/scripts/run_collector_real.py ...
     python -m powerbi_to_looker.scripts.run_collector_real --help

Hardcoded defaults (from archive/): workspace Powerbi-POC, report Suprer_Store_Dashboard.
Env PBI_* overrides credentials; CLI overrides workspace/report/pbix.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure package is importable when run as script (from powerbi_to_looker or repo root)
if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    src = root / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))

from powerbi_to_looker.canonical import build_metadata_model
from powerbi_to_looker.collector import collect
from powerbi_to_looker.generator import generate
from powerbi_to_looker.transformer import to_lookml_terms

# Hardcoded defaults from archive (API credentials, workspace, report, .pbix path)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CREDENTIALS = {
    "tenant_id": "a812643e-dcca-45b3-bde2-ef646799d843",
    "client_id": "8ee9bf2b-e49f-4cb4-90f8-bfd9fd47af17",
    "client_secret": "MD48Q~7nQTc2f8oVsgn.Y3q9osWc3~4rkQGtVc2g",
}
DEFAULT_WORKSPACE_ID = "5945fc8b-1fb7-48a5-873a-0a35ea442166"  # Powerbi-POC
DEFAULT_REPORT_NAME = "Suprer_Store_Dashboard"
DEFAULT_PBIX = _REPO_ROOT / "powerbi_to_looker_parser" / "powerbi_reports" / "Suprer_Store_Dashboard.pbix"




def _get_credentials() -> dict[str, str]:
    """Credentials: env PBI_* overrides; else use hardcoded defaults from archive."""
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
        description="Run collector and canonical (and optionally transformer + generator) with real .pbix and API; write raw + canonical JSON; use --lookml-dir to also write LookML."
    )
    parser.add_argument(
        "--workspace-id",
        default=DEFAULT_WORKSPACE_ID,
        help=f"Power BI workspace (group) ID (default: {DEFAULT_WORKSPACE_ID})",
    )
    parser.add_argument(
        "--report-name",
        default=DEFAULT_REPORT_NAME,
        help=f"Report/dataset name to filter (default: {DEFAULT_REPORT_NAME})",
    )
    parser.add_argument(
        "--pbix",
        type=Path,
        default=DEFAULT_PBIX,
        help="Path to .pbix file (default: repo powerbi_reports/Suprer_Store_Dashboard.pbix)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("collector_output.json"),
        help="Raw (collector) output JSON path (default: collector_output.json)",
    )
    parser.add_argument(
        "-c",
        "--canonical-output",
        type=Path,
        default=Path("canonical_output.json"),
        help="Canonical (MetadataModel) output JSON path (default: canonical_output.json)",
    )
    parser.add_argument(
        "--scan-timeout",
        type=int,
        default=300,
        help="Scanner API wait timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--lookml-dir",
        type=Path,
        default=Path("lookml_output"),
        metavar="DIR",
        help="If set, run transformer + generator and write .view.lkml and model.model.lkml to DIR",
    )
    args = parser.parse_args()

    credentials = _get_credentials()
    pbix_path = args.pbix.resolve()
    raw_path = args.output.resolve()
    canonical_path = args.canonical_output.resolve()

    print(f"Collecting: workspace={args.workspace_id}, report={args.report_name}, pbix={pbix_path}")
    raw = collect(
        args.workspace_id,
        args.report_name,
        credentials,
        pbix_path,
        scan_timeout=args.scan_timeout,
    )
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2)
    print(f"Wrote raw metadata to {raw_path}")

    print("Building canonical MetadataModel...")
    canonical_model = build_metadata_model(raw)
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    with open(canonical_path, "w", encoding="utf-8") as f:
        json.dump(canonical_model.model_dump(mode="json"), f, indent=2)
    print(f"Wrote canonical model to {canonical_path}")

    if args.lookml_dir is not None:
        lookml_dir = args.lookml_dir.resolve()
        print(f"Building LookML terms and writing to {lookml_dir}...")
        lookml_terms = to_lookml_terms(canonical_model)
        files_written = generate(lookml_terms, str(lookml_dir))
        for p in files_written:
            print(f"  Wrote {p}")
        print(f"Done. {len(files_written)} LookML file(s) written.")


if __name__ == "__main__":
    main()
