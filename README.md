# MicroStrategy Data Extraction Tool

A Python tool to extract comprehensive data from MicroStrategy Library API, including projects, dossiers, documents, visualizations, and dataset/datamodel information.

## Project Structure

```
MicroStrategy_assessment/
├── config.py              # Configuration and API endpoints
├── mstr_client.py         # MicroStrategy API client
├── data_extractor.py      # Data extraction and processing logic
├── json_formatter.py      # JSON output formatting
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## File Descriptions

### `config.py`
- **Purpose**: Stores configuration settings and API endpoints
- **Contains**:
  - Environment variables (base_url, username, password)
  - All API endpoint paths
- **Usage**: Modify credentials here or set environment variables (`MSTR_BASE_URL`, `MSTR_USERNAME`, `MSTR_PASSWORD`)

### `mstr_client.py`
- **Purpose**: Handles all API interactions with MicroStrategy server
- **Key Features**:
  - Authentication (login and token management)
  - All API endpoint methods (projects, dossiers, documents, etc.)
  - Error handling and response parsing
- **Main Class**: `MicroStrategyClient`
- **Methods**: 
  - `login()` - Authenticates and gets auth token
  - `get_projects()` - Fetches all projects
  - `get_dossiers()` / `get_documents()` - Fetches dossiers/documents
  - `get_dossier_definition()` / `get_document_definition()` - Gets definitions
  - `create_dossier_instance()` - Creates instance for visualization data
  - `get_visualization_data()` - Gets visualization field mappings
  - `get_data_model_info()` / `get_dataset_definition()` - Gets dataset/datamodel info

### `data_extractor.py`
- **Purpose**: Extracts and processes data from API responses
- **Key Features**:
  - Parses dossier/document definitions to extract visualization keys
  - Extracts dataset IDs from definitions
  - Determines if dataset is a data model or regular dataset
  - Orchestrates data extraction for dossiers and documents
- **Main Class**: `DataExtractor`
- **Key Methods**:
  - `extract_visualizations_from_dossier_definition()` - Extracts chapter/visualization keys
  - `extract_dataset_id_from_definition()` - Finds dataset ID in definition
  - `get_dataset_or_datamodel_info()` - Determines dataset type and fetches info
  - `extract_dossier_data()` / `extract_document_data()` - Complete extraction for each item

### `json_formatter.py`
- **Purpose**: Structures extracted data into final JSON format
- **Key Features**:
  - Formats data according to required structure
  - Saves output to JSON file
- **Main Class**: `JSONFormatter`
- **Methods**:
  - `format_output()` - Structures data by projects → dossiers/documents
  - `save_to_file()` - Writes JSON to file

### `main.py`
- **Purpose**: Main entry point that orchestrates the entire process
- **Workflow**:
  1. Login to MicroStrategy
  2. Get all projects
  3. For each project:
     - Get dossiers and documents
     - Extract dossier data (definition, visualizations, dataset info)
     - Extract document data (definition, visualizations, dataset info)
  4. Format and save output JSON

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Option 1: Edit `config.py`
Modify the `ENV_VARIABLES` dictionary with your credentials:
```python
ENV_VARIABLES = {
    "base_url": "https://your-server.com",
    "username": "your-username",
    "password": "your-password",
}
```

### Option 2: Use Environment Variables
Set these environment variables:
```bash
export MSTR_BASE_URL="https://your-server.com"
export MSTR_USERNAME="your-username"
export MSTR_PASSWORD="your-password"
```

## Usage

Run the main script:
```bash
python main.py
```

The script will:
1. Authenticate with MicroStrategy
2. Extract all data from all projects
3. Save output to `microstrategy_output.json`

## Output Structure

The output JSON follows this structure:

```json
{
  "Project Name 1": {
    "project_id": "...",
    "project_name": "...",
    "dossiers": [
      {
        "id": "...",
        "name": "...",
        "dossier_information": {...},
        "visualization_field_mapping": [
          {
            "visualization_name": "...",
            "visualization_type": "...",
            "chapter_key": "...",
            "visualization_key": "...",
            "data": {...}
          }
        ],
        "dataset_type": "datamodel" | "dataset",
        "dataset_datamodel_information": {...}
      }
    ],
    "documents": [
      {
        "id": "...",
        "name": "...",
        "document_information": {...},
        "visualization_field_mapping": [...],
        "dataset_type": "datamodel" | "dataset",
        "dataset_datamodel_information": {...}
      }
    ]
  }
}
```

## Authentication Token

The auth token is automatically extracted from the login response header (`X-MSTR-AuthToken`). The token is:
- Generated fresh on each login
- Stored in the client instance
- Used for all subsequent API calls
- Valid for the session duration (typically until logout or expiration)

**Note**: You don't need to manually manage the auth token - it's handled automatically by the `MicroStrategyClient` class.

## Error Handling

The tool includes error handling for:
- Login failures
- API request failures
- Missing data in responses
- Invalid dataset/datamodel types

Errors are logged to console with clear messages, and the extraction continues for other items even if one fails.

## Notes

- The extraction process may take time depending on the number of projects, dossiers, and documents
- Some API calls require instance creation, which adds to processing time
- The tool processes items sequentially to avoid overwhelming the API server
- Progress is displayed in the console as items are processed

