"""
LaTeX rendering helpers.

This module contains low-level helpers used when generating LaTeX code
for the font catalog. The functions here focus exclusively on producing
LaTeX-safe text fragments from arbitrary Unicode input.

Responsibilities
----------------
- Escape characters that have special meaning in LaTeX.
- Remove ASCII control characters that could break compilation.
- Provide safe detokenization helpers for embedding arbitrary text into
  LaTeX commands or environments.

Design principles
-----------------
These helpers are intentionally pure string transformations and must not
depend on catalog orchestration logic, inventory processing, or CLI code.
They form the lowest layer of the LaTeX subsystem and can be reused by
any module that needs to emit LaTeX-safe text.

Architectural role
------------------
This module belongs to the **LaTeX rendering infrastructure layer**. It
is used by higher-level catalog rendering modules (e.g. document or
sample rendering code) but does not perform any document assembly or
policy decisions itself.
"""

from fontshow.platform.runtime import IS_WINDOWS

# ============================================================
# LaTeX escaping utility
# ============================================================


def escape_latex(text: str) -> str:
    """
    Escape LaTeX special characters in a string.

    Parameters
    ----------
    text : str
        Input string to be escaped for safe inclusion in LaTeX source.

    Returns
    -------
    str
        String with LaTeX special characters escaped.
    """
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }
    return "".join(replacements.get(c, c) for c in text)


def _strip_ascii_control_chars(text: str) -> str:
    """
    Remove ASCII control characters from text before LaTeX insertion.

    Keeps newline (\\n) and tab (\\t); strips other chars in:
        U+0000–U+001F and U+007F
    """
    return "".join(
        ch for ch in text if ch in {"\n", "\t"} or (ord(ch) >= 0x20 and ord(ch) != 0x7F)
    )


def _latex_detokenize_safe(text: str) -> str:
    """
    Prepare text for safe inclusion inside \\detokenize{...}.

    Removes ASCII control characters and escapes closing braces,
    which would otherwise terminate the TeX group.
    """
    text = _strip_ascii_control_chars(text)
    return text.replace("}", r"\}")


def _renderer_option_prefix() -> str:
    """
    Return the fontspec Renderer option prefix.

    Notes
    -----
    - On Windows, omit Renderer=Harfbuzz to improve compatibility with the
      underlying luaotfload/font loader (deterministic fallback).
    - On non-Windows platforms, keep HarfBuzz enabled.
    """
    if IS_WINDOWS:
        return ""
    return "Renderer=Harfbuzz,"
