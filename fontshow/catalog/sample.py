"""
Catalog specimen selection helpers.

This module implements the logic used to select and render specimen
samples for fonts in the generated catalog.

Responsibilities
----------------
- Choose the most appropriate language to demonstrate a font
  (`choose_sample_language`).
- Select a representative text sample for the chosen language
  (`choose_sample_text`).
- Prepare the sample text for catalog rendering.
- Produce LaTeX-ready sample code snippets used in catalog entries.

Design principles
-----------------
Sample selection operates purely on inventory metadata and language
tables. The functions here decide *what* text should be shown for a
font but do not perform LaTeX escaping or low-level rendering. Those
tasks belong to the LaTeX subsystem (`fontshow.latex.render`).

Architectural role
------------------
This module belongs to the **catalog domain layer** and acts as the
bridge between font metadata (scripts, languages, coverage) and the
catalog rendering layer. It provides deterministic specimen selection
so that the same font always produces the same representative sample
in the catalog.
"""

from typing import cast

from fontshow.catalog.labels import primary_script
from fontshow.common.specimens import choose_language_sample
from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import FontRef, InferenceInfo, ScriptISO
from fontshow.inventory.metadata_processing import font_family
from fontshow.latex.policy import nfss_family_id
from fontshow.latex.render import _renderer_option_prefix, escape_latex
from fontshow.ontology.language_tables import SCRIPT_INFO


def choose_sample_language(font: dict) -> str | None:
    """
    Choose a representative language code for a font.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary possibly containing `inference`
        and `coverage` sections with language lists.

    Returns
    -------
    str | None
        First inferred language if available; otherwise the first
        declared coverage language; otherwise None.
    """
    inf = font.get("inference", {}) or {}
    langs = inf.get("languages", []) or []
    if langs:
        return str(langs[0])
    cov_langs = font.get("coverage", {}).get("languages", []) or []
    return str(cov_langs[0]) if cov_langs else None


def choose_sample_text(font: FontRef) -> str | None:
    """
    Choose a sample text for rendering.

    Parameters
    ----------
    font : FontRef
        Font descriptor containing optional embedded sample text and
        inference metadata.

    Returns
    -------
    str | None
        Selected sample text, or None if no suitable text is available.

    Notes
    -----
    Priority:
    1. Embedded sample text extracted from the font, only if its language
       matches the primary inferred language.
    2. Inferred language-based sample text (fallback).
    """

    inference_raw = font.get("inference")
    inference: InferenceInfo = inference_raw if isinstance(inference_raw, dict) else {}

    langs_raw = inference.get("languages")
    inferred_languages: list[str] = langs_raw if isinstance(langs_raw, list) else []

    # --- 1. Embedded sample text (if present and compatible) ---
    embedded = font.get("sample_text")
    if (
        isinstance(embedded, dict)
        and inferred_languages
        and embedded.get("lang") == inferred_languages[0]
        and embedded.get("text")
    ):
        text = embedded.get("text")
        if isinstance(text, str):
            return text
        return None

    # --- 2. Inferred language fallback ---
    scripts_raw = inference.get("scripts")
    inferred_scripts: list[str] = scripts_raw if isinstance(scripts_raw, list) else []

    sample = choose_language_sample(inferred_languages, inferred_scripts)
    if isinstance(sample, str):
        return sample

    return None


def render_sample_text(font: dict) -> str | None:
    """
    Produce a sample text string appropriate for the font classification.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary containing optional `classification`
        and rendering metadata.

    Returns
    -------
    str | None
        Sample text suitable for rendering, or None if no appropriate
        sample text can be determined.

    Notes
    -----
    Classification-specific overrides take precedence over general sample
    selection. Emoji fonts use a fixed emoji specimen, decorative fonts
    use the family name, and all other fonts delegate to
    `choose_sample_text`.
    """
    cls = font.get("classification", {}) or {}
    fam = font_family(font)
    if cls.get("is_emoji"):
        return "😀 😃 😄 😁 😆 😅 😂 🤣 😊 😇"
    if cls.get("is_decorative"):
        return fam
    return choose_sample_text(cast("FontRef", font))


def render_sample_code(font: dict, fam: str) -> str:
    """
    Build the LaTeX snippet used to render the font sample.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary containing classification and
        inference metadata.
    fam : str
        Font family name used for LaTeX rendering.

    Returns
    -------
    str
        LaTeX code snippet rendering the sample text for the font.

    Notes
    -----
    Rendering constraints:
    - Never request Bold / Italic / BoldItalic shapes.
    - Do not propagate inferred weight/width/style metadata.
    - For RTL scripts use `TestNonLatin` (polyglossia + harfbuzz).
    - For LTR scripts use a minimal, NFSS-safe `fontspec` invocation.
    """
    log_trace_cat(
        log,
        "latex",
        "rendering sample code",
        extra={
            "family": fam,
        },
    )

    txt = render_sample_text(font)
    ps = primary_script(font)

    nfss_id = nfss_family_id(font)
    renderer_prefix = _renderer_option_prefix()

    # -------------------------------------------------
    # Direction-aware rendering (script policy driven)
    # -------------------------------------------------
    script_iso = ScriptISO(ps.upper()) if ps else None
    info = SCRIPT_INFO.get(script_iso) if script_iso else None

    if info and info["requires_polyglossia"]:
        lang = info["polyglossia_language"]
        opts = info["fontspec_opts"]

        # Ensure specimen exists
        if not txt:
            langs = [lang] if isinstance(lang, str) else None
            scripts = [ps] if isinstance(ps, str) else None
            txt = choose_language_sample(langs, scripts) or ""

        return (
            r"\TestNonLatin{"
            + escape_latex(fam)
            + r"}{"
            + lang
            + r"}{"
            + opts
            + r"}{"
            + escape_latex(txt)
            + r"}"
        )

    if not txt:
        return (
            r"\textbf{Sample:}"
            "\n"
            r"{\mdseries\upshape\fontspec[" + renderer_prefix + f"Family={nfss_id},"
            r"UprightFont=*,"
            r"BoldFont={},"
            r"ItalicFont={},"
            r"BoldItalicFont={}"
            r"]{" + escape_latex(fam) + r"}\Li}"
        )

    return (
        r"\textbf{Esempio:}"
        "\n"
        r"{\mdseries\upshape\fontspec[" + renderer_prefix + f"Family={nfss_id},"
        r"UprightFont=*,"
        r"BoldFont={},"
        r"ItalicFont={},"
        r"BoldItalicFont={}"
        r"]{" + escape_latex(fam) + r"}" + escape_latex(txt) + r"}"
    )
