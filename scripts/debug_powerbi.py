"""Debug Power BI API: token, list, report details, dataset, export. Use to find why Export returns 403.

Uses same env/defaults as run_collector: PBI_TENANT_ID, PBI_CLIENT_ID, PBI_CLIENT_SECRET, PBI_WORKSPACE_ID.
Run from repo root: uv run python scripts/debug_powerbi.py [--workspace-id ID] [--report-id ID]
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

# Ensure package is on path when run as script
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from powerbi_to_looker.collector.powerbi import get_token, get_workspace_id_by_name  # noqa: E402

BASE_URL = "https://api.powerbi.com/v1.0/myorg"
DEFAULT_CREDENTIALS = {
    "tenant_id": "a812643e-dcca-45b3-bde2-ef646799d843",
    "client_id": "8ee9bf2b-e49f-4cb4-90f8-bfd9fd47af17",
    "client_secret": "MD48Q~7nQTc2f8oVsgn.Y3q9osWc3~4rkQGtVc2g",
}
DEFAULT_WORKSPACE_ID = "e30575e4-66e6-457f-b11a-351fc73de664"
DEFAULT_REPORT_ID = "ad094011-2546-41e1-a1ac-53981a196d9b"  # Super_Store_Dashboard


def _credentials() -> dict[str, str]:
    if os.environ.get("PBI_ACCESS_TOKEN"):
        return {"access_token": os.environ["PBI_ACCESS_TOKEN"]}
    tenant = os.environ.get("PBI_TENANT_ID") or DEFAULT_CREDENTIALS["tenant_id"]
    client = os.environ.get("PBI_CLIENT_ID") or DEFAULT_CREDENTIALS["client_id"]
    secret = os.environ.get("PBI_CLIENT_SECRET") or DEFAULT_CREDENTIALS["client_secret"]
    if not secret:
        raise SystemExit("Set PBI_CLIENT_SECRET (or PBI_* env) for API auth.")
    return {"tenant_id": tenant, "client_id": client, "client_secret": secret}


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug Power BI list/export: token, report details, dataset, export.")
    parser.add_argument("--workspace-id", type=str, default=None, help="Power BI workspace (group) id.")
    parser.add_argument("--report-id", type=str, default=None, help="Report id to try exporting.")
    args = parser.parse_args()

    workspace_id = args.workspace_id or os.environ.get("PBI_WORKSPACE_ID") or DEFAULT_WORKSPACE_ID
    workspace_name = os.environ.get("PBI_WORKSPACE_NAME")
    if workspace_name and not (args.workspace_id or os.environ.get("PBI_WORKSPACE_ID")):
        credentials = _credentials()
        token = get_token(credentials)
        resolved = get_workspace_id_by_name(workspace_name, token)
        if resolved:
            workspace_id = resolved
            print(f"Resolved workspace name {workspace_name!r} -> {workspace_id}\n")
    report_id = args.report_id or os.environ.get("PBI_REPORT_ID") or DEFAULT_REPORT_ID

    credentials = _credentials()
    print("Getting access token...")
    try:
        access_token = get_token(credentials)
        print("Token obtained.\n")
    except Exception as e:
        print(f"Token failed: {e}")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 0: List reports (confirm token + list works)
    print("=" * 60)
    print("STEP 0: List reports (verify token)")
    print("=" * 60)
    url = f"{BASE_URL}/groups/{workspace_id}/reports"
    resp = requests.get(url, headers=headers, timeout=60)
    print(f"GET {url}")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Body: {resp.text[:500]}")
        print("\nIf 403: tenant setting 'Service principals can use Fabric APIs' + app in allowed group.")
        sys.exit(1)
    reports = resp.json().get("value", [])
    print(f"Reports in workspace: {len(reports)}")
    for r in reports[:5]:
        print(f"  - {r.get('name')} ({r.get('id')})")
    if len(reports) > 5:
        print(f"  ... and {len(reports) - 5} more")

    # Step 0b: Workspace capacity type (Pro vs Fabric/Premium)
    print("\n" + "=" * 60)
    print("STEP 0b: Workspace capacity type")
    print("=" * 60)
    url = f"{BASE_URL}/groups/{workspace_id}"
    resp = requests.get(url, headers=headers, timeout=60)
    print(f"GET {url}")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Body: {resp.text[:300]}")
    else:
        ws_info = resp.json()
        print(f"Name: {ws_info.get('name')}")
        print(f"Capacity ID: {ws_info.get('capacityId')}")
        print(f"Is On Dedicated Capacity: {ws_info.get('isOnDedicatedCapacity')}")
        print(f"Type: {ws_info.get('type')}")
        if ws_info.get("capacityId"):
            print("\n⚠️  THIS IS A FABRIC/PREMIUM WORKSPACE, NOT PRO!")
            print("   That's why you're getting Premium Files error.")
        else:
            print("\n✅ This is truly a Pro workspace")
            print("   But somehow Large format got enabled - check dataset settings")

    # Step 1: Report details
    print("\n" + "=" * 60)
    print("STEP 1: Report details")
    print("=" * 60)
    url = f"{BASE_URL}/groups/{workspace_id}/reports/{report_id}"
    resp = requests.get(url, headers=headers, timeout=60)
    print(f"GET {url}")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Body: {resp.text}")
        sys.exit(1)
    report_info = resp.json()
    print(f"Name: {report_info.get('name')}")
    print(f"reportType: {report_info.get('reportType')}")
    print(f"datasetId: {report_info.get('datasetId')}")
    print(f"datasetWorkspaceId: {report_info.get('datasetWorkspaceId')}")
    dataset_workspace = report_info.get("datasetWorkspaceId") or workspace_id
    dataset_id = report_info.get("datasetId")

    # Step 2: Dataset in different workspace?
    print("\n" + "=" * 60)
    print("STEP 2: Dataset location")
    print("=" * 60)
    if dataset_workspace != workspace_id:
        print("Dataset is in a different workspace.")
        print(f"  Report workspace:  {workspace_id}")
        print(f"  Dataset workspace: {dataset_workspace}")
        print("  -> App needs Member/Admin in BOTH workspaces.")
    else:
        print("Dataset is in the same workspace.")

    # Step 3: Dataset details
    print("\n" + "=" * 60)
    print("STEP 3: Dataset details")
    print("=" * 60)
    url = f"{BASE_URL}/groups/{dataset_workspace}/datasets/{dataset_id}"
    resp = requests.get(url, headers=headers, timeout=60)
    print(f"GET {url}")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Body: {resp.text[:500]}")
        print("-> No access to dataset workspace or dataset.")
    else:
        ds = resp.json()
        print(f"Name: {ds.get('name')}, configuredBy: {ds.get('configuredBy')}")

    # Step 4: Export – try GET (with/without preferClientRouting) then POST with body format PBIX
    print("\n" + "=" * 60)
    print("STEP 4: Export .pbix")
    print("=" * 60)
    for with_param, label in [(False, "without preferClientRouting"), (True, "with preferClientRouting=true")]:
        export_url = f"{BASE_URL}/groups/{workspace_id}/reports/{report_id}/Export"
        if with_param:
            export_url += "?preferClientRouting=true"
        print(f"\nGET {export_url}")
        resp = requests.get(export_url, headers=headers, timeout=120)
        print(f"Status: {resp.status_code} ({label})")
        if resp.status_code == 200:
            print(f"  Success: {len(resp.content)} bytes")
            break
        print(f"  Response body: {resp.text[:400]}")
        if resp.headers.get("Content-Type", "").startswith("application/json"):
            try:
                print(f"  JSON: {json.dumps(resp.json(), indent=2)[:500]}")
            except Exception:
                pass

    # Step 4b: Try POST Export with body format PBIX (for debugging – API may not support it)
    print("\n" + "-" * 60)
    print("STEP 4b: POST Export with body {\"format\": \"PBIX\"}")
    print("-" * 60)
    export_url = f"{BASE_URL}/groups/{workspace_id}/reports/{report_id}/Export"
    body = {"format": "PBIX"}
    post_headers = {**headers, "Content-Type": "application/json"}
    print(f"POST {export_url}")
    print(f"Body: {json.dumps(body)}")
    resp = requests.post(export_url, headers=post_headers, json=body, timeout=120)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"  Success: {len(resp.content)} bytes")
    else:
        print(f"  Response body: {resp.text[:500]}")
        if resp.headers.get("Content-Type", "").startswith("application/json"):
            try:
                print(f"  JSON: {json.dumps(resp.json(), indent=2)[:600]}")
            except Exception:
                pass

    # Step 5: Workspace access (who has access, is our app there?)
    print("\n" + "=" * 60)
    print("STEP 5: Workspace access (users/groups)")
    print("=" * 60)
    url = f"{BASE_URL}/groups/{workspace_id}/users"
    resp = requests.get(url, headers=headers, timeout=60)
    print(f"GET {url}")
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        users = resp.json().get("value", [])
        apps = [u for u in users if u.get("principalType") == "App"]
        if apps:
            for u in apps:
                print(f"  App: {u.get('displayName')}  Role: {u.get('groupUserAccessRight')}  id: {u.get('identifier')}")
        else:
            print("  No service principals (Apps) in this workspace.")
        print(f"  Total users/roles: {len(users)}")
    else:
        print(f"  Body: {resp.text[:300]}")

    print("\nDone. If Export is 403: enable tenant setting 'Service principals can use Fabric APIs' and add app to allowed security group.")


if __name__ == "__main__":
    main()
