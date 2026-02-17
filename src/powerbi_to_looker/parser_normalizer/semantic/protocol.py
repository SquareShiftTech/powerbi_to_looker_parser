"""Semantic handler protocol and TablesResult. All handlers implement can_handle(raw) and run(raw)."""

from typing import Any, Protocol, runtime_checkable

from powerbi_to_looker.models.canonical import (
    Connection,
    Table,
    TableRelationship,
)


class TablesResult:
    """Return type of the tables handler: tables, table_relationships, connection."""

    __slots__ = ("tables", "table_relationships", "connection")

    def __init__(
        self,
        tables: list[Table],
        table_relationships: list[TableRelationship],
        connection: Connection,
    ) -> None:
        self.tables = tables
        self.table_relationships = table_relationships
        self.connection = connection


@runtime_checkable
class SemanticHandlerProtocol(Protocol):
    """Protocol for semantic handlers. Orchestrator sends full raw; handler returns own type."""

    def can_handle(self, raw: dict[str, Any]) -> bool:
        """Return True if this handler can process the raw model (e.g. has tables, has columns)."""
        ...

    def run(self, raw: dict[str, Any]) -> Any:
        """Extract and map to canonical. Tables handler → TablesResult; others → list[Field]."""
        ...
