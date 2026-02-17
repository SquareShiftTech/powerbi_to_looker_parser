"""Extract Report content from .pbix zip when pbi-tools did not write a Report folder."""

import zipfile
from pathlib import Path


def extract_report_from_pbix(pbix_path: str | Path, out_folder: str | Path) -> int:
    """Extract all Report-related entries from .pbix (ZIP) into out_folder.

    Use when pbi-tools extract succeeds but does not create Report/sections.
    .pbix is a ZIP; entries may be "Report/Layout", "Report/Sections/...", etc.

    Args:
        pbix_path: Path to the .pbix file.
        out_folder: Directory to extract into (same as parsed output folder).

    Returns:
        Number of members extracted.

    Raises:
        FileNotFoundError: If pbix_path does not exist.
        zipfile.BadZipFile: If the file is not a valid ZIP.
    """
    pbix = Path(pbix_path)
    out = Path(out_folder)
    if not pbix.exists():
        raise FileNotFoundError(f"PBIX file not found: {pbix_path}")

    count = 0
    with zipfile.ZipFile(pbix, "r") as zf:
        for name in zf.namelist():
            # Normalize: ZIP often uses forward slashes; accept Report (case-insensitive)
            normalized = name.replace("\\", "/").strip("/")
            lower = normalized.lower()
            if lower == "report" or lower.startswith("report/"):
                zf.extract(name, out)
                count += 1
    return count
