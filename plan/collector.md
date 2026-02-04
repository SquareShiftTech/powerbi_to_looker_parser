# Collector Plan: Power BI to LookML

Plan for implementing the **collector** stage and its tests, then wiring into the full migration engine tests.

---

## 1. Scope and responsibility

**Collector:** For a given report (identified by API + .pbix file), produce a **single raw metadata dict** for the pipeline (canonical → transformer → generator).

- **Input:** All mandatory: `workspace_id`, `report_name`, `credentials`, `pbix_path`.
- **Output:** One merged dict: API dataset (tables, columns, measures) + pbixray relationships (+ optional M/RLS) + report layout/viz (pages, visuals, filters, slicers).

Reference: [archive/list_workspaces.py](archive/list_workspaces.py) (API), [archive/extract_data_model.py](archive/extract_data_model.py) (pbixray), [archive/extract_visuals.py](archive/extract_visuals.py) (layout).

---

## 2. Input contract

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspace_id` | str | Yes | Power BI workspace (group) id for Scanner API. |
| `report_name` | str | Yes | Report/dataset name to filter scan result. |
| `credentials` | dict | Yes | Auth: `tenant_id`, `client_id`, `client_secret` (or pre-obtained `access_token`). |
| `pbix_path` | str \| Path | Yes | Path to .pbix report file (for relationships + layout). |

Signature (target):

```python
def collect(
    workspace_id: str,
    report_name: str,
    credentials: dict,
    pbix_path: str | Path,
) -> dict[str, Any]:
    ...
```

---

## 3. Output contract

Single dict with at least:

| Section | Keys | Source |
|---------|------|--------|
| API | `workspace_id`, `workspace_name`, `report_name`, `workspaces` (with `datasets`, `reports`, `dashboards`) | Scanner API |
| Dataset | `workspaces[0].datasets[0].tables` (name, columns, measures) | API |
| Relationships | `relationships` and/or `workspaces[0].datasets[0].relationships` | pbixray (API often empty) |
| Optional | `dax_measures`, `power_query`, `rls` | pbixray |
| Layout/viz | `report_layout`: `source_file`, `report_level_filters`, `pages` (id, name, ordinal, width, height, page_level_filters, visuals), `slicers` | .pbix Report/Layout (ZIP) |

Visuals: each has `visual_type`, `name`, `position` (x,y,width,height), `filters`, and `slicer_config` when type is slicer.

---

## 4. Code structure (collector)

```
powerbi_to_looker/src/powerbi_to_looker/collector/
  __init__.py           # Export: collect
  powerbi_collector.py  # collect(workspace_id, report_name, credentials, pbix_path) – orchestrate
  api_loader.py         # get_token, run_scanner, fetch_scan_result; filter by workspace_id + report_name
  pbix_loader.py        # load from .pbix via pbixray: tables, relationships, dax_measures, power_query, rls
  layout_loader.py      # load Report/Layout from .pbix (ZIP): pages, visuals, filters, slicers
  merge.py              # merge_api_and_pbix(api_result, pbix_result); attach report_layout
