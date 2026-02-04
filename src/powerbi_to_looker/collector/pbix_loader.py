"""Load data model (tables, relationships, measures, M, RLS) from .pbix via pbixray."""

from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from pbixray import PBIXRay
except ImportError:
    PBIXRay = None


def _df_to_records(df: Any) -> list[dict]:
    """Convert DataFrame to list of dicts, replacing NaN with None for JSON."""
    if df is None or (pd is not None and hasattr(df, "empty") and df.empty):
        return []
    if pd is None:
        return []
    return df.replace({pd.NA: None}).fillna(value=None).to_dict(orient="records")


def load_from_pbix(pbix_path: str | Path) -> dict[str, Any]:
    """Extract data model metadata from a PBIX file using pbixray.

    Returns tables (with columns), relationships, dax_measures, power_query, rls.
    Relationships are the main payload (API often omits them).

    Args:
        pbix_path: Path to .pbix file.

    Returns:
        Dict with source_file, tables, relationships, dax_measures, power_query, rls.

    Raises:
        FileNotFoundError: If pbix_path does not exist.
        ImportError: If pbixray or pandas is not installed.
    """
    if PBIXRay is None:
        raise ImportError("pbixray is required for .pbix data model extraction. Install with: pip install pbixray")
    if pd is None:
        raise ImportError("pandas is required for pbix_loader. Install with: pip install pandas")

    pbix_path = Path(pbix_path)
    if not pbix_path.exists():
        raise FileNotFoundError(f"PBIX file not found: {pbix_path}")

    model = PBIXRay(str(pbix_path))
    schema_df = model.schema

    tables_with_columns: list[dict] = []
    if schema_df is not None and not schema_df.empty:
        for table_name, group in schema_df.groupby("TableName", sort=False):
            columns = [
                {
                    "column_name": row["ColumnName"],
                    "data_type": None if pd.isna(row.get("PandasDataType")) else str(row["PandasDataType"]),
                }
                for _, row in group.iterrows()
            ]
            tables_with_columns.append({"table_name": table_name, "columns": columns})

    dax_measures = _df_to_records(model.dax_measures)
    relationships = _df_to_records(model.relationships)
    power_query = _df_to_records(model.power_query)
    rls = _df_to_records(model.rls)

    return {
        "source_file": str(pbix_path.resolve()),
        "tables": tables_with_columns,
        "dax_measures": dax_measures,
        "relationships": relationships,
        "power_query": power_query,
        "rls": rls,
    }
