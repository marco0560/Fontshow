import shutil


def has_lualatex() -> bool:
    """
    Detect availability of the LuaLaTeX engine.

    Returns True if lualatex is found in PATH, False otherwise.
    """
    return shutil.which("lualatex") is not None
