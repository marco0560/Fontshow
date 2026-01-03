# fontshow/preflight/checks/font_discovery.py

import shutil


def has_fontconfig() -> bool:
    """
    Detect availability of fontconfig (fc-list).

    Returns True if fc-list is found in PATH, False otherwise.
    """
    return shutil.which("fc-list") is not None
