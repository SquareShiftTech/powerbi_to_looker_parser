"""
Main Entry Point for MicroStrategy Assessment Tool
Orchestrates the entire data extraction process with CLI support.
Supports both .env file and command-line arguments (CLI args take precedence).
"""
import argparse
import os
from pathlib import Path
from microstrategy_to_looker_parser.mstr_client import MicroStrategyClient
from microstrategy_to_looker_parser.data_extractor import DataExtractor
from microstrategy_to_looker_parser.json_formatter import JSONFormatter


def upload_output_to_gcs(gcp_project: str, bucket_name: str, output_dir: str = "output"):
    """
    Upload the entire output folder to GCS bucket.
    Deletes and recreates the bucket every time (even if it already exists).
    
    Args:
        gcp_project: GCP project ID
        bucket_name: GCS bucket name
        output_dir: Local output directory to upload (default: "output")
        
    Returns:
        str: GCS bucket path where files were uploaded
    """
    try:
        from google.cloud import storage
        from google.cloud.exceptions import NotFound
    except ImportError:
        raise ImportError(
            "google-cloud-storage is required for GCS upload. "
            "Install it with: pip install google-cloud-storage"
        )
    
    output_path = Path(output_dir)
    if not output_path.exists():
        raise FileNotFoundError(f"Output directory not found: {output_dir}")
    
    print(f"\n{'='*60}")
    print(f"Uploading output to GCS bucket")
    print(f"{'='*60}")
    print(f"  GCP Project: {gcp_project}")
    print(f"  Bucket Name: {bucket_name}")
    print(f"  Source: {output_path.absolute()}")
    
    # Initialize GCS client
    client = storage.Client(project=gcp_project)
    
    # Always delete and recreate the bucket (even if it exists)
    try:
        bucket = client.bucket(bucket_name)
        bucket.reload()  # Check if bucket exists
        print(f"  Deleting existing bucket: {bucket_name}")
        try:
            # Delete all blobs in the bucket first
            for blob in bucket.list_blobs():
                blob.delete()
            # Delete the bucket
            bucket.delete()
            print(f"  ✓ Bucket deleted successfully")
        except Exception as e:
            raise Exception(f"Failed to delete bucket '{bucket_name}': {e}")
    except NotFound:
        print(f"  Bucket does not exist, will create new one")
    
    # Create new bucket
    print(f"  Creating new bucket: {bucket_name}")
    try:
        bucket = client.create_bucket(bucket_name, location="us-central1")
        print(f"  ✓ Bucket created successfully")
    except Exception as e:
        raise Exception(f"Failed to create bucket '{bucket_name}': {e}")
    
    # Upload all files recursively
    uploaded_count = 0
    for file_path in output_path.rglob("*"):
        if file_path.is_file():
            # Get relative path from output directory
            relative_path = file_path.relative_to(output_path)
            blob_path = str(relative_path).replace("\\", "/")  # Use forward slashes for GCS
            
            # Create blob and upload
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(str(file_path))
            uploaded_count += 1
    
    gcs_path = f"gs://{bucket_name}/"
    print(f"\n✅ Successfully uploaded {uploaded_count} file(s) to {gcs_path}")
    return gcs_path


