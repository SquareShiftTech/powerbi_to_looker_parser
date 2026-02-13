from pybix import PBIXReader
from pathlib import Path
from typing import List, Dict


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PBIX = _REPO_ROOT / "powerbi_reports" / "Suprer_Store_Dashboard.pbix"

def extract_using_pybix(pbix_path: str) -> List[Dict]:
    """
    Use pybix library to read Power BI file
    """
    reader = PBIXReader(pbix_path)
    
    # Get model
    model = reader.get_model()
    
    columns_metadata = []
    
    for table in model.tables:
        for column in table.columns:
            field_metadata = {
                'id': f"{table.name}.{column.name}",
                'name': column.name,
                'field_type': 'dimension' if column.summarize_by == 'None' else 'measure',
                'data_type': column.data_type,
                'source_table': table.name,
                'source_column': column.source_column,
                'aggregation': column.summarize_by,
                
                'extended_properties': {
                    'powerbi': {
                        'format_string': column.format_string,
                        'is_hidden': column.is_hidden,
                        'data_category': column.data_category,
                        'sort_by_column': column.sort_by_column,
                        'is_nullable': column.is_nullable,
                        'display_folder': column.display_folder,
                        'description': column.description,
                    }
                }
            }
            
            columns_metadata.append(field_metadata)
    
    return columns_metadata