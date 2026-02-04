# Power BI to LookML Migration Library

Python library for migrating Power BI metadata to LookML (Looker semantic layer). Pipeline: **Collector → Canonical → Transformer → Generator**.

## Features

- **Collector**: Load Power BI metadata from a JSON file or in-memory dict.
- **Canonical**: Convert raw metadata to multi-BI canonical models (datasources, tables, fields).
- **Transformer**: Map canonical model to LookML terms (views, explores).
- **Generator**: Render `.view.lkml` and `.model.lkml` via Jinja templates.

Output is the **LookML semantic layer** (views and model). Dashboard and visualization generation are planned for a later phase.

## Installation

```bash
pip install powerbi-to-looker
```

Or from source (from this directory):

```bash
uv sync
# or: pip install -e .
```

## Quick Start

```python
from powerbi_to_looker import MigrationEngine

engine = MigrationEngine()

# From in-memory metadata
result = engine.migrate_metadata(
    metadata={"source_system": "powerbi", "datasource_name": "Sales"},
    output_dir="output/",
)

# From a JSON file
result = engine.migrate_file(
    path="path/to/data_model_metadata.json",
    output_dir="output/",
)

print(result["files_written"])  # paths to .view.lkml and .model.lkml
```

## Development

```bash
cd powerbi_to_looker
uv sync
uv run pytest
uv run ruff check src
```

## Build and Publish

From the `powerbi_to_looker/` directory:

```bash
uv build
# dist/ will contain the wheel. Upload to your artifact repository (e.g. twine upload dist/*).
```

Optional: use `cloudbuild.yaml` in this directory for GCP Cloud Build (build + publish to Artifact Registry).