def main():
    """Main function to extract all MicroStrategy data with CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Extract MicroStrategy dossiers, documents, and reports for Looker migration assessment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all data from MicroStrategy server (using CLI arguments)
  microstrategy-assess --base-url https://your-server.com/MicroStrategyLibrary --username admin --password yourpass --output-dir output
  
  # Extract data using .env file (create .env with MSTR_BASE_URL, MSTR_USERNAME, MSTR_PASSWORD)
  microstrategy-assess --output-dir output
  
  # Extract data and upload to GCS (using CLI arguments)
  microstrategy-assess --output-dir output --gcp-project your-gcp-project --bucket-name assessment-json
  
  # Extract with .env credentials and upload to GCS (GCS settings from .env)
  # Add to .env: GCP_PROJECT=your-gcp-project, GCS_BUCKET_NAME=assessment-json
  microstrategy-assess --output-dir output
  
  # Mix: GCS project from CLI, bucket from .env
  microstrategy-assess --output-dir output --gcp-project your-gcp-project
        """
    )
    
    # Connection arguments (optional - can use .env file)
    parser.add_argument(
        "--base-url",
        type=str,
        help="MicroStrategy server base URL (e.g., https://your-server.com/MicroStrategyLibrary). Can also use MSTR_BASE_URL in .env file."
    )
    parser.add_argument(
        "--username",
        type=str,
        help="MicroStrategy username. Can also use MSTR_USERNAME in .env file."
    )
    parser.add_argument(
        "--password",
        type=str,
        help="MicroStrategy password. Can also use MSTR_PASSWORD in .env file."
    )
    
    # Output arguments (required)
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for extracted JSON files (required)"
    )
    
    parser.add_argument(
        "--consolidated-file",
        type=str,
        default="microstrategy_output_consolidated.json",
        help="Filename for consolidated JSON output (default: microstrategy_output_consolidated.json)"
    )
    
    # Optional GCS upload arguments (can use .env file)
    parser.add_argument(
        "--gcp-project",
        type=str,
        help="GCP project ID for uploading output to GCS bucket. Can also use GCP_PROJECT in .env file."
    )
    parser.add_argument(
        "--bucket-name",
        type=str,
        help="GCS bucket name for uploading output. Can also use GCS_BUCKET_NAME in .env file."
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("MicroStrategy Data Extraction Tool")
    print("=" * 60)
    
    # Debug: Show what credentials will be used (mask password)
    print(f"\nUsing MicroStrategy credentials:")
    if args.base_url:
        print(f"  BASE_URL: {args.base_url} (from CLI)")
    elif os.getenv("MSTR_BASE_URL"):
        print(f"  BASE_URL: {os.getenv('MSTR_BASE_URL')} (from .env)")
    else:
        print(f"  BASE_URL: Not set")
    
    if args.username:
        print(f"  USERNAME: {args.username} (from CLI)")
    elif os.getenv("MSTR_USERNAME"):
        print(f"  USERNAME: {os.getenv('MSTR_USERNAME')} (from .env)")
    else:
        print(f"  USERNAME: Not set")
    
    if args.password:
        print(f"  PASSWORD: *** (from CLI)")
    elif os.getenv("MSTR_PASSWORD"):
        print(f"  PASSWORD: *** (from .env)")
    else:
        print(f"  PASSWORD: Not set")
    
    print(f"  OUTPUT_DIR: {args.output_dir}")
    
    # Get GCS settings (CLI takes precedence over .env)
    gcp_project = args.gcp_project or os.getenv("GCP_PROJECT")
    bucket_name = args.bucket_name or os.getenv("GCS_BUCKET_NAME")
    
    # Show GCS settings only if at least one is configured
    if gcp_project or bucket_name:
        print(f"\nGCS Upload settings:")
        if args.gcp_project:
            print(f"  GCP_PROJECT: {args.gcp_project} (from CLI)")
        elif os.getenv("GCP_PROJECT"):
            print(f"  GCP_PROJECT: {os.getenv('GCP_PROJECT')} (from .env)")
        else:
            print(f"  GCP_PROJECT: Not set")
        
        if args.bucket_name:
            print(f"  BUCKET_NAME: {args.bucket_name} (from CLI)")
        elif os.getenv("GCS_BUCKET_NAME"):
            print(f"  BUCKET_NAME: {os.getenv('GCS_BUCKET_NAME')} (from .env)")
        else:
            print(f"  BUCKET_NAME: Not set")
    # If no GCS settings, silently skip (GCS upload is optional)
    
    # Initialize client with CLI arguments (CLI takes precedence over env vars)
    try:
        client = MicroStrategyClient(
            base_url=args.base_url,
            username=args.username,
            password=args.password
        )
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        return
    
    # Step 1: Login
    print("\n[Step 1] Logging in...")
    if not client.login():
        print("[ERROR] Login failed. Exiting.")
        return
    
    # Step 2: Get all projects
    print("\n[Step 2] Fetching projects...")
    projects = client.get_projects()
    
    if not projects:
        print("[ERROR] No projects found. Exiting.")
        return
    
    # Initialize data extractor
    extractor = DataExtractor(client)
    
    # Process each project
    projects_data = []
    
    for project in projects:
        project_id = project.get("id")
        project_name = project.get("name", "Unknown")
        
        print(f"\n{'=' * 60}")
        print(f"[INFO] Processing Project: {project_name} ({project_id})")
        print(f"{'=' * 60}")
        
        # Step 3: Get dossiers, documents, and reports
        print("\n[Step 3.1] Fetching dossiers...")
        dossiers = client.get_dossiers(project_id)
        print(f"  Found {len(dossiers)} dossiers")
        
        print("\n[Step 3.2] Fetching documents...")
        documents = client.get_documents(project_id)
        print(f"  Found {len(documents)} documents")
        
        print("\n[Step 3.3] Fetching reports...")
        reports = client.get_reports(project_id)
        print(f"  Found {len(reports)} reports")
        
        # Process dossiers
        dossier_data_list = []
        for dossier in dossiers:
            dossier_data = extractor.extract_dossier_data(project_id, dossier)
            dossier_data_list.append(dossier_data)
        
        # Process documents
        document_data_list = []
        for document in documents:
            document_data = extractor.extract_document_data(project_id, document)
            document_data_list.append(document_data)
        
        # Process reports
        report_data_list = []
        for report in reports:
            report_data = extractor.extract_report_data(project_id, report)
            report_data_list.append(report_data)
        
        projects_data.append({
            "id": project_id,
            "name": project_name,
            "dossiers": dossier_data_list,
            "documents": document_data_list,
            "reports": report_data_list
        })
    
    # Format and save output
    print("\n" + "=" * 60)
    print("Saving output files...")
    print("=" * 60)
    
    formatter = JSONFormatter()
    
    # Save split files (each dossier/document as separate file)
    formatter.save_split_files(projects_data, base_dir=args.output_dir)
    
    # Also save consolidated file for reference
    formatted_output = formatter.format_output(projects_data)
    consolidated_path = Path(args.output_dir) / args.consolidated_file
    consolidated_path.parent.mkdir(parents=True, exist_ok=True)
    formatter.save_to_file(formatted_output, filename=str(consolidated_path))
    
    print("\n[SUCCESS] Extraction complete!")
    print(f"   Processed {len(projects_data)} project(s)")
    print(f"   Output directory: {args.output_dir}")
    
    # Upload to GCS if arguments provided (from CLI or .env)
    if gcp_project and bucket_name:
        try:
            gcs_path = upload_output_to_gcs(
                gcp_project=gcp_project,
                bucket_name=bucket_name,
                output_dir=args.output_dir
            )
            print(f"   GCS path: {gcs_path}")
        except ImportError as e:
            print(f"\n⚠️  Warning: {e}")
            print("   Skipping GCS upload. Install with: pip install google-cloud-storage")
        except Exception as e:
            print(f"\n❌ Error uploading to GCS: {e}")
            import traceback
            traceback.print_exc()
    elif gcp_project or bucket_name:
        print(f"\n⚠️  Warning: Both GCP_PROJECT and GCS_BUCKET_NAME are required for GCS upload")
        print(f"   Provide via CLI (--gcp-project and --bucket-name) or .env file (GCP_PROJECT and GCS_BUCKET_NAME)")


if __name__ == "__main__":
    main()