```

- **powerbi_collector.collect:** Call API loader → get API result; call pbix_loader → get pbix result; call layout_loader → get report_layout; merge (API + pbix relationships + report_layout); return one dict.
- **api_loader:** Token via client credentials; POST getInfo; poll scanStatus; GET scanResult; filter to one workspace and report_name.
- **pbix_loader:** PBIXRay(pbix_path); schema → tables/columns; relationships → list of dicts; optional dax_measures, power_query, rls.
- **layout_loader:** Open .pbix as ZIP; read Report/Layout (UTF-16-LE); parse sections and visualContainers (reuse logic from archive/extract_visuals.py).
- **merge:** Prefer API for dataset structure; set relationships (and optional M/RLS) from pbix; add key `report_layout` from layout_loader.

---

## 5. Implementation order

1. **layout_loader.py** – Pure .pbix read; no API/pbixray. Easy to unit test with a fixture .pbix or ZIP.
2. **pbix_loader.py** – Optional dependency pbixray (+ pandas if needed). Unit test with fixture .pbix.
3. **api_loader.py** – Token + getInfo/scanStatus/scanResult. Unit test with mocked requests (or pytest-vcr).
4. **merge.py** – Merge API + pbix + report_layout; test with dict fixtures.
5. **powerbi_collector.py** – Wire collect(); integration test with mocks for API and real (or fixture) .pbix.
6. **Migration engine** – Update engine to call collect(workspace_id, report_name, credentials, pbix_path) when running full pipeline; keep backward path (e.g. migrate_metadata(dict) for tests) if desired.

---

## 6. Test cases: Collector

### 6.1 layout_loader

| Test | Description |
|------|-------------|
| `test_layout_loader_returns_dict_with_pages_and_visuals` | Given path to .pbix (or fixture ZIP with Report/Layout), assert output has `source_file`, `pages` (list), each page has `visuals`, and `report_level_filters` / `slicers` present. |
| `test_layout_loader_missing_layout_raises` | Invalid .pbix or ZIP without Report/Layout raises ValueError or FileNotFoundError. |
| `test_layout_loader_slicer_has_slicer_config` | For a page that has a slicer visual, at least one visual has `visual_type == "slicer"` and `slicer_config` in output. |

### 6.2 pbix_loader

| Test | Description |
|------|-------------|
| `test_pbix_loader_returns_tables_and_relationships` | Given path to fixture .pbix, assert output has `tables` (with columns), `relationships` (list with FromTableName, ToTableName, etc.). |
| `test_pbix_loader_missing_file_raises` | Non-existent path raises FileNotFoundError. |
| `test_pbix_loader_relationships_have_expected_keys` | Each relationship dict has keys like FromTableName, ToTableName, FromColumnName, ToColumnName, Cardinality (or similar). |

### 6.3 api_loader

| Test | Description |
|------|-------------|
| `test_get_token_returns_access_token` | With mocked requests.post, get_token returns a non-empty string. |
| `test_run_scanner_polls_until_succeeded` | Mock getInfo (202 + scan_id), scanStatus (Running then Succeeded), scanResult (200 + body); run_scanner returns scan result dict. |
| `test_fetch_filtered_result_by_report_name` | Given scan result with workspaces/datasets/reports, filter by report_name returns one workspace and matching dataset/report. |
| `test_api_loader_invalid_credentials_raises` | Token request returns 401 → raise or return error (as designed). |

### 6.4 merge

| Test | Description |
|------|-------------|
| `test_merge_api_and_pbix_relationships_from_pbix` | API result has empty relationships; pbix result has relationships; merged output has relationships from pbix. |
| `test_merge_preserves_api_tables_and_columns` | Merged output tables/columns match API; only relationships (and optional keys) come from pbix. |
| `test_merge_attach_report_layout` | Merged output has top-level `report_layout` with pages and visuals from layout input. |

### 6.5 powerbi_collector (collect)

| Test | Description |
|------|-------------|
| `test_collect_requires_all_mandatory_params` | Calling collect with missing workspace_id or report_name or credentials or pbix_path raises TypeError or ValueError. |
| `test_collect_returns_single_dict` | With mocked API and real/fixture .pbix, collect(...) returns a dict. |
| `test_collect_output_has_workspace_and_report_name` | Output has workspace_id, report_name, workspaces. |
| `test_collect_output_has_relationships` | Output has non-empty relationships (from pbix) when fixture has relationships. |
| `test_collect_output_has_report_layout` | Output has report_layout with pages and visuals. |
| `test_collect_pbix_path_must_exist` | Non-existent pbix_path raises FileNotFoundError. |

### 6.6 Fixtures and mocks

- **Fixtures:** Use repo .pbix (e.g. powerbi_reports/Suprer_Store_Dashboard.pbix) or a small copy in tests/fixtures/; optionally a minimal ZIP with Report/Layout for layout_loader.
- **API:** Use pytest mock or responses/vcr to mock GET/POST to Power BI API (getInfo, scanStatus, scanResult) so tests don’t need real credentials.

---

## 7. Test cases: Migration engine (full pipeline)

Run these **after** collector is implemented and integrated.

| Test | Description |
|------|-------------|
| `test_migrate_full_pipeline_returns_result` | MigrationEngine.migrate(workspace_id, report_name, credentials, pbix_path, output_dir) runs without error and returns dict with e.g. files_written, output_dir. |
| `test_migrate_writes_lookml_files` | After migrate(), output_dir contains at least one .view.lkml and one .model.lkml. |
| `test_migrate_metadata_dict_still_works` | migrate_metadata(metadata_dict, output_dir) still works for backward compatibility (stub/minimal dict) and writes .lkml files. |
| `test_migrate_fails_gracefully_on_invalid_pbix` | Invalid or missing pbix_path leads to clear error (FileNotFoundError or collector error), no silent pass. |
| `test_migrate_fails_gracefully_on_api_error` | If API returns 401/500, error is raised or surfaced (no crash with generic exception). |

---

## 8. Dependencies

- **Required for collector:** `requests` (API), `pbixray` (pbix_loader), `pandas` (if pbixray output is DataFrame). Standard library: `zipfile`, `json` (layout_loader).
- **Optional:** Keep `pbixray` and `pandas` as optional extras if the rest of the package can run without .pbix (e.g. when using pre-fetched JSON only).
- **Tests:** `pytest`, `pytest-mock` or `responses`/`vcr.py` for API mocking.

---

## 9. Downstream: canonical builder

Collector output is consumed by the **canonical builder**, which produces the `MetadataModel`. See [plan/canonical_builder.md](canonical_builder.md) for:

- Raw → canonical mapping (tables, relationships, fields)
- Join behaviour (LEFT to match Power BI)
- Parameters, primary key, measures, and calculated-field decisions

---

## 10. Document revision

| Date | Change |
|------|--------|
| (initial) | Created: collector plan + test cases for collector and migration engine. |
| 2026-02 | Added §9 downstream reference to canonical_builder.md. |
