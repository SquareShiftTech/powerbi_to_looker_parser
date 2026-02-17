# Integration Script Orchestration (Option B)

## Purpose

Define the main pipeline orchestration so that:
- Execution flows through a **single entry** (integration script / API).
- Processing is **per-report** (Option B) so an API orchestration layer can reuse the same steps.
- For now we implement only through **canonical model**; Transformation and Looker generation are added later.

## Execution Flow

### Main orchestrator

- **CLI:** `scripts/run_integration.py`
- **API (future):** Orchestration layer calls the same per-report steps (e.g. "process report X" or "process all reports").

### Step 1: List and Download

- **Responsibility:** List all available `.pbix`; download into a single folder.
- **Module:** Collector (existing). Can be run as a separate phase or subprocess.
- **Output:** `--output-dir` (e.g. `collector_output/`) with one `.pbix` per report.

### Step 2: Process each report (per-report loop)

For **every** parsed report folder (after Step 1 + parse), the orchestrator runs the following in order. Failure at any step marks that report as failed and skips the rest for that report.

| Step   | Name              | Input              | Output                    | On failure        |
|--------|-------------------|--------------------|---------------------------|-------------------|
| **2.a** | Canonical mapping | Parsed report path | `canonical_output/<id>/metadata_model.json` | Mark failed; write `_error.json` |
| **2.b** | Transformation   | Canonical model    | Transformation artifact   | Mark failed; no artifact (future) |
| **2.c** | Looker generation| Transformer output | Looker artifacts          | Mark failed (future) |

- **2.a (implemented):** Load raw from parsed folder → run semantic orchestrator → write canonical `metadata_model.json`. If metadata is missing or load/semantic fails → mark report failed, write `_error.json`.
- **2.b (later):** Pass canonical output to Transformer; store transformation artifact. If no canonical file → fail.
- **2.c (later):** Use transformer output to generate Looker artifacts. If no transformer output → fail.

## Module responsibilities

| Component           | Responsibility |
|--------------------|----------------|
| **Orchestrator**   | Step 1 (list+download); Step 2 parse (all .pbix); Step 2 per-report loop (2.a → 2.b → 2.c); manifest and counts. |
| **Collector**      | List, download, parse (.pbix → parsed folder). |
| **Parser/Normalizer** | Load(raw/path), run_semantic(raw) → canonical `MetadataModel`. |
| **Transformer**   | (Later) canonical → LookML terms; store artifact. |
| **Generator**      | (Later) LookML terms → Looker artifacts. |

## Implementation notes

- **Option B:** The integration script performs an **explicit per-report loop**: discover report folders → for each report run 2.a (and later 2.b, 2.c). This allows the API to call "process one report" or "process all" with the same functions.
- **Reusable unit:** `process_one_report_canonical(report_path, report_id, canonical_output_dir)` returns a manifest entry (success, error, stage). The script loop and the API can both use it.
- **Manifest:** After the canonical step, write `canonical_output/_manifest.json` with one entry per report (`report_id`, `success`, `error`, `stage`, `metadata_model` path when success).
- **Current scope:** Only Step 2.a (canonical) is implemented in the script. Steps 2.b and 2.c are stubbed or omitted until Transformer and Generator are implemented.

## Error handling

- **2.a:** Missing metadata (e.g. no `Model/database.json`) or load/semantic exception → `success: false`, `stage: "load"` or `"semantic"`, write `_error.json` in report output dir.
- **2.b / 2.c:** (Future) Same pattern: fail the report, record stage and error, skip downstream steps for that report.

## Artifact layout

- `collector_output/` — downloaded `.pbix` (flat).
- `parsed_output/<report_id>/` — parsed report (Model/, Report/).
- `canonical_output/<report_id>/metadata_model.json` or `_error.json`.
- `canonical_output/_manifest.json` — per-report status for API/CLI.

(Future: transformation output dir, looker output dir.)
