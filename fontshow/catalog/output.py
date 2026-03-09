"""
Catalog output helpers.

This module contains utilities used by the catalog generation pipeline
to determine output filenames and write the generated LaTeX catalog to
disk.

Responsibilities
----------------
- Generate unique output filenames when collisions occur.
- Determine the final output filename used by the catalog pipeline.
- Write the generated LaTeX document to the filesystem.

Design principles
-----------------
These helpers perform filesystem operations and output management but
contain no catalog rendering or inventory processing logic. They exist
to keep the catalog pipeline module focused on orchestration while
isolating file I/O responsibilities.

Architectural role
------------------
This module belongs to the **catalog pipeline infrastructure layer** and
is used by the create-catalog workflow to persist generated catalog
documents.
"""

import platform
from pathlib import Path

from fontshow.constants.runtime import DATE_STR
from fontshow.core.cli_utils import log_err, log_info, log_ok


def get_unique_filename(base_name: str, extension: str) -> str:
    """
    Generate a unique filename by appending a three-digit counter (000–999).

    Parameters
    ----------
    base_name : str
        Base filename without extension.
    extension : str
        File extension without leading dot.

    Returns
    -------
    str
        A filename of the form:
            <base_name>_<NNN>.<extension>
        where NNN is the first available counter between 000 and 999.

    Raises
    ------
    ValueError
        If no available filename is found after 1000 attempts.
    """
    for i in range(1000):
        suffix = f"_{i:03d}"
        filename = f"{base_name}{suffix}.{extension}"
        if not Path(filename).exists():
            return filename
    msg = f"Impossibile trovare un nome file unico per {base_name}.{extension} dopo 1000 tentativi."
    raise ValueError(msg)


def _prepare_output_filename() -> tuple[int, str | None]:
    """
    Build a unique output filename based on platform and DATE_STR.

    Parameters
    ----------
    None

    Returns
    -------
    tuple[int, str | None]
        A pair (exit_code, filename):
        - exit_code == 0 → success, filename contains the generated name.
        - exit_code == 1 → error already logged, filename is None.
    """
    base_name = f"fontshow_{platform.system()}_{DATE_STR}"

    try:
        output_filename = get_unique_filename(base_name, "tex")
    except ValueError as e:
        log_err(f"Error: {e}")
        return 1, None
    else:
        return 0, output_filename


def _write_latex_output(output_filename: str, latex_content: str) -> None:
    """
    Write generated LaTeX catalog to disk and emit user messages.

    Parameters
    ----------
    output_filename : str
        Target filename for the LaTeX document.
    latex_content : str
        Full LaTeX document content to be written.

    Returns
    -------
    None

    Notes
    -----
    In addition to writing the file, this helper emits completion messages
    and prints the recommended two-pass `lualatex` compilation command.
    """
    log_info(f"Writing file {output_filename}...")

    with Path(output_filename).open("w", encoding="utf-8") as f:
        f.write(latex_content)

    log_ok("Done! LaTeX file generated successfully.")
    log_ok("Ready for compilation.")
    log_ok(
        f"  Execute: lualatex -interaction=nonstopmode {output_filename} | texlogsieve (twice)"
    )
