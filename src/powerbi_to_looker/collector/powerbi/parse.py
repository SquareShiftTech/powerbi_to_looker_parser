"""Run pbi-tools to extract .pbix into a folder. pbi_tools_exe from caller."""

import subprocess
from pathlib import Path


def run_pbi_tools(
    pbix_path: str | Path,
    output_path: str | Path,
    pbi_tools_exe: str | Path,
) -> None:
    """Run pbi-tools extract: pbix_path -> output_path. One folder per report.

    Args:
        pbix_path: Path to .pbix file.
        output_path: Directory to write extracted model (e.g. report folder).
        pbi_tools_exe: Path to pbi-tools executable (from orchestration).

    Raises:
        FileNotFoundError: If exe or pbix not found.
        subprocess.CalledProcessError: If pbi-tools exits non-zero.
    """
    pbix = Path(pbix_path)
    out = Path(output_path)
    exe = Path(pbi_tools_exe)
    if not exe.exists():
        raise FileNotFoundError(f"pbi-tools executable not found: {pbi_tools_exe}")
    if not pbix.exists():
        raise FileNotFoundError(f"PBIX file not found: {pbix_path}")
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(exe), "extract", str(pbix), "-outPath", str(out)],
        check=True,
        capture_output=True,
        timeout=300,
    )
