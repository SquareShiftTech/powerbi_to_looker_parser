# Collector: test cases and integration testing plan

Plan for **collector** unit tests and integration testing. Review and approve before implementation.

---

## 1. Collector contract and “from orchestration” inputs

- **Contract** (see `collector/interface.py` and `docs/code_layout.md`): `list`, `download`, `extract`, `collect`.
- **All of the following are provided by the orchestration layer** (scripts / API / CLI). The collector does not read env, config, or defaults for them:
  - **credentials** — e.g. `tenant_id`, `client_id`, `client_secret` or `access_token`. Passed into `list(...)` and `download(...)`.
  - **workspace_id** or **workspace_name** — Caller may pass either. The **collector** resolves name → id via Power BI Groups API (`GET .../myorg/groups`) when `workspace_name` is given; `workspace_id` takes precedence when both are set. Passed into `list(...)` and `download(...)`.
  - **pbi_tools_exe** — Path to pbi-tools executable. Passed in when the collector runs parse (e.g. `extract(..., pbi_tools_exe=...)` or a dedicated parse method).
- **Library responsibility:** Implement list (Power BI API), download (Export API), extract/parse (using pbi_tools_exe, one folder per report). No orchestration logic; callers decide order and batching.

---

## 2. Collector requirements (recap)

| # | Requirement | Notes |
|---|-------------|--------|
| 1 | List reports from given Power BI workspace | `list(workspace_id=..., workspace_name=..., credentials=...)` → list of report items (id, name, datasetId, …). Name resolved to id inside collector when needed. |
| 2 | Download .pbix and track failed vs successful | `download(item_id, ...)` uses Export API; script only counts success when returned path exists and file is non-empty. |
| 3 | Use pbi-tools to parse .pbix; one folder per report | Parse step receives `pbi_tools_exe` from caller; each report in its own folder (e.g. `output_dir/{report_id}/` with .pbix and extracted output). Report folder path is resolved (absolute). |

---

## 2b. Extract (parse) design

- **Single code path:** One extract step = pass **.pbix path** → run pbi-tools (exe) → **parsed output stored in a folder**. No separate model/report/dashboard extract modules; one implementation (e.g. `powerbi/parse.run_pbi_tools` or a single `extract/` entry that runs the exe).
- **Inputs:** (1) Path to .pbix file. (2) Output folder for parsed/extracted content (by default per-report, e.g. `output_dir/{report_id}/` or report_name). (3) **Exe path** — always passed from **orchestrator** (e.g. `PBI_TOOLS_EXE`); never hardcoded in the library.
- **Output:** Folder containing all parsed details (TMDL, model, etc. — whatever pbi-tools writes). Caller may receive output path or a small summary (e.g. `{"output_path": "..."}`).
- **When extract runs:** **Only successfully downloaded candidates** go to extract. The integration script runs parse (extract) only when download succeeded (path returned, file exists, non-empty). Failed/skipped reports are never passed to extract.

---

## 2c. Single folder flow: step 1 download (optional), step 2 parse all .pbix

- **One folder** (`--output-dir`, default `collector_output`): holds .pbix files (from our download or from other sources). **No report_id subdirs** — flat layout.
- **Step 1 — List and download (download=True when Power BI API creds + workspace given):** Store each .pbix in the folder as `ReportName_shortid.pbix`. Skip step 1 when `--no-download` or when folder is passed from orchestrator (download=False).
- **Step 2 — Parse:** Read **all** .pbix in the folder; write parsed output to a **separate** folder `--parsed-output-dir` (default `parsed_output`), one subdir per .pbix: `parsed_output_dir/<stem>/`. Uses pbi-tools with `-extractFolder` and `-modelSerialization Raw`.
- **Error handling:** When pbi-tools exits non-zero, `run_pbi_tools` raises `subprocess.CalledProcessError` with `.stderr` and `.stdout` set. The integration script catches it and includes `exit_code`, `stderr`, `stdout` in the `parse_failed` entry (JSON output) for diagnostics.
- **download=True** when workspace + credentials are available and `--no-download` is not set. **download=False** when `--no-download` (parse-only: use folder as source of .pbix).
- **CLI:** `--output-dir` = .pbix folder; `--parsed-output-dir` = parsed output folder; `--no-download` = skip step 1. Default `PBI_TOOLS_EXE`: repo `pbi-tools/pbi-tools.exe` or `pbi-tools/<ver>/pbi-tools.exe`.

---

## 2d. Report fallback: extract from .pbix zip when pbi-tools did not write Report

- **Problem:** For some .pbix files, pbi-tools completes successfully but does not write a **Report** folder (no `Report/sections/`, no page/viz layout). We then have no dashboard/viz details.
- **Fix:** A .pbix file is a **ZIP archive**. When the parsed output folder has **no** `Report` directory after pbi-tools, **unzip the .pbix** and extract only the **Report**-related entries (e.g. `Report/`, `Report/Layout`, or whatever the zip contains) into the same parsed output folder. This gives us report layout/viz without depending on pbi-tools writing it.
- **When to run:** After pbi-tools extract succeeds; then check `parsed_output_dir/<stem>/Report`. If missing, run the zip fallback for that .pbix into that folder.
- **Scope:** Read-only extraction from zip into the existing parsed folder; no modification of the .pbix. Implementation: e.g. `powerbi/pbix_zip.py` or helper in parse layer; script calls it when Report is missing.

