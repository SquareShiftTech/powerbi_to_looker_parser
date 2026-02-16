# Code layout

This document describes the target code layout for the migration pipeline: **collector**, **parser_normalizer**, **transformer**, **generator**, and **common utils** shared across all four.

## Common utils

Reusable across collector, parser_normalizer, transformer, and generator. No business logic; only path/config helpers.

```
common/
  __init__.py
  path_utils.py          # Local path vs GCS (gs://); read bytes/JSON
  yaml_loader.py         # Load YAML config (used by parser_normalizer + transformer)
```

- **path_utils:** Used by parser_normalizer loader (and optionally collector) for local/GCS resolution.
- **yaml_loader:** Single place to load any config YAML; used by parser_normalizer and transformer.

## Collector

The collector follows a single pattern: **list → download → extract**. The same interface can be used from API or CLI, and collection over multiple items can be parallelized.

### Folder structure

```
collector/
  __init__.py
  interface.py           # Contract: list, download, extract, collect
  collector.py            # Implementation (generic name; Power BI today)
  powerbi/                # Power BI backend: auth, API, pbi-tools parse
    __init__.py
    auth.py               # get_token(credentials)
    powerbi_api.py        # list_groups, get_workspace_id_by_name, list_reports, export_report
    parse.py              # run_pbi_tools(pbix_path, output_path, pbi_tools_exe)
  extract/
    __init__.py
    run.py               # extract_to_folder(pbix_path, output_path, pbi_tools_exe) — runs pbi-tools, exe from orchestrator
```

