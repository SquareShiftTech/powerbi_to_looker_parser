# Archive plan

Preserve the previous implementation before switching to the new code layout.

## Steps

1. **Archive current code** (one-time):
   - `src` → `archive/src`
   - `tests` → `archive/tests`
   - `scripts` → `archive/scripts`

2. **New layout** lives in:
   - `src/` — new boilerplate (common, collector, parser_normalizer, transformer, generator, models)
   - `tests/` — new tests (placeholders / structure)
   - `scripts/` — new scripts (placeholders)

3. **Restore** (if needed): copy from `archive/src`, `archive/tests`, `archive/scripts` back.

## After archive

- `archive/` is for reference only; not part of the package.
- `pyproject.toml` and tooling point at `src/` and `tests/` as usual.
