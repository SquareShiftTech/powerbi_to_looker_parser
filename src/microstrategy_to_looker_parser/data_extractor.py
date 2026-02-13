"""
Data Extraction Logic
Handles the extraction and processing of data from MicroStrategy API.
"""
from typing import Dict, List, Optional, Any
from .mstr_client import MicroStrategyClient


class DataExtractor:
    """Extracts and processes data from MicroStrategy API."""
    
    def __init__(self, client: MicroStrategyClient):
        self.client = client
        self._datasources_list = None  # Cache for datasources (common for environment)
    
    def _get_datasources(self) -> Optional[List[Dict]]:
        """
        Get list of datasources (cached - only called once).
        This is common for the entire MicroStrategy environment.
        """
        if self._datasources_list is None:
            print("[INFO] Fetching datasources list (environment-wide)...")
            response = self.client.get_datasources()
            
            # Handle different response structures
            if response is None:
                print("[WARNING] Failed to load datasources or no datasources found")
                self._datasources_list = []
            elif isinstance(response, list):
                # Direct list of datasources
                self._datasources_list = response
                print(f"[SUCCESS] Loaded {len(self._datasources_list)} datasources")
            elif isinstance(response, dict):
                # Response might be wrapped in a dict (e.g., {"datasources": [...]})
                if "datasources" in response:
                    self._datasources_list = response["datasources"]
                    print(f"[SUCCESS] Loaded {len(self._datasources_list)} datasources from response")
                else:
                    # Try to find any list in the response
                    for key, value in response.items():
                        if isinstance(value, list):
                            self._datasources_list = value
                            print(f"[SUCCESS] Loaded {len(self._datasources_list)} datasources from key '{key}'")
                            break
                    else:
                        print("[WARNING] Could not find datasources list in response")
                        self._datasources_list = []
            else:
                print(f"[WARNING] Unexpected response type: {type(response)}")
                self._datasources_list = []
        
        return self._datasources_list
    
    def _extract_visualizations_from_panel(self, panel: Dict, chapter_key: str, visualizations: List[Dict]) -> None:
        """
        Recursively extract visualizations from a panel and its nested panelStacks.
        """
        # Get visualizations directly in this panel
        panel_visualizations = panel.get("visualizations", [])
        for viz in panel_visualizations:
            visualizations.append({
                "chapter_key": chapter_key,
                "visualization_key": viz.get("key"),
                "visualization_name": viz.get("name"),
                "visualization_type": viz.get("visualizationType")
            })
        
        # Recursively extract from nested panelStacks within this panel
        nested_panel_stacks = panel.get("panelStacks", [])
        for nested_panel_stack in nested_panel_stacks:
            nested_panels = nested_panel_stack.get("panels", [])
            for nested_panel in nested_panels:
                # Recursive call to extract from nested panels
                self._extract_visualizations_from_panel(nested_panel, chapter_key, visualizations)
    
    def extract_visualizations_from_dossier_definition(self, dossier_def: Dict) -> List[Dict]:
        """
        Extract chapter and visualization keys from dossier definition.
        Returns list of {chapter_key, visualization_key, visualization_name} dictionaries.
        Handles nested panelStacks recursively.
        """
        visualizations = []
        
        current_chapter = dossier_def.get("currentChapter")
        chapters = dossier_def.get("chapters", [])
        
        for chapter in chapters:
            chapter_key = chapter.get("key")
            pages = chapter.get("pages", [])
            
            for page in pages:
                # Get visualizations from page level
                page_visualizations = page.get("visualizations", [])
                for viz in page_visualizations:
                    visualizations.append({
                        "chapter_key": chapter_key,
                        "visualization_key": viz.get("key"),
                        "visualization_name": viz.get("name"),
                        "visualization_type": viz.get("visualizationType")
                    })
                
                # Get visualizations from panel stacks (with recursive extraction)
                panel_stacks = page.get("panelStacks", [])
                for panel_stack in panel_stacks:
                    panels = panel_stack.get("panels", [])
                    for panel in panels:
                        # Use recursive function to extract from panel and nested panelStacks
                        self._extract_visualizations_from_panel(panel, chapter_key, visualizations)
        
        return visualizations
    
    def extract_visualizations_from_document_definition(self, document_def: Dict) -> List[Dict]:
        """
        Extract chapter and visualization keys from document definition.
        Similar structure to dossier definition.
        """
        # Documents have similar structure to dossiers
        return self.extract_visualizations_from_dossier_definition(document_def)
    
    def extract_dataset_id_from_definition(self, definition: Dict) -> Optional[str]:
        """
        Extract dataset ID from dossier or document definition.
        The dataset ID might be in different places depending on the structure.
        """
        # Try different possible locations for dataset ID
        if "dataSource" in definition:
            data_source = definition["dataSource"]
            if isinstance(data_source, dict):
                dataset_id = data_source.get("id") or data_source.get("datasetId") or data_source.get("dataModelId")
                if dataset_id:
                    return dataset_id
            elif isinstance(data_source, str):
                return data_source
        
        # Check for dataset references in the definition
        if "datasets" in definition:
            datasets = definition["datasets"]
            if isinstance(datasets, list) and len(datasets) > 0:
                # Try first dataset
                first_dataset = datasets[0]
                if isinstance(first_dataset, dict):
                    return first_dataset.get("id") or first_dataset.get("datasetId")
                elif isinstance(first_dataset, str):
                    return first_dataset
            elif isinstance(datasets, dict):
                return datasets.get("id") or datasets.get("datasetId")
        
        # Check in other common locations
        if "datasetId" in definition:
            return definition["datasetId"]
        
        if "dataModelId" in definition:
            return definition["dataModelId"]
        
        # Check in dataModel field
        if "dataModel" in definition:
            data_model = definition["dataModel"]
            if isinstance(data_model, dict):
                return data_model.get("id") or data_model.get("datasetId")
            elif isinstance(data_model, str):
                return data_model
        
        # Check in pages/chapters for dataset references
        if "chapters" in definition:
            for chapter in definition.get("chapters", []):
                for page in chapter.get("pages", []):
                    if "dataSource" in page:
                        page_ds = page["dataSource"]
                        if isinstance(page_ds, dict):
                            ds_id = page_ds.get("id") or page_ds.get("datasetId")
                            if ds_id:
                                return ds_id
                        elif isinstance(page_ds, str):
                            return page_ds
        
        return None
    
    def get_dataset_or_datamodel_info(self, project_id: str, dataset_id: str) -> Dict[str, Any]:
        """
        Step 7: Determine if dataset is a data model or regular dataset and get info.
        Returns dict with 'type' ('datamodel' or 'dataset') and 'data' (the info).
        """
        if not dataset_id:
            return {"type": None, "data": None}
        
        # First try to get data model info
        data_model_info = self.client.get_data_model_info(project_id, dataset_id)
        
        if data_model_info:
            # It's a data model, get attributes, metrics, and tables
            attributes = self.client.get_data_model_attributes(project_id, dataset_id)
            metrics = self.client.get_data_model_metrics(project_id, dataset_id)
            tables = self.client.get_data_model_tables(project_id, dataset_id)
            
            # Get datasources list (common for environment, cached)
            datasources_list = self._get_datasources()
            
            # Enrich each datasource with its namespaces
            enriched_datasources = []
            if datasources_list:
                print(f"[INFO] Fetching namespaces for {len(datasources_list)} datasources...")
                # Debug: Check first item type
                if datasources_list and len(datasources_list) > 0:
                    print(f"[DEBUG] First datasource type: {type(datasources_list[0])}, value: {datasources_list[0]}")
                
                for idx, datasource in enumerate(datasources_list, 1):
                    datasource_id = None
                    datasource_dict = None
                    
                    # Handle both cases: datasource as dict or as string (ID)
                    if isinstance(datasource, str):
                        # If it's a string, treat it as an ID
                        datasource_id = datasource
                        datasource_dict = {"id": datasource_id, "name": "Unknown"}
                    elif isinstance(datasource, dict):
                        # If it's a dict, use it as-is
                        datasource_dict = datasource.copy()
                        datasource_id = datasource_dict.get("id")
                    else:
                        # Unknown type, skip
                        print(f"    [WARNING] Unknown datasource type: {type(datasource)}, value: {datasource}, skipping")
                        continue
                    
                    if not datasource_dict:
                        print(f"    [WARNING] Could not create datasource_dict, skipping")
                        continue
                    
                    datasource_name = datasource_dict.get("name", "Unknown")
                    if datasource_id:
                        print(f"  [{idx}/{len(datasources_list)}] Fetching namespaces for datasource: {datasource_name} ({datasource_id})")
                        # Get namespaces for this datasource (pass project_id for X-MSTR-ProjectID header)
                        try:
                            namespaces_data = self.client.get_datasource_namespaces(datasource_id, project_id)
                            if namespaces_data:
                                # Enrich each namespace with its tables
                                namespaces_list = namespaces_data.get("namespaces", [])
                                enriched_namespaces = []
                                
                                if namespaces_list:
                                    print(f"    [INFO] Fetching tables for {len(namespaces_list)} namespaces...")
                                    for ns_idx, namespace in enumerate(namespaces_list, 1):
                                        namespace_id = namespace.get("id")
                                        namespace_name = namespace.get("name", "Unknown")
                                        
                                        if namespace_id:
                                            print(f"      [{ns_idx}/{len(namespaces_list)}] Fetching tables for namespace: {namespace_name} ({namespace_id})")
                                            try:
                                                tables_data = self.client.get_namespace_tables(datasource_id, namespace_id, project_id)
                                                if tables_data:
                                                    # Add namespace_tables to the namespace object
                                                    namespace_copy = namespace.copy()
                                                    namespace_copy["namespace_tables"] = tables_data
                                                    enriched_namespaces.append(namespace_copy)
                                                    table_count = len(tables_data.get("tables", []))
                                                    print(f"        [SUCCESS] Loaded {table_count} tables")
                                                else:
                                                    # If tables fetch returned None, add namespace with empty tables
                                                    namespace_copy = namespace.copy()
                                                    namespace_copy["namespace_tables"] = {"tables": []}
                                                    enriched_namespaces.append(namespace_copy)
                                                    print(f"        [WARNING] No tables found or returned None")
                                            except Exception as e:
                                                # If error occurs, store error message and continue
                                                error_msg = str(e)
                                                print(f"        [ERROR] Failed to fetch tables: {error_msg}")
                                                namespace_copy = namespace.copy()
                                                namespace_copy["namespace_tables"] = {
                                                    "tables": [],
                                                    "error": error_msg
                                                }
                                                enriched_namespaces.append(namespace_copy)
                                        else:
                                            # If no namespace ID, add as-is without tables
                                            namespace_copy = namespace.copy()
                                            namespace_copy["namespace_tables"] = {"tables": []}
                                            enriched_namespaces.append(namespace_copy)
                                
                                # Update namespaces_data with enriched namespaces
                                namespaces_data["namespaces"] = enriched_namespaces
                                
                                # Add datasource_namespaces to the datasource object
                                datasource_copy = datasource_dict.copy()
                                datasource_copy["datasource_namespaces"] = namespaces_data
                                enriched_datasources.append(datasource_copy)
                                print(f"    [SUCCESS] Loaded {len(enriched_namespaces)} namespaces with tables")
                            else:
                                # If namespaces fetch returned None, add datasource with empty namespaces
                                datasource_copy = datasource_dict.copy()
                                datasource_copy["datasource_namespaces"] = {"namespaces": []}
                                enriched_datasources.append(datasource_copy)
                                print(f"    [WARNING] No namespaces found or returned None")
                        except Exception as e:
                            # If error occurs, store error message and continue
                            error_msg = str(e)
                            print(f"    [ERROR] Failed to fetch namespaces: {error_msg}")
                            datasource_copy = datasource_dict.copy()
                            datasource_copy["datasource_namespaces"] = {
                                "namespaces": [],
                                "error": error_msg
                            }
                            enriched_datasources.append(datasource_copy)
                    else:
                        # If no ID, add as-is without namespaces
                        datasource_copy = datasource_dict.copy()
                        datasource_copy["datasource_namespaces"] = {"namespaces": []}
                        enriched_datasources.append(datasource_copy)
            
            # Build data structure (datasource_connection_tables will be separate top-level section)
            data = {
                "data_model_info": data_model_info,
                "attributes": attributes,
                "metrics": metrics,
                "datamodel_tables_info": tables
            }
            
            # Build datasource_connection_tables as separate section
            datasource_connection_tables = {
                "list_of_datasources": enriched_datasources
            }
            
            return {
                "type": "datamodel",
                "data": data,
                "datasource_connection_tables": datasource_connection_tables
            }
        else:
            # It's a regular dataset
            dataset_def = self.client.get_dataset_definition(project_id, dataset_id)
            return {
                "type": "dataset",
                "data": dataset_def
            }
    
    def extract_dossier_data(self, project_id: str, dossier) -> Dict[str, Any]:
        """
        Extract complete dossier data including definition, visualizations, and dataset info.
        Handles both dict objects and string IDs.
        """
        # Handle both dict objects and string IDs
        if isinstance(dossier, str):
            dossier_id = dossier
            dossier_name = "Unknown"
        elif isinstance(dossier, dict):
            dossier_id = dossier.get("id")
            dossier_name = dossier.get("name", "Unknown")
        else:
            dossier_id = str(dossier)
            dossier_name = "Unknown"
        
        print(f"  [INFO] Processing dossier: {dossier_name} ({dossier_id})")
        
        # Step 4.1: Get dossier definition
        dossier_def = self.client.get_dossier_definition(project_id, dossier_id)
        if not dossier_def:
            # Try to get more specific error information
            error_info = {
                "id": dossier_id,
                "name": dossier_name,
                "error": "Failed to get dossier definition",
                "error_reason": "API request failed - possible reasons: dossier not found, access denied, or dossier is a template/restricted"
            }
            return error_info
        
        # Update name from definition if available
        if dossier_name == "Unknown" and dossier_def:
            dossier_name = dossier_def.get("name") or dossier_def.get("information", {}).get("name") or "Unknown"
        
        # Step 5: Create dossier instance
        instance_id = self.client.create_dossier_instance(project_id, dossier_id)
        if not instance_id:
            print(f"    [WARNING] Could not create instance for dossier {dossier_id}")
        
        # Step 6.1: Extract visualizations and get their data
        visualizations_list = self.extract_visualizations_from_dossier_definition(dossier_def)
        visualization_mappings = []
        
        if instance_id:
            for viz in visualizations_list:
                viz_data = self.client.get_visualization_data(
                    project_id,
                    dossier_id,
                    instance_id,
                    viz["chapter_key"],
                    viz["visualization_key"]
                )
                visualization_mappings.append({
                    "visualization_name": viz["visualization_name"],
                    "visualization_type": viz["visualization_type"],
                    "chapter_key": viz["chapter_key"],
                    "visualization_key": viz["visualization_key"],
                    "data": viz_data
                })
        
        # Step 7.1: Get dataset/datamodel information
        dataset_id = self.extract_dataset_id_from_definition(dossier_def)
        dataset_info = self.get_dataset_or_datamodel_info(project_id, dataset_id) if dataset_id else None
        
        result = {
            "id": dossier_id,
            "name": dossier_name,
            "dossier_information": dossier_def,
            "visualization_field_mapping": visualization_mappings,
            "dataset_type": dataset_info.get("type") if dataset_info else None,
            "dataset_datamodel_information": dataset_info.get("data") if dataset_info else None
        }
        
        # Add datasource_connection_tables as separate top-level section (only for datamodels)
        if dataset_info and dataset_info.get("type") == "datamodel":
            result["datasource_connection_tables"] = dataset_info.get("datasource_connection_tables")
        
        return result
    
    def extract_document_data(self, project_id: str, document) -> Dict[str, Any]:
        """
        Extract complete document data including definition, visualizations, and dataset info.
        Handles both dict objects and string IDs.
        """
        # Handle both dict objects and string IDs
        if isinstance(document, str):
            document_id = document
            document_name = "Unknown"
        elif isinstance(document, dict):
            document_id = document.get("id")
            document_name = document.get("name", "Unknown")
        else:
            document_id = str(document)
            document_name = "Unknown"
        
        print(f"  [INFO] Processing document: {document_name} ({document_id})")
        
        # Step 4.2: Get document definition
        document_def = self.client.get_document_definition(project_id, document_id)
        if not document_def:
            # Try to get more specific error information
            error_info = {
                "id": document_id,
                "name": document_name,
                "error": "Failed to get document definition",
                "error_reason": "API request failed - possible reasons: document not found, access denied, or document is restricted"
            }
            return error_info
        
        # Update name from definition if available
        if document_name == "Unknown" and document_def:
            document_name = document_def.get("name") or document_def.get("information", {}).get("name") or "Unknown"
        
        # Step 5 (for documents): Try to create instance using dossier endpoint
        # Documents might use the same instance creation endpoint as dossiers
        instance_id = self.client.create_dossier_instance(project_id, document_id)
        if not instance_id:
            print(f"    [WARNING] Could not create instance for document {document_id}")
        
        # Step 6.2: Extract visualizations and get their data
        visualizations_list = self.extract_visualizations_from_document_definition(document_def)
        visualization_mappings = []
        
        if instance_id:
            # Try to get visualization data using dossier visualization endpoint
            # Documents might use the same structure as dossiers
            for viz in visualizations_list:
                viz_data = self.client.get_visualization_data(
                    project_id,
                    document_id,  # Using document_id as dossier_id
                    instance_id,
                    viz["chapter_key"],
                    viz["visualization_key"]
                )
                visualization_mappings.append({
                    "visualization_name": viz["visualization_name"],
                    "visualization_type": viz["visualization_type"],
                    "chapter_key": viz["chapter_key"],
                    "visualization_key": viz["visualization_key"],
                    "data": viz_data
                })
        else:
            # If no instance, just extract structure
            for viz in visualizations_list:
                visualization_mappings.append({
                    "visualization_name": viz["visualization_name"],
                    "visualization_type": viz["visualization_type"],
                    "chapter_key": viz["chapter_key"],
                    "visualization_key": viz["visualization_key"],
                    "data": None
                })
        
        # Step 7.2: Get dataset/datamodel information
        dataset_id = self.extract_dataset_id_from_definition(document_def)
        dataset_info = self.get_dataset_or_datamodel_info(project_id, dataset_id) if dataset_id else None
        
        result = {
            "id": document_id,
            "name": document_name,
            "document_information": document_def,
            "visualization_field_mapping": visualization_mappings,
            "dataset_type": dataset_info.get("type") if dataset_info else None,
            "dataset_datamodel_information": dataset_info.get("data") if dataset_info else None
        }
        
        # Add datasource_connection_tables as separate top-level section (only for datamodels)
        if dataset_info and dataset_info.get("type") == "datamodel":
            result["datasource_connection_tables"] = dataset_info.get("datasource_connection_tables")
        
        return result
    
    def extract_report_data(self, project_id: str, report) -> Dict[str, Any]:
        """
        Extract complete report data including basic info and metadata.
        Handles both dict objects and string IDs.
        """
        # Handle both dict objects and string IDs
        if isinstance(report, str):
            report_id = report
            report_name = "Unknown"
            report_basic_info = {}
        elif isinstance(report, dict):
            report_id = report.get("id")
            report_name = report.get("name", "Unknown")
            report_basic_info = report  # Store the basic info from first API call
        else:
            report_id = str(report)
            report_name = "Unknown"
            report_basic_info = {}
        
        print(f"  📋 Processing report: {report_name} ({report_id})")
        
        # Step 1: Get report metadata (second API call)
        report_metadata = self.client.get_report_metadata(project_id, report_id)
        
        # Structure the output as requested:
        # - First API call response (basic info)
        # - Report definition: Second API call response (metadata)
        output = {
            "id": report_id,
            "name": report_name
        }
        
        # Add basic info from first API call if available
        if report_basic_info:
            output.update(report_basic_info)
        else:
            # If we only have ID, create minimal structure
            output.update({
                "id": report_id,
                "name": report_name
            })
        
        # Add report definition (metadata from second API call)
        if report_metadata:
            output["report_definition"] = report_metadata
        else:
            output["report_definition"] = None
            output["error"] = "Failed to get report metadata"
        
        return output
