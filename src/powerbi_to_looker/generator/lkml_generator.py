"""Generate .view.lkml and .model.lkml from LookML terms using Jinja templates."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape


def generate(lookml_terms: dict[str, Any], output_dir: str) -> list[str]:
    """Render view and model templates; write .lkml files to output_dir.

    Args:
        lookml_terms: Dict with keys: views (list), model (dict with connection, explores).
        output_dir: Directory to write files.

    Returns:
        List of written file paths.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=PackageLoader("powerbi_to_looker", "templates"),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    files_written = []

    # One .view.lkml per view
    for view in lookml_terms.get("views", []):
        template = env.get_template("view.lkml.j2")
        content = template.render(view=view)
        view_name = view.get("view_name", "view")
        path = out / f"{view_name}.view.lkml"
        path.write_text(content, encoding="utf-8")
        files_written.append(str(path))

    # One .model.lkml for the model (named power_bi_looker to match LookML convention)
    model_data = lookml_terms.get("model") or {}
    template = env.get_template("model.lkml.j2")
    content = template.render(model=model_data)
    path = out / "power_bi_looker.model.lkml"
    path.write_text(content, encoding="utf-8")
    files_written.append(str(path))

    # Emit bundled dashboard template v2 only (matches our model/field names)
    _dashboard_template = Path(__file__).resolve().parent / "dashboard_template" / "super_store_dashboard_v2.dashboard.lookml"
    if _dashboard_template.exists():
        dashboard_out = out / "super_store_dashboard_v2.dashboard.lookml"
        dashboard_out.write_text(_dashboard_template.read_text(encoding="utf-8"), encoding="utf-8")
        files_written.append(str(dashboard_out))

    return files_written
