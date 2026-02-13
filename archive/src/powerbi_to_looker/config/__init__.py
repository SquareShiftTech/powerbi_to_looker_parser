"""Config: Power BI → canonical and canonical → LookML mapping rules (YAML)."""

from powerbi_to_looker.config.loader import load_canonical_mapping, load_lookml_mapping

__all__ = ["load_canonical_mapping", "load_lookml_mapping"]
