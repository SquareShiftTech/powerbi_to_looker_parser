# Collector: test cases and integration testing plan

Plan for **collector** unit tests and integration testing. Review and approve before implementation.

---

## 1. Collector contract and “from orchestration” inputs

- **Contract** (see `collector/interface.py` and `docs/code_layout.md`): `list`, `download`, `extract`, `collect`.
- **All of the following are provided by the orchestration layer** (scripts / API / CLI). The collector does not read env, config, or defaults for them:
  - **credentials** — e.g. `tenant_id`, `client_id`, `client_secret` or `access_token`. Passed into `list(...)` and `download(...)`.
  - **workspace_id** — Power BI workspace (group) id or “My Workspace”. Passed into `list(...)` and `download(...)`.
  - **pbi_tools_exe** — Path to pbi-tools executable. Passed in when the collector runs parse (e.g. `extract(..., pbi_tools_exe=...)` or a dedicated parse method).
- **Library responsibility:** Implement list (Power BI API), download (Export API, optional success/failed tracking), extract/parse (using pbi_tools_exe, one folder per report). No orchestration logic; callers decide order and batching.

---

## 2. Collector requirements (recap)

| # | Requirement | Notes |
|---|-------------|--------|
| 1 | List reports from given Power BI workspace | `list(workspace_id=..., credentials=...)` → list of report items (id, name, datasetId, …). |
| 2 | Download .pbix and track failed vs successful | `download(item_id, ...)` uses Export API; return or expose success/failed (e.g. result type or batch summary). |
| 3 | Use pbi-tools to parse .pbix; one folder per report | Parse step receives `pbi_tools_exe` from caller; each report in its own folder (e.g. `output_base/{report_id}/` with .pbix and extracted output). |

---

## 3. Unit test plan (tests/)

**Scope:** Fast tests, no real network or real .pbix. Mock Power BI API and (when needed) file I/O or subprocess. One behavior per test.

**Subfolder from the start:** Collector unit tests live under **tests/collector/** in a single file, `tests/collector/test_collector.py`, so they are easy to find and manage. Use clear test names and optional comment sections to group: protocol, list, download, extract, collect, parse.

### 3.1 Test cases (all in tests/collector/test_collector.py)

| Area | Test case |
|------|-----------|
| **Protocol** | `test_collector_implements_protocol` — Collector has list, download, extract, collect and signatures match. |
| **list** | `test_list_requires_credentials_and_workspace_id` — With missing credentials or workspace_id, list raises or returns empty as per contract. |
| | `test_list_returns_list_of_dicts` — Mock API response; assert return type and that each item has e.g. id, name. |
| **download** | `test_download_returns_bytes_or_path` — Mock Export API; assert return is bytes or str (path). |
| | `test_download_tracks_success_and_failed` — When a batch or result type is used, assert success/failed structure (e.g. two lists or result objects). |
| **extract** | `test_extract_delegates_to_artifact_type` — Mock extract.model/report/dashboard; call extract(blob, artifact_type="model"); assert correct module used. |
| | `test_extract_model_returns_dict` — Given blob or path to fixture, assert return is dict with expected keys. |
| | `test_extract_report_returns_dict` — Same for report extract. |
| | `test_extract_dashboard_returns_dict` — Same for dashboard extract. |
| | `test_extract_raises_on_invalid_blob` — Invalid or empty blob raises. |
| **collect** | `test_collect_calls_download_then_extract` — Mock download and extract; call collect(id); assert download called with id, extract called with download return value. |
| **parse** | `test_parse_receives_pbi_tools_exe_from_caller` — Parse method accepts `pbi_tools_exe`; when called without it, raises or is optional as designed. |
| | `test_parse_runs_subprocess_with_given_exe` — Mock subprocess; call parse(..., pbi_tools_exe="..."); assert subprocess called with exe path. |
| | `test_parse_writes_to_report_folder_only` — Given output_base and report_id, assert output is under e.g. output_base/{report_id}/ (no cross-report writes). |

### 3.2 If split later: add at most 1–2 more files in tests/collector/

We already use **tests/collector/** with one file. If `test_collector.py` grows too large (e.g. 30+ tests or 400+ lines), add at most **1–2 more files** in the same folder (e.g. `test_extract_and_parse.py`) so the folder has **2–3 files max**. Do not add many small files; keep the total number of test files in tests/collector/ manageable.

### 3.3 Fixtures and shared setup

- **tests/conftest.py:** Shared fixtures, e.g. minimal `credentials` dict, sample API response for list, small blob or path to a minimal fixture for extract. Session-scoped if needed.
- **tests/fixtures/:** Optional: minimal .pbix or extracted folder for extract tests; keep small and committed or document how to generate.

---

## 4. Integration testing plan

**Integration testing is required.** The goal is to **test full functionality**: list → download (with success/failed tracking) → parse (pbi-tools, one folder per report). Real flows live in **scripts/**. One script runs the full flow by default; optional flags allow partial runs for debugging.

### 4.1 Single integration script (required)

| Script | Purpose | Inputs (env / CLI) | What it does |
|--------|---------|--------------------|--------------|
| `scripts/run_collector.py` | Integration: full collector flow | `PBI_TENANT_ID`, `PBI_CLIENT_ID`, `PBI_CLIENT_SECRET`, `PBI_WORKSPACE_ID`, `PBI_TOOLS_EXE` (or CLI args); `output_dir` | **Default:** list → download each report (one folder per report) → parse with pbi_tools_exe; track and print success/failed. **Optional flags:** `--list-only` (only list and print), `--download-only` (list + download, no parse) for debugging. |

- **Run manually or from CI** with real credentials and pbi-tools path. Full run exercises list, download, and parse together.
- **Document in script docstring or README:** Required env vars, CLI args, that this is the integration test for full collector functionality.

### 4.2 Sync with code changes

- When collector method signatures, return types, or “from orchestration” inputs change, update the corresponding unit tests and the integration script in the same change.

---

## 5. Implementation order (suggested)

1. **Collector implementation** — Implement the collector in `src/powerbi_to_looker/collector/`: list (Power BI API + auth), download (Export API, success/failed tracking), extract (delegate to extract.model/report/dashboard), parse (invoke pbi-tools with `pbi_tools_exe`, one folder per report). Match contract in `interface.py` and requirements in section 2.
2. **Unit tests** — Subfolder `tests/collector/` with single file `test_collector.py` containing all cases (protocol, list, download, extract, collect, parse); use mocks and fixtures.
3. **Integration script** — One script `scripts/run_collector.py` that runs the full flow (list → download → parse); optional `--list-only`, `--download-only`. Document env and usage. Required for integration coverage.
4. **If unit tests grow** — Add at most 1–2 more files in `tests/collector/` (e.g. test_extract_and_parse.py); cap at 2–3 files in that folder.

---

## 6. Summary

| Area | Where | Notes |
|------|--------|--------|
| Unit tests | tests/collector/test_collector.py | Subfolder from the start; single file; mock API and I/O; protocol, list, download, extract, collect, parse. If split later: add max 1–2 more files in tests/collector/ (2–3 files total). |
| Integration tests | scripts/run_collector.py | Required. One script: full flow (list → download → parse); optional --list-only, --download-only. credentials, workspace_id, pbi_tools_exe from env/CLI. |
| From orchestration | All caller-provided | credentials, workspace_id, pbi_tools_exe; collector never reads env/config for these. |

Review this plan and say when to proceed with implementation.
