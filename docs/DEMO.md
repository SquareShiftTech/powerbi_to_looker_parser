# Demo Guide: Power BI to Looker Pipeline

End-to-end demo: run integration pipeline → push LookML to GitHub.

## Prerequisites

```bash
# Install dependencies
uv sync
# or: pip install -r requirements.txt

# Set environment variables
$env:GITHUB_TOKEN="your_github_token_here"
$env:GITHUB_REPO_URL="https://github.com/SquareShiftTech/looker_demo_repository.git"
$env:GITHUB_BRANCH="feat/looker-demo-phase1"
$env:GITHUB_FOLDER="Education_24b04535"
python scripts/push_to_github.py --verbose

folder
```

## Demo Steps

### 1. Run Integration Pipeline

```bash
# Full pipeline: download → parse → canonical → transformer → generator
uv run python scripts/run_integration.py --download

# Or skip download if .pbix files already exist
uv run python scripts/run_integration.py
```

**Output:**
- `collector_output/` - Downloaded .pbix files
- `parsed_output/` - Parsed Power BI metadata
- `canonical_output/` - Canonical metadata models
- `transformer_output/` - LookML semantic artifacts
- `generator_output/` - **Final LookML files** (views/, models/, manifest.lkml)

### 2. Push to GitHub

```bash
# Push entire generator_output
uv run python scripts/push_to_github.py

# Push only specific folder (e.g., Education_24b04535)
uv run python scripts/push_to_github.py --folder Education_24b04535 --verbose
```

**What it does:**
- Uploads LookML files to GitHub repository
- Creates new files, updates existing ones
- Deletes files in GitHub not present locally (within the folder if `--folder` is used)
- Preserves folder structure in repository

## Quick Demo (One Command)

```bash
# Run pipeline and push Education folder
uv run python scripts/run_integration.py && \
uv run python scripts/push_to_github.py --folder Education_24b04535 --verbose
```

## Verify

1. Check `generator_output/Education_24b04535/` for LookML files
2. Check GitHub repository branch for uploaded files
3. Files should appear under `Education_24b04535/` in the repo

## Troubleshooting

- **Missing token**: Set `GITHUB_TOKEN` environment variable
- **Branch not found**: Create branch in GitHub or use existing branch name
- **Folder not found**: Check folder name matches exactly (case-sensitive)
- **Parse errors**: Ensure `PBI_TOOLS_EXE` is set or pbi-tools exists in `pbi-tools/`
