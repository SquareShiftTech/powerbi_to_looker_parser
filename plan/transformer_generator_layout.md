# Transformer & Generator Layout Plan

## Goals

- **Transformer:** Replace the single confusing `semantic/` folder with a structure split by **what is built** (views vs explores).
- **Generator:** Split by **what is rendered** (views vs model/manifest) and centralize filters.

---

## 1. Transformer — Option A (views / explores / shared)

### Target structure

```
transformer/
  orchestrator.py              # run(metadata_model) → SemanticLayerArtifact
  views/
    __init__.py
    builder.py                 # build_views() — from semantic/view_builder.py
    field_cleanup.py           # from semantic/field_cleanup.py
    field_type_mapping.py     # from semantic/field_type_mapping.py
    formula_converter.py      # from semantic/formula_converter.py
    view_mapper.py             # from semantic/view_mapper.py
  explores/
    __init__.py
    builder.py                 # build_explores() — from semantic/explore_builder.py
    model_mapper.py            # from semantic/model_mapper.py
  shared/
    __init__.py
    _helpers.py                # from semantic/_helpers.py
  dashboard/
  visualization.py
```

### Orchestrator

- **transformer/orchestrator.py** contains:
  - `run(metadata_model)` — load metadata, call `build_views()`, `build_explores()`, build conversion summary, return `SemanticLayerArtifact`.
  - Imports: `from powerbi_to_looker.transformer.views.builder import build_views`, `from powerbi_to_looker.transformer.explores.builder import build_explores`.
  - Existing `to_lookml_terms` stub remains here.

### Config paths

- All modules under `views/` and `explores/` use `Path(__file__).resolve().parent`; from `views/` or `explores/` we need to reach `powerbi_to_looker` for `config/`. So: `parent.parent.parent` for files in `transformer/views/` or `transformer/explores/` (views → transformer → powerbi_to_looker). Same as current semantic depth.

### Backward compatibility

- Remove `transformer/semantic/` after moving code and updating all imports (run_integration, tests, transformer `__init__`).

---

## 2. Generator — Optimization (views / model / filters)

### Target structure

```
generator/
  writer.py                    # write(artifact, output_dir) — orchestrator only
  views/
    __init__.py
    renderer.py                # render_all_views(artifact, env) → write files, return paths
  model/
    __init__.py
    renderer.py                # render_model_and_manifest(artifact, env, output_dir) → paths
  filters.py                   # _sql_quote_table_column, _comment_dax_lines
  templates/                    # unchanged
```

### Behavior

- **writer.py:** Create Jinja `Environment`, register filters from `filters.py`, call `views.renderer.render_all_views()`, then `model.renderer.render_model_and_manifest()`, return combined list of written paths.
- **views/renderer.py:** Loop over `artifact.views`, render each with view template, write to `output_dir/views/{view_name}.view.lkml`, return list of paths.
- **model/renderer.py:** Render model template and manifest template, write to `output_dir/models/` and `output_dir/`, return list of paths.
- **filters.py:** Define `sql_quote_table_column` and `comment_dax_lines`; no Jinja dependency in this file.

---

## 3. Implementation order

1. Add this plan document.
2. Transformer: create `views/`, `explores/`, `shared/`; move/copy files; update imports; move `run()` into top-level `orchestrator.py`; update `transformer/__init__.py` and `run_integration.py`; remove `semantic/`.
3. Generator: add `filters.py`, `views/renderer.py`, `model/renderer.py`; refactor `writer.py` to orchestrate only; update any generator imports if needed.
4. Run tests and integration script to verify.
