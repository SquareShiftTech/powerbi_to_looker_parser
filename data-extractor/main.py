"""Extract Power BI workspace metadata (reports, dashboards, datasets) to JSON."""
import argparse
import json
import logging
import os
import sys
from typing import Optional

from config import get_config
from auth import get_powerbi_token
from api import get_reports, get_dashboards, get_datasets

DEFAULT_OUTPUT_JSON = "workspace_metadata.json"
# DEFAULT_OUTPUT_SUMMARY = "workspace_metadata_summary.txt"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_extract(output_json: Optional[str] = None, output_summary: Optional[str] = None) -> None:
    """Load config, get token, fetch reports/dashboards/datasets, write JSON and optional summary."""
    output_json = output_json or DEFAULT_OUTPUT_JSON
    # output_summary = output_summary or DEFAULT_OUTPUT_SUMMARY

    try:
        cfg = get_config()
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    tenant_id = cfg["PBI_TENANT_ID"]
    workspace_id = cfg["PBI_WORKSPACE_ID"]
    client_id = cfg["PBI_CLIENT_ID"]
    client_secret = cfg["PBI_CLIENT_SECRET"]

    try:
        token = get_powerbi_token(tenant_id, client_id, client_secret)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    reports = get_reports(workspace_id, token)
    dashboards = get_dashboards(workspace_id, token)
    datasets = get_datasets(workspace_id, token)

    payload = {
        "workspace_id": workspace_id,
        "reports": reports,
        "dashboards": dashboards,
        "datasets": datasets,
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s", output_json)

    # summary_lines = [
    #     f"Workspace ID: {workspace_id}",
    #     "",
    #     f"Reports: {len(reports)}",
    #     *[f"  - {r.get('name', r.get('id', '?'))}" for r in reports],
    #     "",
    #     f"Dashboards: {len(dashboards)}",
    #     *[f"  - {d.get('name', d.get('id', '?'))}" for d in dashboards],
    #     "",
    #     f"Datasets (semantic models): {len(datasets)}",
    #     *[f"  - {d.get('name', d.get('id', '?'))}" for d in datasets],
    # ]
    # summary_text = os.linesep.join(summary_lines)
    # print(summary_text)

    # with open(output_summary, "w", encoding="utf-8") as f:
    #     f.write(summary_text)
    # logger.info("Wrote %s", output_summary)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Power BI workspace metadata to JSON")
    parser.add_argument(
        "--output-json",
        default=DEFAULT_OUTPUT_JSON,
        help=f"Output JSON file path (default: {DEFAULT_OUTPUT_JSON})",
    )
    # parser.add_argument(
    #     "--output-summary",
    #     default=DEFAULT_OUTPUT_SUMMARY,
    #     help=f"Output summary text file path (default: {DEFAULT_OUTPUT_SUMMARY})",
    # )
    args = parser.parse_args()
    run_extract(output_json=args.output_json)# output_summary=args.output_summary


if __name__ == "__main__":
    main()
