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

    Notes
    -----
    Escaping is character-based and deterministic. The helper does not
    attempt full LaTeX lexical analysis.
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
    r"""
    Remove ASCII control characters from text before LaTeX insertion.

    Parameters
    ----------
    text : str
        Input text that may contain ASCII control characters.

    Returns
    -------
    str
        Text with control characters removed, except for newline and tab.

    Notes
    -----
    Keeps newline (``\\n``) and tab (``\\t``); strips other characters
    in the ranges ``U+0000-U+001F`` and ``U+007F``.
    """
    return "".join(
        ch for ch in text if ch in {"\n", "\t"} or (ord(ch) >= 0x20 and ord(ch) != 0x7F)
    )


def _latex_detokenize_safe(text: str) -> str:
    r"""
    Prepare text for safe inclusion inside ``\\detokenize{...}``.

    Parameters
    ----------
    text : str
        Input text to sanitize.

    Returns
    -------
    str
        Sanitized text safe for placement inside ``\\detokenize{...}``.

    Notes
    -----
    Removes ASCII control characters and escapes braces, which would
    otherwise terminate the TeX group inside ``\\\\detokenize{...}``.
    """
    text = _strip_ascii_control_chars(text)
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def _latex_debug_literal(text: str) -> str:
    """
    Render debug text safely while preserving human-readable braces.

    Parameters
    ----------
    text : str
        Raw debug text to render in LaTeX.

    Returns
    -------
    str
        LaTeX-safe debug text suitable for direct insertion in
        monospaced inline output.

    Notes
    -----
    This helper differs from :func:`escape_latex` because it renders
    literal braces via character codes so values such as
    ``Script={Hanifi Rohingya}`` remain human-readable instead of
    showing brace escapes in the debug output.
    """
    text = _strip_ascii_control_chars(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\char123{}",
        "}": r"\char125{}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }
    return "".join(replacements.get(c, c) for c in text)


def _renderer_option_prefix() -> str:
    """
    Return the fontspec Renderer option prefix.

    Parameters
    ----------
    None

    Returns
    -------
    str
        ``"Renderer=Harfbuzz,"`` on non-Windows platforms, otherwise an
        empty string.

    Notes
    -----
    - On Windows, omit Renderer=Harfbuzz to improve compatibility with the
      underlying luaotfload/font loader (deterministic fallback).
    - On non-Windows platforms, keep HarfBuzz enabled.
    """
    if IS_WINDOWS:
        return ""
    return "Renderer=Harfbuzz,"
