"""Single extract: run pbi-tools on .pbix; parsed output stored in folder. Exe path from orchestrator."""

from pathlib import Path


def extract_to_folder(
    pbix_path: str | Path,
    output_path: str | Path,
    pbi_tools_exe: str | Path,
) -> str:
    """Run pbi-tools on .pbix; write all parsed output to output_path. Returns output_path.

    Args:
        pbix_path: Path to .pbix file.
        output_path: Directory to write parsed/extracted content (e.g. report folder).
        pbi_tools_exe: Path to pbi-tools executable (from orchestrator).

    Returns:
        Resolved output path as string.

    Raises:
        FileNotFoundError: If exe or pbix not found.
        subprocess.CalledProcessError: If pbi-tools exits non-zero.
    """
    from powerbi_to_looker.collector.powerbi.parse import run_pbi_tools

    run_pbi_tools(pbix_path, output_path, pbi_tools_exe)
    return str(Path(output_path).resolve())
