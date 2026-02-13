"""Semantic: raw -> MetadataModel. Orchestrator wires dimension, measure, calc_field, tables."""

from powerbi_to_looker.parser_normalizer.semantic.orchestrator import run

__all__ = ["run"]
