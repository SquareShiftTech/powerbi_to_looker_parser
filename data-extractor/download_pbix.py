"""Download Power BI reports from a workspace as .pbix files into a folder."""
import argparse
import json
import logging
import os
import sys

from config import get_config
from auth import get_powerbi_token
from api import export_report, _safe_filename

DEFAULT_OUTPUT_DIR = "downloaded_pbix"
# Default metadata JSON: same folder as this script
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_METADATA_JSON = os.path.join(_SCRIPT_DIR, "workspace_metadata.json")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_download(output_dir: str, metadata_json: str) -> None:
    """
    Download each report as .pbix into output_dir.
    workspace_id and reports are read from the metadata JSON file only.
    """
    with open(metadata_json, encoding="utf-8") as f:
        data = json.load(f)
    workspace_id = data.get("workspace_id")
    reports = data.get("reports", [])
    if not workspace_id:
        logger.error("Metadata JSON missing workspace_id")
        sys.exit(1)
    logger.info("Loaded %s reports from %s", len(reports), metadata_json)
    try:
        cfg = get_config()
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)
    token = get_powerbi_token(
        cfg["PBI_TENANT_ID"], cfg["PBI_CLIENT_ID"], cfg["PBI_CLIENT_SECRET"]
    )

    if not reports:
        logger.warning("No reports to download")
        return

    os.makedirs(output_dir, exist_ok=True)
    failed = []
    for report in reports:
        report_id = report.get("id")
        name = report.get("name", "report")
        if not report_id:
            logger.warning("Report missing id, skipping: %s", name)
            failed.append(name or "?")
            continue
        filename = _safe_filename(name, report_id)
        path = os.path.join(output_dir, filename)
        try:
            content = export_report(workspace_id, report_id, token)
            with open(path, "wb") as f:
                f.write(content)
            logger.info("Saved %s", filename)
        except Exception as e:
            logger.error("Failed %s: %s", name, e)
            failed.append(report_id)
    if failed:
        logger.warning("Failed report ids: %s", failed)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Power BI workspace reports as .pbix files"
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for .pbix files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--metadata-json",
        default=DEFAULT_METADATA_JSON,
        help=f"Path to workspace_metadata.json (default: {DEFAULT_METADATA_JSON})",
    )
    args = parser.parse_args()
    run_download(output_dir=args.output_dir, metadata_json=args.metadata_json)


if __name__ == "__main__":
    main()
