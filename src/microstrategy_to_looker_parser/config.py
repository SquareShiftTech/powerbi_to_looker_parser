"""
Configuration file for MicroStrategy API credentials and settings.
"""
import os
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variables - loaded from .env file or system environment
# Credentials must be set in .env file - no hardcoded defaults
ENV_VARIABLES: Dict[str, str] = {
    "base_url": os.getenv("MSTR_BASE_URL", ""),
    "username": os.getenv("MSTR_USERNAME", ""),
    "password": os.getenv("MSTR_PASSWORD", ""),
}

# API endpoints
API_ENDPOINTS = {
    "login": "/MicroStrategyLibrary/api/auth/login",
    "projects": "/MicroStrategyLibrary/api/projects",
    "dossiers": "/MicroStrategyLibrary/api/dossiers",
    "documents": "/MicroStrategyLibrary/api/documents",
    "reports": "/MicroStrategyLibrary/api/searches/results",
    "dossier_definition": "/MicroStrategyLibrary/api/v2/dossiers/{dossier_id}/definition",
    "document_definition": "/MicroStrategyLibrary/api/documents/{document_id}/definition",
    "report_metadata": "/MicroStrategyLibrary/api/model/reports/{report_id}",
    "dossier_instance": "/MicroStrategyLibrary/api/dossiers/{dossier_id}/instances",
    "visualization_data": "/MicroStrategyLibrary/api/v2/dossiers/{dossier_id}/instances/{instance_id}/chapters/{chapter_key}/visualizations/{visualization_key}",
    "data_model": "/MicroStrategyLibrary/api/model/dataModels/{dataset_id}",
    "data_model_attributes": "/MicroStrategyLibrary/api/model/dataModels/{dataset_id}/attributes",
    "data_model_metrics": "/MicroStrategyLibrary/api/model/dataModels/{dataset_id}/metrics",
    "data_model_tables": "/MicroStrategyLibrary/api/model/dataModels/{dataset_id}/tables",
    "dataset_definition": "/MicroStrategyLibrary/api/datasets/{dataset_id}",
    "datasources": "/MicroStrategyLibrary/api/datasources",
    "datasource_namespaces": "/MicroStrategyLibrary/api/datasources/{datasource_id}/catalog/namespaces",
    "namespace_tables": "/MicroStrategyLibrary/api/datasources/{datasource_id}/catalog/namespaces/{namespace_id}/tables",
}