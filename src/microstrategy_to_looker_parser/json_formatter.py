"""
JSON Formatter
Structures the extracted data into the final JSON format.
"""
from typing import Dict, List, Any
import json
import os
import re


class JSONFormatter:
    """Formats extracted data into the required JSON structure."""
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Sanitize filename by removing invalid characters."""
        # Replace invalid filename characters with underscore
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        return sanitized if sanitized else "unnamed"
    
    @staticmethod
    def format_output(projects_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format the final output JSON structure.
        
        Structure:
        {
            "project_1": {
                "dossiers": [
                    {
                        "dossier_information": {...},
                        "visualization_field_mapping": [...],
                        "dataset_type": "datamodel" | "dataset",
                        "dataset_datamodel_information": {...}
                    }
                ],
                "documents": [
                    {
                        "document_information": {...},
                        "visualization_field_mapping": [...],
                        "dataset_type": "datamodel" | "dataset",
                        "dataset_datamodel_information": {...}
                    }
                ]
            },
            "project_2": {...}
        }
        """
        output = {}
        
        for project_data in projects_data:
            project_id = project_data.get("id")
            project_name = project_data.get("name", f"Project_{project_id}")
            
            # Use project name as key, or project_id if name not available
            project_key = project_name if project_name else f"Project_{project_id}"
            
            output[project_key] = {
                "project_id": project_id,
                "project_name": project_name,
                "dossiers": project_data.get("dossiers", []),
                "documents": project_data.get("documents", []),
                "reports": project_data.get("reports", [])
            }
        
        return output
    
    @staticmethod
    def save_to_file(data: Dict[str, Any], filename: str = "microstrategy_output.json") -> None:
        """Save formatted JSON to file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Output saved to {filename}")
    
    @staticmethod
    def save_split_files(projects_data: List[Dict[str, Any]], base_dir: str = "output") -> None:
        """
        Save each dossier and document as separate JSON files in folder structure:
        output/
          project_name_1/
            dossiers/
              dossier_id_name.json
            documents/
              document_id_name.json
          project_name_2/
            ...
        """
        os.makedirs(base_dir, exist_ok=True)
        
        total_dossiers = 0
        total_documents = 0
        total_reports = 0
        
        for project_data in projects_data:
            project_id = project_data.get("id")
            project_name = project_data.get("name", f"Project_{project_id}")
            
            # Sanitize project name for folder
            project_folder = JSONFormatter._sanitize_filename(project_name)
            if not project_folder:
                project_folder = f"Project_{project_id}"
            
            project_path = os.path.join(base_dir, project_folder)
            dossiers_path = os.path.join(project_path, "dossiers")
            documents_path = os.path.join(project_path, "documents")
            reports_path = os.path.join(project_path, "reports")
            
            # Create directories
            os.makedirs(dossiers_path, exist_ok=True)
            os.makedirs(documents_path, exist_ok=True)
            os.makedirs(reports_path, exist_ok=True)
            
            # Save dossiers
            dossiers = project_data.get("dossiers", [])
            for dossier in dossiers:
                dossier_id = dossier.get("id", "unknown")
                dossier_name = dossier.get("name", "Unknown")
                
                # Create filename: id_name.json
                safe_name = JSONFormatter._sanitize_filename(dossier_name)
                filename = f"{dossier_id}_{safe_name}.json"
                filepath = os.path.join(dossiers_path, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(dossier, f, indent=2, ensure_ascii=False)
                
                total_dossiers += 1
            
            # Save documents
            documents = project_data.get("documents", [])
            for document in documents:
                document_id = document.get("id", "unknown")
                document_name = document.get("name", "Unknown")
                
                # Create filename: id_name.json
                safe_name = JSONFormatter._sanitize_filename(document_name)
                filename = f"{document_id}_{safe_name}.json"
                filepath = os.path.join(documents_path, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(document, f, indent=2, ensure_ascii=False)
                
                total_documents += 1
            
            # Save reports
            reports = project_data.get("reports", [])
            for report in reports:
                report_id = report.get("id", "unknown")
                report_name = report.get("name", "Unknown")
                
                # Create filename: id_name.json
                safe_name = JSONFormatter._sanitize_filename(report_name)
                filename = f"{report_id}_{safe_name}.json"
                filepath = os.path.join(reports_path, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                
                total_reports += 1
            
            print(f"  📁 Project: {project_name}")
            print(f"     Dossiers: {len(dossiers)} files saved")
            print(f"     Documents: {len(documents)} files saved")
            print(f"     Reports: {len(reports)} files saved")
        
        print(f"\n✅ All files saved to {base_dir}/")
        print(f"   Total dossiers: {total_dossiers}")
        print(f"   Total documents: {total_documents}")
        print(f"   Total reports: {total_reports}")

