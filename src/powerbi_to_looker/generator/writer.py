"""Render semantic layer artifact to LookML files (views, model, manifest)."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader, select_autoescape

if TYPE_CHECKING:
    from powerbi_to_looker.models.artifact import SemanticLayerArtifact


def _sql_quote_table_column(sql: str) -> str:
    """If sql is ${TABLE}.<col> and col has spaces/special chars, return ${TABLE}.`col` (backtick-wrapped)."""
    if not sql or "${TABLE}." not in sql:
        return sql
    m = re.match(r"^(\$\{TABLE\}\.)(.*)$", sql.strip())
    if not m:
        return sql
    prefix, col = m.group(1), m.group(2)
    if not col or col.startswith("`"):
        return sql
    col_clean = col.rstrip()
    if col_clean.replace("_", "").replace(" ", "").isalnum() and " " not in col_clean:
        return sql
    escaped = col_clean.replace("\\", "\\\\").replace("`", "\\`")
    return f"{prefix}`{escaped}`"


def _comment_dax_lines(text: str | None) -> str:
    """Normalize newlines and prefix every line after the first with '# ' for valid LookML comments."""
    if not text:
        return ""
    s = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = s.split("\n")
    return "\n# ".join(lines)


def write(artifact: "SemanticLayerArtifact", output_dir: str | Path) -> list[str]:
    """Render artifact to LookML files. Returns list of written file paths.

    Writes:
      - views/{view_name}.view.lkml for each view
      - models/{project_name}.model.lkml
      - manifest.lkml
    """
    output_dir = Path(output_dir)
    env = Environment(
        loader=PackageLoader("powerbi_to_looker.generator", "templates"),
        autoescape=select_autoescape(default=False),
    )
    env.filters["sql_quote_table_column"] = _sql_quote_table_column
    env.filters["comment_dax_lines"] = _comment_dax_lines
    written: list[str] = []

    # Views
    views_dir = output_dir / "views"
    views_dir.mkdir(parents=True, exist_ok=True)
    view_tpl = env.get_template("view.lkml.j2")
    for view in artifact.views:
        content = view_tpl.render(view=view)
        path = views_dir / f"{view.view_name}.view.lkml"
        path.write_text(content, encoding="utf-8")
        written.append(str(path))

    # Model
    models_dir = output_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_tpl = env.get_template("model.lkml.j2")
    model_content = model_tpl.render(artifact=artifact)
    model_path = models_dir / f"{artifact.project_name}.model.lkml"
    model_path.write_text(model_content, encoding="utf-8")
    written.append(str(model_path))

    # Manifest
    manifest_tpl = env.get_template("manifest.lkml.j2")
    manifest_content = manifest_tpl.render(artifact=artifact)
    manifest_path = output_dir / "manifest.lkml"
    manifest_path.write_text(manifest_content, encoding="utf-8")
    written.append(str(manifest_path))

    return written
