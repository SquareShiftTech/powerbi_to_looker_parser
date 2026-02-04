# Folder Structure: Power BI to Looker

Target layout for `powerbi_to_looker/src/powerbi_to_looker/`: simple layered architecture (models, config, pipeline stages). Single entry point: `migration_engine`.

---

## 1. Target structure

```
powerbi_to_looker/
  README.md
  pyproject.toml
  MANIFEST.in
  scripts/
    run_collector_real.py
  tests/
    test_collector.py
    test_migration_engine.py
  src/
    powerbi_to_looker/
      __init__.py
      migration_engine.py              # Single entry / orchestrator

      models/                          # LAYER: data shapes only (no business logic)
        __init__.py
        canonical.py                   # MetadataModel, Datasource, Table, Field, etc.
        dashboard.py                   # Dashboard, Report, Visualization, etc. (future viz)

      config/                          # LAYER: mapping rules and defaults
        __init__.py
        loader.py                      # Load YAML, resolve paths
        powerbi_canonical_mapping.yaml # Power BI → canonical enums (see plan/yaml_rules.md)
        canonical_lookml_mapping.yaml  # Canonical → LookML (transformer; see plan/transformer_plan.md)

      collector/                       # LAYER: raw metadata (API + pbix + layout)
        __init__.py
        powerbi_collector.py
        api_loader.py
        pbix_loader.py
        layout_loader.py
        merge.py

      canonical/                       # LAYER: raw → canonical (builder only)
        __init__.py
        builder.py                     # Uses models.*, config; produces MetadataModel

      transformer/                     # LAYER: canonical → LookML terms (see plan/transformer_plan.md)
        __init__.py
        semantic_layer.py              # Orchestrator; outputs views + model dict
        view_builder.py                # One view (dimensions + measures) per table
        dimensions.py                  # Field → LookML dimension entry
        measures.py                   # Field → LookML measure entry; base-dimension reuse
        dates.py                       # Date/datetime handling
        formula_to_sql.py              # DAX → LookML sql (pattern-based)
        model_builder.py               # Tables + relationships → explores with joins
        config.py                      # Load LookML mapping (or use config.load_lookml_mapping)

      generator/                       # LAYER: LookML terms → files
        __init__.py
        lkml_generator.py              # Jinja, writes .view.lkml / .model.lkml

      templates/
        view.lkml.j2
        model.lkml.j2
```

---

## 2. Layer roles

| Layer | Responsibility | Depends on |
|-------|----------------|------------|
| **models** | Pydantic schemas only (canonical + dashboard). No loaders, no builders. | — |
| **config** | Load and expose YAML: Power BI → canonical, canonical → LookML. | — |
| **collector** | Fetch raw metadata (API, pbix, layout) and merge into one dict. | — |
| **canonical** | Build `MetadataModel` from raw using config mappings. | models, config |
| **transformer** | Convert `MetadataModel` to LookML terms (views, explores). | models, config (canonical_lookml_mapping.yaml) |
| **generator** | Render Jinja templates and write .lkml files. | templates |
| **migration_engine** | Run pipeline: collect → canonical → transformer → generator. | collector, canonical, transformer, generator |

---

## 3. Current vs target (summary)

| Current | Target |
|---------|--------|
| `canonical/models.py`, `canonical/dashboard_models.py` | `models/canonical.py`, `models/dashboard.py` |
| No dedicated config | `config/` with loader + `powerbi_canonical_mapping.yaml` |
| `generator/semantic_layer.py` | `generator/lkml_generator.py` (clearer name) |
| Models mixed with builder in `canonical/` | Models in `models/`; `canonical/` only has builder |

---

## 4. Public API (unchanged)

- `from powerbi_to_looker import MigrationEngine`
- `from powerbi_to_looker.collector import collect, collect_from_dict_or_path`
- `from powerbi_to_looker.canonical import build_metadata_model, MetadataModel, ...`
- `from powerbi_to_looker.transformer import to_lookml_terms`
- `from powerbi_to_looker.generator import generate`

Canonical package continues to re-export model classes from `models` so existing `from powerbi_to_looker.canonical import MetadataModel` keeps working.

---

## 5. Migration steps (when implementing)

1. Create `models/` and move `canonical/models.py` → `models/canonical.py`, `canonical/dashboard_models.py` → `models/dashboard.py`; add `models/__init__.py` (re-export canonical types).
2. Create `config/` with `__init__.py`, `loader.py`, `powerbi_canonical_mapping.yaml`.
3. Update `canonical/builder.py` to import from `powerbi_to_looker.models.canonical`; update `canonical/__init__.py` to import from `models` and re-export.
4. Update `transformer/semantic_layer.py` to import from `powerbi_to_looker.models.canonical`.
5. Rename `generator/semantic_layer.py` → `generator/lkml_generator.py`; update `generator/__init__.py`.
6. Remove `canonical/models.py` and `canonical/dashboard_models.py`.
7. Update `MANIFEST.in` to include `config/*.yaml` if needed.
8. Run tests and fix any remaining imports.

---

## 6. Related docs

- [plan/canonical_builder.md](canonical_builder.md) – canonical builder behaviour and mapping.
- [plan/yaml_rules.md](yaml_rules.md) – what lives in canonical vs transformer YAML.
- [plan/transformer_plan.md](transformer_plan.md) – transformer design, modules, YAML, implementation phases.
