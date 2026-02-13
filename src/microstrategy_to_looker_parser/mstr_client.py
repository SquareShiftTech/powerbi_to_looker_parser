"""
MicroStrategy API Client
Handles all API interactions with the MicroStrategy server.
"""
import requests
import json
from typing import Dict, Optional, Any, List
from .config import ENV_VARIABLES, API_ENDPOINTS


class MicroStrategyClient:
    """Client for interacting with MicroStrategy REST API."""
    
    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        # Use provided parameters or fall back to ENV_VARIABLES
        self.base_url = base_url or ENV_VARIABLES["base_url"]
        self.username = username or ENV_VARIABLES["username"]
        self.password = password or ENV_VARIABLES["password"]
        self.auth_token: Optional[str] = None
        self.session = requests.Session()
        
        # Validate configuration
        if not self.base_url:
            raise ValueError(
                "ERROR: MSTR_BASE_URL is not set!\n\n"
                "Please configure the base URL using one of these methods:\n"
                "1. Create a .env file with: MSTR_BASE_URL=https://your-server.com\n"
                "2. Set environment variable: $env:MSTR_BASE_URL='https://your-server.com' (PowerShell)\n"
                "3. Edit config.py and set base_url directly\n\n"
                "Example: MSTR_BASE_URL=https://your-microstrategy-server.com"
            )
        if not self.username:
            raise ValueError(
                "ERROR: MSTR_USERNAME is not set!\n\n"
                "Please configure the username using one of these methods:\n"
                "1. Create a .env file with: MSTR_USERNAME=your-username\n"
                "2. Set environment variable: $env:MSTR_USERNAME='your-username' (PowerShell)\n"
                "3. Edit config.py and set username directly"
            )
        if not self.password:
            raise ValueError(
                "ERROR: MSTR_PASSWORD is not set!\n\n"
                "Please configure the password using one of these methods:\n"
                "1. Create a .env file with: MSTR_PASSWORD=your-password\n"
                "2. Set environment variable: $env:MSTR_PASSWORD='your-password' (PowerShell)\n"
                "3. Edit config.py and set password directly"
            )
    
    def _get_headers(self, project_id: Optional[str] = None, include_auth: bool = True) -> Dict[str, str]:
        """Get standard headers for API requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if include_auth and self.auth_token:
            headers["X-MSTR-AuthToken"] = self.auth_token
        
        if project_id:
            headers["X-MSTR-ProjectID"] = project_id
        
        return headers
    
    def login(self) -> bool:
        """
        Step 1: Login to MicroStrategy server and get auth token.
        Returns True if successful, False otherwise.
        """
        url = f"{self.base_url}{API_ENDPOINTS['login']}"
        payload = {
            "username": self.username,
            "password": self.password,
            "loginMode": 1
        }
        
        try:
            response = self.session.post(url, json=payload, headers=self._get_headers(include_auth=False))
            response.raise_for_status()
            
            # Extract auth token from response header
            self.auth_token = response.headers.get("X-MSTR-AuthToken")
            
            if self.auth_token:
                print(f"[SUCCESS] Login successful. Auth token: {self.auth_token[:20]}...")
                return True
            else:
                print("[ERROR] Auth token not found in response headers")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Login failed: {str(e)}")
            return False
    
    def get_projects(self) -> list:
        """
        Step 2: Get list of all projects.
        Returns list of project objects.
        """
        url = f"{self.base_url}{API_ENDPOINTS['projects']}"
        
        try:
            response = self.session.get(url, headers=self._get_headers())
            response.raise_for_status()
            projects = response.json()
            print(f"[SUCCESS] Retrieved {len(projects)} projects")
            return projects
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get projects: {str(e)}")
            return []
    
    def get_dossiers(self, project_id: str) -> list:
        """
        Step 3.1: Get list of dossiers for a project.
        Returns list of dossier objects.
        """
        url = f"{self.base_url}{API_ENDPOINTS['dossiers']}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                # Already a list
                return data
            elif isinstance(data, dict):
                # Check for common response wrapper keys
                if "result" in data:
                    result = data["result"]
                    if isinstance(result, list):
                        return result
                    elif isinstance(result, dict) and "data" in result:
                        return result["data"] if isinstance(result["data"], list) else []
                elif "data" in data:
                    return data["data"] if isinstance(data["data"], list) else []
                elif "dossiers" in data:
                    return data["dossiers"] if isinstance(data["dossiers"], list) else []
            
            # If we can't parse it, return empty list
            print(f"[WARNING] Unexpected dossier response format for project {project_id}")
            print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get dossiers for project {project_id}: {str(e)}")
            return []
    
    def get_documents(self, project_id: str) -> list:
        """
        Step 3.2: Get list of documents for a project.
        Returns list of document objects.
        """
        url = f"{self.base_url}{API_ENDPOINTS['documents']}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                # Already a list
                return data
            elif isinstance(data, dict):
                # Check for common response wrapper keys
                if "result" in data:
                    result = data["result"]
                    if isinstance(result, list):
                        return result
                    elif isinstance(result, dict) and "data" in result:
                        return result["data"] if isinstance(result["data"], list) else []
                elif "data" in data:
                    return data["data"] if isinstance(data["data"], list) else []
                elif "documents" in data:
                    return data["documents"] if isinstance(data["documents"], list) else []
            
            # If we can't parse it, return empty list
            print(f"[WARNING] Unexpected document response format for project {project_id}")
            print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get documents for project {project_id}: {str(e)}")
            return []
    
    def get_reports(self, project_id: str) -> list:
        """
        Get list of reports for a project.
        Returns list of report objects.
        """
        url = f"{self.base_url}{API_ENDPOINTS['reports']}"
        params = {
            "type": 3,
            "name": "*",
            "pattern": 4
        }
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id), params=params)
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Check for common response wrapper keys
                if "result" in data:
                    result = data["result"]
                    if isinstance(result, list):
                        return result
                    elif isinstance(result, dict) and "data" in result:
                        return result["data"] if isinstance(result["data"], list) else []
                elif "data" in data:
                    return data["data"] if isinstance(data["data"], list) else []
                elif "reports" in data:
                    return data["reports"] if isinstance(data["reports"], list) else []
            
            # If we can't parse it, return empty list
            print(f"[WARNING] Unexpected report response format for project {project_id}")
            print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get reports for project {project_id}: {str(e)}")
            return []
    
    def get_report_metadata(self, project_id: str, report_id: str) -> Optional[Dict]:
        """
        Get report metadata/definition.
        Returns report metadata dictionary, or None if failed.
        """
        url = f"{self.base_url}{API_ENDPOINTS['report_metadata'].format(report_id=report_id)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Get more details about HTTP errors
            status_code = e.response.status_code if e.response else "Unknown"
            error_message = str(e)
            
            # Try to get error details from response body
            error_details = None
            if e.response is not None:
                try:
                    error_details = e.response.json()
                except:
                    error_details = e.response.text[:200] if e.response.text else None
            
            print(f"[ERROR] Failed to get report metadata {report_id}: HTTP {status_code} - {error_message}")
            if error_details:
                print(f"   Error details: {error_details}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get report metadata {report_id}: {str(e)}")
            return None
    
    def get_dossier_definition(self, project_id: str, dossier_id: str) -> Optional[Dict]:
        """
        Step 4.1: Get dossier definition/information.
        Returns dossier definition dictionary, or None if failed.
        """
        url = f"{self.base_url}{API_ENDPOINTS['dossier_definition'].format(dossier_id=dossier_id)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Get more details about HTTP errors
            status_code = e.response.status_code if e.response else "Unknown"
            error_message = str(e)
            
            # Try to get error details from response body
            error_details = None
            if e.response is not None:
                try:
                    error_details = e.response.json()
                except:
                    error_details = e.response.text[:200] if e.response.text else None
            
            print(f"[ERROR] Failed to get dossier definition {dossier_id}: HTTP {status_code} - {error_message}")
            if error_details:
                print(f"   Error details: {error_details}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get dossier definition {dossier_id}: {str(e)}")
            return None
    
    def get_document_definition(self, project_id: str, document_id: str) -> Optional[Dict]:
        """
        Step 4.2: Get document definition/information.
        Returns document definition dictionary, or None if failed.
        """
        url = f"{self.base_url}{API_ENDPOINTS['document_definition'].format(document_id=document_id)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Get more details about HTTP errors
            status_code = e.response.status_code if e.response else "Unknown"
            error_message = str(e)
            
            # Try to get error details from response body
            error_details = None
            if e.response is not None:
                try:
                    error_details = e.response.json()
                except:
                    error_details = e.response.text[:200] if e.response.text else None
            
            print(f"[ERROR] Failed to get document definition {document_id}: HTTP {status_code} - {error_message}")
            if error_details:
                print(f"   Error details: {error_details}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get document definition {document_id}: {str(e)}")
            return None
    
    def create_dossier_instance(self, project_id: str, dossier_id: str) -> Optional[str]:
        """
        Step 5: Create a dossier instance.
        Returns instance_id (mid) if successful, None otherwise.
        """
        url = f"{self.base_url}{API_ENDPOINTS['dossier_instance'].format(dossier_id=dossier_id)}"
        payload = {
            "persistViewState": True,
            "username": self.username,
            "password": self.password
        }
        
        try:
            response = self.session.post(url, json=payload, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            data = response.json()
            instance_id = data.get("mid")
            return instance_id
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to create dossier instance for {dossier_id}: {str(e)}")
            return None
    
    def get_visualization_data(self, project_id: str, dossier_id: str, instance_id: str, 
                              chapter_key: str, visualization_key: str) -> Optional[Dict]:
        """
        Step 6: Get data results of a visualization.
        Returns visualization data dictionary.
        """
        endpoint = API_ENDPOINTS['visualization_data'].format(
            dossier_id=dossier_id,
            instance_id=instance_id,
            chapter_key=chapter_key,
            visualization_key=visualization_key
        )
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get visualization data: {str(e)}")
            return None
    
    def get_data_model_info(self, project_id: str, dataset_id: str) -> Optional[Dict]:
        """
        Step 7: Get data model information.
        Returns data model info if it's a Mosaic model, None otherwise.
        """
        url = f"{self.base_url}{API_ENDPOINTS['data_model'].format(dataset_id=dataset_id)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Check if it's the "not a Mosaic model" error
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if "not a Mosaic model" in error_data.get("message", ""):
                        return None  # Not a data model, it's a regular dataset
                except:
                    pass
            print(f"[WARNING] Dataset {dataset_id} is not a Mosaic model")
            return None
    
    def get_data_model_attributes(self, project_id: str, dataset_id: str) -> Optional[Dict]:
        """
        Get data model attributes and relationships.
        Returns attributes dictionary.
        """
        url = f"{self.base_url}{API_ENDPOINTS['data_model_attributes'].format(dataset_id=dataset_id)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get data model attributes for {dataset_id}: {str(e)}")
            return None
    
    def get_data_model_metrics(self, project_id: str, dataset_id: str) -> Optional[Dict]:
        """
        Get data model metrics.
        Returns metrics dictionary.
        """
        url = f"{self.base_url}{API_ENDPOINTS['data_model_metrics'].format(dataset_id=dataset_id)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get data model metrics for {dataset_id}: {str(e)}")
            return None
    
    def get_data_model_tables(self, project_id: str, dataset_id: str) -> Optional[Dict]:
        """
        Get data model tables information.
        Returns tables dictionary with total count and table details.
        """
        url = f"{self.base_url}{API_ENDPOINTS['data_model_tables'].format(dataset_id=dataset_id)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get data model tables for {dataset_id}: {str(e)}")
            return None
    
    def get_dataset_definition(self, project_id: str, dataset_id: str) -> Optional[Dict]:
        """
        Get dataset definition for regular datasets (not Mosaic models).
        Returns dataset definition dictionary.
        """
        url = f"{self.base_url}{API_ENDPOINTS['dataset_definition'].format(dataset_id=dataset_id)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(project_id=project_id))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get dataset definition for {dataset_id}: {str(e)}")
            return None
    
    def get_datasources(self) -> Optional[List[Dict]]:
        """
        Get list of datasources (common for the MicroStrategy environment).
        This API doesn't require a project_id as it's environment-wide.
        Returns list of datasource dictionaries.
        """
        url = f"{self.base_url}{API_ENDPOINTS['datasources']}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(include_auth=True))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get datasources: {str(e)}")
            return None
    
    def get_datasource_namespaces(self, datasource_id: str, project_id: str) -> Optional[Dict]:
        """
        Get namespaces for a specific datasource.
        Requires project_id to be passed in X-MSTR-ProjectID header.
        Returns dictionary with namespaces array.
        Raises exception if error occurs (to be caught by caller).
        """
        url = f"{self.base_url}{API_ENDPOINTS['datasource_namespaces'].format(datasource_id=datasource_id)}"
        
        # Include project_id in headers (required for namespaces API)
        response = self.session.get(url, headers=self._get_headers(include_auth=True, project_id=project_id))
        
        # Try to parse JSON response regardless of status code
        # Some APIs return valid data even with non-200 status codes
        try:
            json_data = response.json()
            # If we got valid JSON with namespaces array, return it (even if status code is not 200)
            if isinstance(json_data, dict) and "namespaces" in json_data:
                return json_data
            # If status is 200, return the JSON data even if structure is different
            if response.status_code == 200:
                return json_data
        except (ValueError, json.JSONDecodeError):
            # Response is not valid JSON, will raise error below
            pass
        
        # If we couldn't parse valid data, raise exception with error details
        # Try to get error details from response
        try:
            error_json = response.json()
            if isinstance(error_json, dict):
                error_msg = f"{response.status_code} Client Error: {response.reason} for url: {url}"
                # Include error details if available
                if "message" in error_json:
                    error_msg += f". Message: {error_json['message']}"
                if "errors" in error_json:
                    error_msg += f". Errors: {error_json['errors']}"
            else:
                error_msg = f"{response.status_code} Client Error: {response.reason} for url: {url}. Response: {error_json}"
        except:
            error_msg = f"{response.status_code} Client Error: {response.reason} for url: {url}. Response text: {response.text[:200] if response.text else 'No response text'}"
        
        raise requests.exceptions.HTTPError(error_msg, response=response)
    
    def get_namespace_tables(self, datasource_id: str, namespace_id: str, project_id: str) -> Optional[Dict]:
        """
        Get tables for a specific namespace within a datasource.
        Requires project_id to be passed in X-MSTR-ProjectID header.
        Returns dictionary with tables array.
        Raises exception if error occurs (to be caught by caller).
        """
        url = f"{self.base_url}{API_ENDPOINTS['namespace_tables'].format(datasource_id=datasource_id, namespace_id=namespace_id)}"
        
        # Include project_id in headers (required for namespace tables API)
        response = self.session.get(url, headers=self._get_headers(include_auth=True, project_id=project_id))
        
        # Try to parse JSON response regardless of status code
        # Some APIs return valid data even with non-200 status codes
        try:
            json_data = response.json()
            # If we got valid JSON with tables array, return it (even if status code is not 200)
            if isinstance(json_data, dict) and "tables" in json_data:
                return json_data
            # If status is 200, return the JSON data even if structure is different
            if response.status_code == 200:
                return json_data
        except (ValueError, json.JSONDecodeError):
            # Response is not valid JSON, will raise error below
            pass
        
        # If we couldn't parse valid data, raise exception with error details
        # Try to get error details from response
        try:
            error_json = response.json()
            if isinstance(error_json, dict):
                error_msg = f"{response.status_code} Client Error: {response.reason} for url: {url}"
                # Include error details if available
                if "message" in error_json:
                    error_msg += f". Message: {error_json['message']}"
                if "errors" in error_json:
                    error_msg += f". Errors: {error_json['errors']}"
            else:
                error_msg = f"{response.status_code} Client Error: {response.reason} for url: {url}. Response: {error_json}"
        except:
            error_msg = f"{response.status_code} Client Error: {response.reason} for url: {url}. Response text: {response.text[:200] if response.text else 'No response text'}"
        
        raise requests.exceptions.HTTPError(error_msg, response=response)