- **Root** holds only the contract and the main implementation; **powerbi/** holds auth, API, and parse so the root is not cluttered.
- **extract/** has a single code path: “.pbix path + output folder + pbi-tools exe (from orchestrator) → parsed output in folder” 
### Interface (contract)

The collector interface exposes:

| Method | Purpose |
|--------|--------|
| `list(...)` | Return list of report/dataset identifiers (id, name, workspace, type, etc.). |
| `download(id)` | Fetch the artifact for one item; returns blob (bytes or path when `output_dir` set). |
| `extract(pbix_path, output_path, pbi_tools_exe)` | Run pbi-tools on .pbix; write parsed output to folder. Returns e.g. `{"output_path": str}`. Exe path from orchestrator. |
| `collect(id, ...)` | Convenience: `download(id)` then, when `output_dir` and `pbi_tools_exe` provided, `extract(pbix_path, output_path, pbi_tools_exe)`. “” |

Implementations live in `collector.py`; extract delegates to `extract.run.extract_to_folder` (which calls `powerbi.parse.run_pbi_tools`).

### Parallelization

- **List** is called once; then you have N items.
- **Download + extract** (or `collect`) can run **per item** in parallel.
- **Tweak:** The collector accepts an optional **`max_workers`** (e.g. in constructor or config). Callers use it to run a thread/process pool over the item list:
  - `max_workers=1`: single-threaded (e.g. default for CLI).
  - `max_workers>1`: parallel (e.g. API batch or CLI `--parallel`).
- **extract/** is stateless: input = .pbix path + output folder + exe; output = folder. No shared mutable state, so parallel execution is safe.

### Using from API and CLI

- **API:** Route handlers call the same collector: e.g. `list()`, then for each (or a subset) run `collect(id)` in a pool, or a single `collect(id)` for one report.
- **CLI:** Script parses args and calls the same methods (e.g. `list`, or `collect(id)` for one, or loop/pool over ids with `collect`).
- No duplicate logic: one implementation, two entry points.

## Parser & normalizer

One module: input = metadata from collector (in-memory) or stored at a path (local file or GCS); output = canonical model(s). Canonical types live in `models/` (e.g. `MetadataModel`, `Dashboard`, `Visualization`); this module only produces them.

### Folder structure

```
parser_normalizer/
  __init__.py             # load(path_or_metadata) -> canonical bundle
  loader.py               # Input: dict | local path | gs:// path -> raw dict
  semantic/
    __init__.py
    orchestrator.py       # Wires handlers; builds MetadataModel
    dimension.py          # raw -> list of canonical dimension fields
    measure.py            # raw -> list of canonical measure fields
    calc_field.py         # raw -> list of canonical calculated fields
    tables.py             # raw -> tables, relationships, datasource shell
  visualization.py        # raw -> Visualization / Chart list
  dashboard.py            # raw -> Dashboard / DashboardMetadata
```

- **Loader:** Resolves input (read from path or use dict), returns raw metadata for downstream.
- **Semantic:** Orchestrator calls tables → dimension → measure → calc_field and assembles one `MetadataModel` (datasources, tables, relationships, fields).
- **Visualization / dashboard:** One file each; split into subpackages only if they grow.

### Mapping config (YAML)

Rules for **raw → canonical** are config-driven. Use **separate YAMLs** per domain:

| Config file | Purpose |
|-------------|---------|
| `config/semantic_mapping.yaml` | Datasource/table/relationship, dimension, measure, calc field rules (types, renames, defaults, aggregation mapping). |
| `config/visualization_mapping.yaml` | Viz type mapping, field roles, style/conditional-formatting rules. |

Optional: a small **index** YAML that only lists paths (e.g. `semantic: config/semantic_mapping.yaml`, `viz: config/visualization_mapping.yaml`) so code has one place to resolve config. Add `config/dashboard_mapping.yaml` later if dashboard rules grow.

## Transformer

Canonical in → LookML terms out. No file I/O; all mapping logic lives here. Structure mirrors canonical (semantic / visualization / dashboard). Generator handles render + write.

### Folder structure

```
transformer/
  __init__.py
  orchestrator.py         # Dispatches to semantic/viz/dashboard; merges LookML terms
  semantic/
    __init__.py
    view_mapper.py        # canonical semantic -> view dicts (dimensions, measures)
    model_mapper.py       # canonical semantic -> explores, joins
    _helpers.py           # formula_to_sql, dates, type mapping (or _helpers/ with separate files)
  visualization.py       # canonical Visualization/Chart -> LookML terms (if needed)
  dashboard/
    __init__.py
    dashboard_mapper.py   # canonical Dashboard -> LookML dashboard structure
```

- **Orchestrator:** Calls semantic, visualization, dashboard mappers; returns one LookML terms bundle.
- **semantic/_helpers:** Shared by view_mapper and model_mapper (formula→SQL, date handling, type mapping).

### Transformer config (YAML)

| Config file | Purpose |
|-------------|---------|
| `config/lookml_mapping.yaml` | Dimension/measure types, SQL dialect, join defaults, BigQuery; used by transformer semantic mappers. |

## Generator

LookML terms in → render (Jinja) → write `.view.lkml`, `.model.lkml`, dashboard files. Thin layer; no mapping logic.

```
generator/
  __init__.py
  writer.py               # LookML terms -> render -> write files
  templates/              # view.lkml.j2, model.lkml.j2, dashboard(s)
  _helpers.py             # Optional: path sanitization, filename rules
```

---

## Summary

| Concern | Location |
|--------|----------|
| **Common** path / GCS | `common/path_utils.py` |
| Common YAML load | `common/yaml_loader.py` |
| **Collector** contract | `collector/interface.py` |
| Collector implementation | `collector/collector.py` |
| Power BI backend | `collector/powerbi/auth.py`, `powerbi_api.py`, `parse.py` |
| Extract (parse) | `collector/extract/run.py` (extract_to_folder); `collector/powerbi/parse.py` (run_pbi_tools) |
| One-item flow | `collect(id)` on the interface |
| Parallelism | Config/constructor `max_workers`; caller runs per-item `collect` in a pool |
| **Parser–normalizer** entry | `parser_normalizer/__init__.py` (`load`) |
| Load input (path / GCS / dict) | `parser_normalizer/loader.py` |
| Semantic orchestration | `parser_normalizer/semantic/orchestrator.py` |
| Semantic handlers | `parser_normalizer/semantic/dimension.py`, `measure.py`, `calc_field.py`, `tables.py` |
| Viz / dashboard canonical | `parser_normalizer/visualization.py`, `parser_normalizer/dashboard.py` |
| Parser–normalizer mapping | `config/semantic_mapping.yaml`, `config/visualization_mapping.yaml` |
| **Transformer** entry | `transformer/orchestrator.py` (canonical -> LookML terms) |
| Semantic mappers | `transformer/semantic/view_mapper.py`, `model_mapper.py` |
| Transformer semantic helpers | `transformer/semantic/_helpers.py` |
| Viz / dashboard mappers | `transformer/visualization.py`, `transformer/dashboard/dashboard_mapper.py` |
| Transformer mapping | `config/lookml_mapping.yaml` |
| **Generator** | `generator/writer.py`, `generator/templates/`, optional `generator/_helpers.py` |

This layout is boilerplate-friendly: the same structure can be reused for other BI sources in other repos, with only the implementation in `collector.py` and the extract modules being BI-specific.
