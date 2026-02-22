"""Transformer orchestrator: metadata_model -> SemanticLayerArtifact (views, explores)."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from powerbi_to_looker.models.artifact import (
    ConversionSummary,
    SemanticLayerArtifact,
)
from powerbi_to_looker.transformer.views.builder import build_views
from powerbi_to_looker.transformer.explores.builder import build_explores
from powerbi_to_looker.transformer.views.field_cleanup import clean_field_name
from powerbi_to_looker.common.yaml_loader import load_yaml


def _load_metadata(metadata_model: dict[str, Any] | Path) -> dict[str, Any]:
    """Load metadata from dict or JSON file path."""
    if isinstance(metadata_model, dict):
        return metadata_model
    path = Path(metadata_model)
    if not path.exists():
        raise FileNotFoundError(f"metadata_model not found: {path}")
    import json
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(metadata_model: dict[str, Any] | Path) -> SemanticLayerArtifact:
    """Build semantic layer artifact from metadata_model (single datasource).

    Reads first datasource; builds views (one per table), explores (one per physical table),
    conversion_summary; returns SemanticLayerArtifact.
    """
    raw = _load_metadata(metadata_model)
    datasources = raw.get("datasources") or []
    if not datasources:
        raise ValueError("metadata_model has no datasources")
    ds = datasources[0]
    connection = ds.get("connection") or {}
    tables = ds.get("tables") or []
    fields = ds.get("fields") or []
    table_relationships = ds.get("table_relationships") or []

    views = build_views(tables, fields, connection)
    explores = build_explores(tables, table_relationships, views)

    # Conversion summary
    total = 0
    auto = 0
    partial = 0
    manual = 0
    manual_fields: list[dict[str, Any]] = []
    for v in views:
        for f in v.fields:
            total += 1
            if f.conversion_status == "auto":
                auto += 1
            elif f.conversion_status == "partial":
                partial += 1
            else:
                manual += 1
                if f.message:
                    manual_fields.append({
                        "view_name": v.view_name,
                        "field_name": f.field_name,
                        "message": f.message,
                    })
    summary = ConversionSummary(
        total_fields=total,
        auto=auto,
        partial=partial,
        manual=manual,
        manual_fields=manual_fields,
    )

    # project_name from datasource name (same cleanup as field names)
    _rw_path = Path(__file__).resolve().parent.parent / "config" / "looker_reserved_words.yaml"
    _reserved = set((load_yaml(_rw_path) or {}).get("reserved_words") or [])
    project_name = clean_field_name(ds.get("name") or "project", _reserved) or "project"
    database = connection.get("database") or ""
    schema = connection.get("schema") or ""

    return SemanticLayerArtifact(
        artifact_version="1.0",
        source="powerbi",
        target="looker",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        database=database,
        schema=schema,
        views=views,
        explores=explores,
        conversion_summary=summary,
    )


def to_lookml_terms(canonical_bundle: Any) -> dict[str, Any]:
    """Canonical bundle -> LookML terms (views, model, dashboard). Placeholder."""
    raise NotImplementedError("to_lookml_terms")
