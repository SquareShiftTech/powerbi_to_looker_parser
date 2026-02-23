"""Push generator_output to GitHub repository.

Uploads the generator_output directory to a GitHub repository on a specific branch.
Deletes any extra files or folders in the repository that are not present locally.

Usage:
    python scripts/push_to_github.py
    python scripts/push_to_github.py --generator-output-dir generator_output --repo owner/repo --branch main

Environment Variables:
    GITHUB_TOKEN: Personal access token for GitHub authentication (required)
    GITHUB_REPO or GITHUB_REPO_URL: The name of the GitHub repository (e.g., "username/repo") or full URL (e.g., "https://github.com/owner/repo.git")
    GITHUB_BRANCH: The name of the branch to upload files to (default: main)
    GITHUB_FOLDER: Optional subfolder name to push (e.g., "Education_24b04535"). If specified, only this subfolder is pushed.
    LOOKER_PROJECT_URL: Optional Looker project URL to display in success message
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from github import Github, GithubException
except ImportError:
    print(
        "Error: PyGithub is not installed. Install it with: pip install PyGithub",
        file=sys.stderr,
    )
    sys.exit(1)


def debug(message: str, verbose: bool = False) -> None:
    """Print debug message if verbose is True."""
    if verbose:
        print(message)


def get_github_files_and_dirs(
    git_repo, branch_name: str, path: str = "", verbose: bool = False
) -> dict[str, str]:
    """Recursively get all files and directories from GitHub repository.

    Returns:
        Dictionary mapping file/directory paths to their type ("file" or "dir").
    """
    items = {}
    try:
        contents = git_repo.get_contents(path, ref=branch_name)
        if not isinstance(contents, list):
            contents = [contents]
        for content in contents:
            if content.type == "dir":
                items[content.path] = "dir"
                items.update(get_github_files_and_dirs(git_repo, branch_name, content.path, verbose))
            else:
                items[content.path] = "file"
    except GithubException as e:
        if e.status != 404:  # 404 means path doesn't exist, which is fine
            debug(f"Error getting contents for {path}: {e}", verbose)
    return items


def extract_repo_name_from_url(repo_url: str) -> str:
    """Extract owner/repo from GitHub URL.

    Supports formats:
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo
    - git@github.com:owner/repo.git
    - owner/repo

    Returns:
        Repository name in format "owner/repo"
    """
    # If already in owner/repo format, return as-is
    if "/" in repo_url and not repo_url.startswith(("http", "git@")):
        return repo_url

    # Remove .git suffix if present
    repo_url = repo_url.rstrip(".git")

    # Handle git@github.com:owner/repo format
    if repo_url.startswith("git@github.com:"):
        return repo_url.replace("git@github.com:", "")

    # Handle https://github.com/owner/repo format
    if "github.com/" in repo_url:
        parts = repo_url.split("github.com/")
        if len(parts) > 1:
            return parts[1]

    # If we can't parse it, return as-is (might already be owner/repo)
    return repo_url


def get_local_files_and_dirs(local_folder_path: Path, subfolder: str | None = None) -> dict[str, str]:
    """Get all files and directories from local directory, optionally filtered by subfolder.

    Args:
        local_folder_path: Base directory path
        subfolder: Optional subfolder name to filter by (e.g., "Education_24b04535")

    Returns:
        Dictionary mapping relative file/directory paths to their type ("file" or "dir").
        If subfolder is specified, paths are relative to the subfolder (not the base path).
    """
    local_files_and_dirs = {}
    
    # If subfolder is specified, only process that subfolder
    if subfolder:
        subfolder_path = local_folder_path / subfolder
        if not subfolder_path.exists():
            return local_files_and_dirs
        walk_path = subfolder_path
        base_path = subfolder_path
    else:
        walk_path = local_folder_path
        base_path = local_folder_path
    
    for root, dirs, files in os.walk(walk_path):
        for file_name in files:
            local_file_path = Path(root) / file_name
            relative_path = local_file_path.relative_to(base_path)
            relative_path_str = str(relative_path).replace(os.path.sep, "/")  # Fix for Windows
            local_files_and_dirs[relative_path_str] = "file"

        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            relative_path = dir_path.relative_to(base_path)
            relative_path_str = str(relative_path).replace(os.path.sep, "/")  # Fix for Windows
            local_files_and_dirs[relative_path_str] = "dir"
    return local_files_and_dirs


def upload_to_github(
    local_folder_path: Path,
    github_token: str,
    github_repo_name: str,
    github_branch_name: str,
    looker_project_url: str | None = None,
    subfolder: str | None = None,
    verbose: bool = False,
) -> tuple[str, int]:
    """Upload a local folder and its files to a GitHub repository on a specific branch.

    Deletes any extra files or folders in the repository that are not present locally.

    Args:
        local_folder_path: Path to the local folder to upload.
        github_token: Personal access token for GitHub authentication.
        github_repo_name: The name of the GitHub repository (e.g., "username/repo").
        github_branch_name: The name of the branch to upload files to.
        looker_project_url: Optional Looker project URL to display in success message.
        subfolder: Optional subfolder name to push (e.g., "Education_24b04535"). If specified, only this subfolder is pushed.
        verbose: Whether to print debug messages.

    Returns:
        Tuple of (message, status_code) where status_code is 200 for success, 500 for error.
    """
    if not github_token or not github_repo_name or not github_branch_name:
        message = "Either GITHUB_TOKEN, GITHUB_REPO, or GITHUB_BRANCH not available"
        debug(message, verbose)
        return message, 500

    if not local_folder_path.exists():
        message = f"Local folder does not exist: {local_folder_path}"
        debug(message, verbose)
        return message, 500

    try:
        debug("Initializing Github Client", verbose)
        git_client = Github(github_token)

        git_repo = git_client.get_repo(github_repo_name)
        debug(f"Authenticated to GitHub repository: {github_repo_name}", verbose)

        # Check if branch exists
        try:
            git_repo.get_branch(github_branch_name)
            debug(f"Branch '{github_branch_name}' found.", verbose)
        except GithubException as e:
            message = f"Branch '{github_branch_name}' not found: {e}"
            debug(message, verbose)
            return message, 500

        # Get all files and folders from the GitHub repository
        debug(f"Getting contents from Branch {github_branch_name}", verbose)
        github_files_and_dirs = get_github_files_and_dirs(git_repo, github_branch_name, verbose=verbose)
        debug(
            f"Found {len(github_files_and_dirs)} files/folders in the GitHub repository.",
            verbose,
        )

        # Determine the actual source path (base or subfolder)
        if subfolder:
            source_path = local_folder_path / subfolder
            if not source_path.exists():
                message = f"Subfolder '{subfolder}' does not exist in {local_folder_path}"
                debug(message, verbose)
                return message, 500
            debug(f"Pushing only subfolder: {subfolder}", verbose)
        else:
            source_path = local_folder_path

        # Get all files and folders from the local directory
        local_files_and_dirs = get_local_files_and_dirs(local_folder_path, subfolder)
        debug(
            f"Found {len(local_files_and_dirs)} files/folders in the local directory.",
            verbose,
        )

        # Delete files/folders in GitHub that are not present locally
        # If subfolder is specified, only delete files within that subfolder path
        deleted_count = 0
        for github_path, github_type in github_files_and_dirs.items():
            # If subfolder is specified, only consider files in that subfolder path
            if subfolder:
                if not github_path.startswith(subfolder + "/") and github_path != subfolder:
                    continue
                # Remove subfolder prefix for comparison with local files
                relative_path = github_path[len(subfolder) + 1:] if github_path.startswith(subfolder + "/") else github_path
            else:
                relative_path = github_path
            
            if relative_path not in local_files_and_dirs:
                if github_type == "file":
                    try:
                        repo_file = git_repo.get_contents(github_path, ref=github_branch_name)
                        git_repo.delete_file(
                            repo_file.path,
                            f"Delete {github_path}",
                            repo_file.sha,
                            branch=github_branch_name,
                        )
                        debug(f"Deleted file: {github_path}", verbose)
                        deleted_count += 1
                    except GithubException as e:
                        debug(f"Error deleting file {github_path}: {e}", verbose)
                elif github_type == "dir":
                    debug(
                        f"Extra folder detected: {github_path}. Note: GitHub API does not directly support deleting folders.",
                        verbose,
                    )

        # Upload or update files from the local directory
        created_count = 0
        updated_count = 0
        for local_path, local_type in local_files_and_dirs.items():
            if local_type == "file":
                local_file_path = source_path / local_path
                # If subfolder is specified, prefix the GitHub path with the subfolder name
                github_path = f"{subfolder}/{local_path}" if subfolder else local_path
                
                try:
                    with open(local_file_path, "rb") as file:  # Open in binary mode
                        content = file.read()

                    # Try to decode as UTF-8 (for text files like .lkml)
                    try:
                        content_text = content.decode("utf-8")
                    except UnicodeDecodeError:
                        error_message = f"File '{local_path}' is not valid UTF-8 text. Binary files are not supported."
                        debug(error_message, verbose)
                        return error_message, 500

                    # Upload or update file in the repository
                    try:
                        repo_file = git_repo.get_contents(github_path, ref=github_branch_name)
                        git_repo.update_file(
                            repo_file.path,
                            f"Update {github_path}",
                            content_text,
                            repo_file.sha,
                            branch=github_branch_name,
                        )
                        debug(f"Updated: {github_path}", verbose)
                        updated_count += 1
                    except GithubException:
                        git_repo.create_file(
                            github_path,
                            f"Add {github_path}",
                            content_text,
                            branch=github_branch_name,
                        )
                        debug(f"Created: {github_path}", verbose)
                        created_count += 1

                except Exception as file_error:
                    error_message = f"Error processing file '{local_path}': {file_error}"
                    debug(error_message, verbose)
                    return error_message, 500

        success_message = f"Successfully updated GitHub repository '{github_repo_name}' on branch '{github_branch_name}'\n"
        success_message += f"  Created: {created_count} files\n"
        success_message += f"  Updated: {updated_count} files\n"
        success_message += f"  Deleted: {deleted_count} files\n"
        if looker_project_url:
            success_message += f"\nLooker project URL: {looker_project_url}"
        debug(success_message, verbose)
        return success_message, 200

    except GithubException as github_error:
        error_message = f"Unexpected error occurred in github\n\nError: {github_error}"
        debug(error_message, verbose)
        return error_message, 500
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        debug(error_message, verbose)
        return error_message, 500


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Upload generator_output directory to GitHub repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--generator-output-dir",
        type=Path,
        default=Path("generator_output"),
        help="Path to generator output directory (default: generator_output)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=os.environ.get("GITHUB_REPO") or os.environ.get("GITHUB_REPO_URL"),
        help="GitHub repository name (e.g., 'owner/repo') or URL. Can also be set via GITHUB_REPO or GITHUB_REPO_URL env var.",
    )
    parser.add_argument(
        "--branch",
        type=str,
        default=os.environ.get("GITHUB_BRANCH", "main"),
        help="GitHub branch name (default: main, or GITHUB_BRANCH env var)",
    )
    parser.add_argument(
        "--looker-project-url",
        type=str,
        default=os.environ.get("LOOKER_PROJECT_URL"),
        help="Optional Looker project URL to display in success message. Can also be set via LOOKER_PROJECT_URL env var.",
    )
    parser.add_argument(
        "--folder",
        type=str,
        default=os.environ.get("GITHUB_FOLDER"),
        help="Optional subfolder name to push (e.g., 'Education_24b04535'). If specified, only this subfolder is pushed. Can also be set via GITHUB_FOLDER env var.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print debug messages",
    )
    args = parser.parse_args()

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print(
            "Error: GITHUB_TOKEN environment variable is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.repo:
        print(
            "Error: --repo argument or GITHUB_REPO/GITHUB_REPO_URL environment variable is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Extract repo name from URL if needed
    repo_name = extract_repo_name_from_url(args.repo)

    generator_output_dir = args.generator_output_dir.resolve()
    if not generator_output_dir.exists():
        print(
            f"Error: Generator output directory does not exist: {generator_output_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    message, status_code = upload_to_github(
        generator_output_dir,
        github_token,
        repo_name,
        args.branch,
        args.looker_project_url,
        subfolder=args.folder,
        verbose=args.verbose,
    )

    print(message)
    if status_code != 200:
        sys.exit(1)


if __name__ == "__main__":
    main()