**What needs to be done (before implementation):**

1. In the **existing** parse flow (e.g. `run_collector.py` step 2): after each successful pbi-tools run for a .pbix, check whether the output folder has a `Report` directory.
2. If **no** `Report`: open the same .pbix as a ZIP; extract every entry whose name is `Report` or starts with `Report/` into that same output folder; then continue.
3. No new scripts or CLI flags. No backfill or scan of existing folders—only this in-flow fallback.
4. Done when: run parse on a .pbix that pbi-tools does not write Report for → the same output folder ends up with `Report/` populated from the .pbix zip.

**Implementation:**

| Step | Location | What |
|------|----------|------|
| 1 | `src/powerbi_to_looker/collector/powerbi/pbix_zip.py` | `extract_report_from_pbix(pbix_path, out_folder)` — open .pbix as ZIP; extract every member named `Report` or `Report/...` (case-insensitive) into `out_folder`. |
| 2 | `scripts/run_collector.py` | In `_run_step2_parse_all`, after successful `collector.parse(...)`, if `(out_folder / "Report").exists()` is False, call `extract_report_from_pbix(pbix_path, out_folder)`. |
| 3 | `tests/collector/test_pbix_zip.py` | Unit tests: zip with `Report/` entries extracted into out_folder; non-Report entries skipped; missing .pbix raises. |

---

## 3. Unit test plan (tests/)

**Scope:** Fast tests, no real network or real .pbix. Mock Power BI API and (when needed) file I/O or subprocess. One behavior per test.

**Subfolder from the start:** Collector unit tests live under **tests/collector/** in a single file, `tests/collector/test_collector.py`, so they are easy to find and manage. Use clear test names and optional comment sections to group: protocol, list, download, extract, collect, parse.

### 3.1 Test cases (all in tests/collector/test_collector.py)

| Area | Test case |
|------|-----------|
| **Protocol** | `test_collector_implements_protocol` — Collector has list, download, extract, collect and signatures match. |
| **list** | `test_list_requires_credentials_and_workspace_id` — With valid creds and workspace_id, list returns from API (mocked). |
| | `test_list_returns_list_of_dicts` — Mock API response; assert return type and that each item has id, name. |
| **download** | `test_download_returns_bytes_or_path` — Mock Export API; assert return is bytes or str (path). |
| | `test_download_writes_to_output_dir_and_returns_path` — When output_dir set, download writes .pbix and returns path. |
| **extract** | `test_extract_calls_extract_to_folder_and_returns_output_path` — extract(pbix_path, output_path, pbi_tools_exe) returns dict with output_path. |
| | `test_extract_raises_on_non_pbix_path` — extract requires .pbix path; raises ValueError for other paths. |
| **collect** | `test_collect_calls_download_then_extract_when_output_dir_and_exe_provided` — When output_dir and pbi_tools_exe provided, collect calls download then extract. |
| | `test_collect_returns_download_only_when_no_pbi_tools_exe` — When pbi_tools_exe not provided, collect does not call extract. |
| **parse** | `test_parse_receives_pbi_tools_exe_from_caller` — Parse method accepts pbi_tools_exe. |
| | `test_parse_runs_subprocess_with_given_exe` — parse() calls run_pbi_tools with exe path. |
| **run_pbi_tools** | `test_run_pbi_tools_success_uses_extract_folder_and_model_serialization_raw` — Subprocess called with extract, -extractFolder, -modelSerialization Raw. |
| | `test_run_pbi_tools_raises_called_process_error_on_nonzero_exit` — On non-zero exit, raises CalledProcessError with stderr and stdout. |
| | `test_run_pbi_tools_raises_file_not_found_for_missing_exe` — Missing exe raises FileNotFoundError. |
| | `test_run_pbi_tools_raises_file_not_found_for_missing_pbix` — Missing .pbix raises FileNotFoundError. |
| **error handling** | `test_parse_failure_includes_exit_code_stderr_stdout_in_failed_entry` — When parse raises CalledProcessError, failed entry includes exit_code, stderr, stdout. |

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
| `scripts/run_collector.py` | Integration: one folder .pbix, separate parsed output | Env: `PBI_*` credentials, workspace; `PBI_TOOLS_EXE` (default: repo pbi-tools exe). CLI: `--output-dir`, `--parsed-output-dir`, `--no-download`, `--list-only`, `--download-only`, `--skip-name-contains`. | **Step 1 (download=True):** list → download each to `output_dir/ReportName_shortid.pbix` (flat). **Step 2:** parse all .pbix in output_dir → `parsed_output_dir/<stem>/` (pbi-tools -extractFolder, -modelSerialization Raw). **Parse errors:** parse_failed entries include exit_code, stderr, stdout. **--no-download:** parse-only. |

- **Run manually or from CI** with real credentials and pbi-tools path. Full run exercises list, download, and parse together.
- **Document in script docstring or README:** Required env vars, CLI args, that this is the integration test for full collector functionality.

### 4.2 Sync with code changes

- When collector method signatures, return types, or “from orchestration” inputs change, update the corresponding unit tests and the integration script in the same change.

---

## 5. Implementation order (suggested)

1. **Collector implementation** — Implement the collector in `src/powerbi_to_looker/collector/`: list (Power BI API + auth), download (Export API, success/failed tracking), extract (delegate to extract.model/report/dashboard), parse (invoke pbi-tools with `pbi_tools_exe`, one folder per report). Match contract in `interface.py` and requirements in section 2.
2. **Unit tests** — Subfolder `tests/collector/` with single file `test_collector.py` containing all cases (protocol, list, download, extract, collect, parse); use mocks and fixtures.
3. **Integration script** — One script `scripts/run_collector.py` that runs the full flow (list → download → parse); optional `--list-only`, `--download-only`. Document env and usage. Required for integration coverage.
4. **Workspace by name** — **Done.** Collector accepts `workspace_id` or `workspace_name`; `_resolve_workspace_id()` in collector resolves name → id via `powerbi_api.get_workspace_id_by_name`. Script passes either to collector; no resolution in script.
5. **Collector layout** — **Done.** Collector root: `interface.py`, `collector.py`, `extract/`. Power BI backend: **collector/powerbi/** (`auth.py`, `powerbi_api.py`, `parse.py`). See `docs/code_layout.md`.
6. **Export API behavior** — **Done.** `powerbi_api.export_report`: 404 → clear message (report not exportable, e.g. usage metrics); 400 → clear message (unsupported config); `preferClientRouting=true` for all workspaces (not only My Workspace).
7. **Integration script behavior** — **Done.** Success only when download returns a path and file exists and is non-empty; report folder uses resolved (absolute) path; `--skip-name-contains` to skip by name (e.g. usage metrics).
8. **Debug script** — **Done.** `scripts/debug_powerbi.py`: token, list reports, workspace capacity type (Pro vs Fabric/Premium), report details, dataset location/details, Export (GET + POST format PBIX). Use to debug 403/404/400 or missing files. Env/CLI: `PBI_WORKSPACE_ID`, `PBI_REPORT_ID`, or `PBI_WORKSPACE_NAME`.
9. **Extract (parse) design** — Single code path: pass .pbix + output folder + `pbi_tools_exe` (from orchestrator) → run pbi-tools → parsed output in folder. No separate model/report/dashboard extract; only successfully downloaded reports go to extract. Optionally unify collector `extract` with this (pbix → folder) and add/update unit and integration tests for parse/extract.
10. **If unit tests grow** — Add at most 1–2 more files in `tests/collector/` (e.g. test_extract_and_parse.py); cap at 2–3 files in that folder.

---

## 6. Summary

| Area | Where | Notes |
|------|--------|--------|
| Unit tests | tests/collector/test_collector.py | Subfolder from the start; single file; mock API and I/O; protocol, list, download, extract, collect, parse, list_groups, get_workspace_id_by_name. If split later: add max 1–2 more files in tests/collector/ (2–3 files total). |
| Integration script | scripts/run_collector.py | One .pbix folder (--output-dir, flat) and separate parsed folder (--parsed-output-dir). Step 1: list + download when creds+workspace. Step 2: parse all .pbix → parsed_output_dir/<stem>/; parse errors include exit_code, stderr, stdout. PBI_TOOLS_EXE default: repo pbi-tools. Flags: --no-download, --list-only, --download-only, --workspace-name, --skip-name-contains. |
| Debug script | scripts/debug_powerbi.py | Token, list reports, workspace capacity type (Pro vs Premium), report details, dataset, Export (GET + POST format PBIX). For debugging 403/404/400 and export issues. |
| From orchestration | All caller-provided | credentials; workspace_id or workspace_name (collector resolves name → id); pbi_tools_exe. Collector never reads env/config for these. |
| Collector layout | collector/ root + powerbi/ | Root: interface.py, collector.py, extract/. Power BI backend: collector/powerbi/ (auth.py, powerbi_api.py, parse.py). |
| Export API | powerbi_api.export_report | 404/400 clear errors; preferClientRouting=true for all workspaces. |
| Extract (parse) | Single code path | Pass .pbix + output folder + pbi_tools_exe → run pbi-tools (extract -extractFolder -modelSerialization Raw). On non-zero exit raise CalledProcessError with stderr/stdout. Script reports parse_failed with exit_code, stderr, stdout. Default exe: repo pbi-tools. |

**Process (see .cursor/rules/plan-and-process.mdc):** Update this plan when adding features; review plan then proceed; keep plan files under plan/ only (no duplicate plan docs).

Review this plan and say when to proceed with implementation.
