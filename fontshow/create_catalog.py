"""
Fontshow create-catalog module.

This module implements the LaTeX catalog generation stage of the Fontshow
pipeline.

Responsibilities
----------------
- Load and strictly validate a schema v1.2 inventory.
- Enforce platform compatibility constraints.
- Perform semantic validation.
- Transform normalized font descriptors into deterministic LaTeX output.
- Provide CLI orchestration for the `create-catalog` command.

Design constraints
------------------
- Pure rendering stage: no font binary inspection.
- Inventory-driven: all semantic information originates from JSON.
- Deterministic output: stable ordering and identifiers.
- LaTeX-first: optimized for LuaLaTeX workflows.
- Whitespace-sensitive templates: LaTeX blocks must not be modified
  unintentionally.

Primary entry points
--------------------
- `run_create_catalog(args)`
- `generate_latex(font_list)`

All rendering decisions must operate exclusively on normalized font
descriptors.
"""

import argparse
import hashlib
import json
import platform
import re
import sys
from collections import OrderedDict
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, cast

from fontshow import __version__
from fontshow.cli_utils import (
    add_common_arguments,
    log_err,
    log_info,
    log_ok,
    log_warn,
    set_cli_mode,
)
from fontshow.global_constants import SCHEMA_VERSION
from fontshow.json_boundary import normalize_loaded_enums
from fontshow.logging_utils import log, log_trace_cat
from fontshow.platform_metadata import collect_platform_metadata
from fontshow.semantic_validation import enforce_semantic_validation
from fontshow.types import (
    CatalogFontEntryV12,
    FontRef,
    InferenceInfo,
    Severity,
)

# Platform-specific imports (deferred, typing-safe)
if TYPE_CHECKING:
    import winreg as _winreg  # noqa: F401

    winreg: Any
else:
    try:
        import winreg  # type: ignore
    except ImportError:
        winreg = None

if sys.platform == "win32":
    # modulo specifico Windows
    IS_WINDOWS = True
    IS_LINUX = False
elif sys.platform.startswith("linux"):
    IS_LINUX = True
    IS_WINDOWS = False
    # eventuale alternativa per altri OS
    # Define a non-Windows placeholder so static checkers won't flag missing 'winreg'
    winreg = None
else:
    IS_WINDOWS = False
    IS_LINUX = False
    winreg = None  # Placeholder for non-Windows systems

# --- Configuration ---
DATE_STR = datetime.now().strftime("%Y%m%d")
TEST_FONTS: set[str] = set()
DEFAULT_INVENTORY = "font_inventory_enriched.json"

EXCLUDED_FONTS: set[str]
DEFAULT_TEST_FONTS: set[str]

if IS_WINDOWS:
    EXCLUDED_FONTS = set()
    DEFAULT_TEST_FONTS = {"Times New Roman", "Arial", "Calibri", "Noto Sans"}
elif IS_LINUX:
    EXCLUDED_FONTS = {
        "MuseJazz Text",
        "MnSymbol",
    }
    DEFAULT_TEST_FONTS = {
        "Times New Roman",
        "Arial",
        "Calibri",
        "Noto Sans Buginese",
        "Noto Sans Buhid",
        "Noto Sans Yi",
        "Noto Sans Devanagari Light",
        "Noto Sans Arabic",
        "Noto Sans Hebrew",
        "Noto Sans Thai",
        "Noto Sans Armenian",
        "Noto Sans Ethiopic",
        "Noto Sans Bengali",
        "Noto Sans Tamil",
        "Noto Sans Khmer",
        "Noto Sans Lao",
        "Noto Sans Myanmar",
        "Noto Sans Georgian",
        "Noto Sans Cherokee",
        "Noto Serif TC",
        "Noto Serif Hentaigana",
        "Bandal",
    }
else:
    EXCLUDED_FONTS = set()
    DEFAULT_TEST_FONTS = set()

# ============================================================
# Sample texts (language-aware)
# ============================================================

SAMPLE_TEXTS = {
    "en": "The quick brown fox jumps over the lazy dog",
    "it": "Ma la volpe col suo balzo ha raggiunto il quieto Fido",
    "fr": "Portez ce vieux whisky au juge blond qui fume",
    "de": "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich",
    "es": "El veloz murciélago hindú comía feliz cardillo y kiwi",
    "el": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία",
    "ru": "Съешь же ещё этих мягких французских булок",
    "hy": "Վարդագույն աղվեսը ցատկում է ծույլ շան վրայով",
    "ja": "いろはにほへと ちりぬるを",
    "vi": "Chữ Việt rất phong phú và đa dạng",
    "zh": "天地玄黃 宇宙洪荒",
    "ar": "صِفْ خَلْقَ خَوْدٍ كَمِثْلِ الشَّمْسِ",
    "he": "דג סקרן שט בים מאוכזב ולפתע מצא לו חברה",
    "ko": "키스의 고유조건은 입술끼리 만나야 하고 특별한 기술은 필요치 않다",
    "cop": "Ⲡⲁⲓ ⲙⲉⲧⲁⲛⲟⲓⲁ",
    "ti": "ሰላም እንታይ ከመይ ኢኻ",
    "ta": "யாதும் ஊரே யாவரும் கேளிர்",
    "te": "అన్ని మానవజాతులు స్వేచ్ఛగా జన్మించాయి, అందరికీ సమానమైన గౌరవం మరియు హక్కులు ఉన్నాయి",
}

RTL_SCRIPTS = {"arab", "hebr"}

SCRIPT_TO_POLYGLOSSIA = {
    "arab": ("arabic", "Script=Arabic"),
    "hebr": ("hebrew", "Script=Hebrew"),
}

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


# ============================================================
# LaTeX rendering logic
# ============================================================
#
# This section is responsible for transforming normalized font descriptors
# into LaTeX source code. It deliberately contains *no font inspection logic*:
# all decisions are based exclusively on the inventory JSON structure.
#
# Key design constraints:
# - LaTeX output must be stable and reproducible.
# - Missing metadata must never break rendering.
# - Right-to-left scripts are handled conservatively.
# - Templates are kept explicit (no metaprogramming) for debuggability.
#
# IMPORTANT:
#   Whitespace inside LaTeX templates is semantically relevant.
#   Changes here must avoid altering indentation or line breaks unless
#   explicitly intended.
#
LATEX_INITIAL_CODE: str = (
    r"""% !TeX TS-program = lualatex
% !TeX spellcheck = en_US
% !TeX encoding = UTF-8
\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\ExplSyntaxOn
\msg_redirect_name:nnn {fontspec} {font-not-found} {warning}
\ExplSyntaxOff
\usepackage{polyglossia}
\usepackage{lipsum}
\usepackage{xcolor}
\usepackage{tcolorbox}
\usepackage{geometry}
\usepackage{fancyhdr}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{multicol}
\usepackage{pdftexcmds}

\setmainlanguage{english}
% Secondary languages for testing non-Latin scripts
\setotherlanguage{latin}
\setotherlanguage{arabic}
\setotherlanguage{hebrew}
\setotherlanguage{japanese}
\setotherlanguage{chinese}
\setotherlanguage{hindi}
\setotherlanguage{thai}

\geometry{margin=2cm}

% --- Utility Macros ---
\makeatletter
\newcommand{\ifFileNotEmpty}[3]{%
	\IfFileExists{#1}{%
		% \pdf@filesize gives size in byte
		\ifnum\pdf@filesize{#1}>0
		#2% if it exists and has at least 1 byte
		\else
		#3% if it exists but is 0 bytes
		\fi
	}{%
		#3% if the file doesn't exist at all
	}%
}
\makeatother

% --- Macro per sezioni riepilogative ---
% #1 filename #2 title of section
\newcommand{\FileSec}[2]{%
	\ifFileNotEmpty{#1}{%
		\section{#2}
		\begin{multicols}{2}
			\begin{itemize}
				\input{#1}
			\end{itemize}
		\end{multicols}
	}
	{}
}
% ---------------------------------------

% Colori
\definecolor{titlecolor}{HTML}{667eea}
\definecolor{boxcolor}{HTML}{f0f0f0}
\definecolor{successcolor}{HTML}{28a745}
\definecolor{errorcolor}{HTML}{dc3545}
\definecolor{othercolor}{HTML}{0d6efd}

% Setup Box
%\tcbuselibrary{skins}
%\newtcolorbox{fontbox}[1]{
%    colback=boxcolor, colframe=titlecolor, boxrule=1pt, arc=3pt,
%    title={\textbf{#1}}, coltitle=white, colbacktitle=titlecolor
%}
\newenvironment{fontbox}[1]{}{}
%\newtcolorbox{errorbox}[1]{
%    colback=errorcolor!10, colframe=errorcolor!80!black, boxrule=1pt, arc=3pt,
%    title={\textbf{Non Caricato: #1}}, coltitle=white, colbacktitle=errorcolor!80!black%
%}
\newenvironment{errorbox}[1]{}{}

% --- MACRO PER CARATTERI NON LATINI (FIXED) ---
% #1: Font Name, #2: Language Tag (polyglossia), #3: Font Options (e.g., Script=Arabic), #4: Sample Text
\newcommand{\TestNonLatin}[4]{%
	\par\noindent\textbf{Test in Lingua (\texttt{#2}) with Options: \texttt{[#3]}}

	\foreignlanguage{#2}{%
		\fontspec[BoldFont={},ItalicFont={},BoldItalicFont={},#3]{#1}%
		#4\par
	}%
	\vspace{0.5em}
}
% --------------------------------------

% --- GESTIONE CONTATORI E INDICI ---
\newcounter{cntWorking}
\newcounter{cntBroken}
\newcounter{cntExcluded}
\setcounter{cntWorking}{0}
\setcounter{cntBroken}{0}
\setcounter{cntExcluded}{0}

% Definiamo file di output temporanei per gli indici
\newwrite\fileWorking
\immediate\openout\fileWorking=\jobname.working
\newwrite\fileBroken
\immediate\openout\fileBroken=\jobname.broken
\newwrite\fileExcluded
\immediate\openout\fileExcluded=\jobname.excluded

% Macro ROBUSTE per registrare i font (evita errori di espansione)
\protected\def\LogWorking#1{%
    \stepcounter{cntWorking}%
%    \immediate\write\fileWorking{\string\item\space\detokenize{#1}}%
}

\protected\def\LogBroken#1{%
    \stepcounter{cntBroken}%
%    \immediate\write\fileBroken{\string\item\space\detokenize{#1}}%
}

\protected\def\LogExcluded#1{%
    \stepcounter{cntExcluded}%
%    \immediate\write\fileExcluded{\string\item\space\detokenize{#1}}%
}
% -----------------------------------

\SetLipsumText{cicero}
\newcommand{\Li}{\lipsum[1][1-4]}

\title{\Huge\textbf{\color{titlecolor}Catalogo Font di Sistema}}
\author{Generato da fontshow.create\_catalog """
    + escape_latex(__version__)
    + r""" \texttt{"""
    + escape_latex(platform.system())
    + r"""}}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
This document catalogs the fonts installed on the system.
Problematic fonts are excluded in advance. The compilation is performed with \textbf{LuaLaTeX}.
\end{abstract}

\tableofcontents
\newpage

\section{Detailed Catalog}
"""
)
# -------------------------------------------
SAMPLE_1: str = r"""\textbf{Sample:}
\begingroup
\IfFontExistsTF{"""
# --------------------------------------------
SAMPLE_2: str = r"""}
{\tempfont\Li}
\endgroup
"""
# --------------------------------------------

NORMAL_BLOCK: str = """\\subsection{{{safe_name}}}

{badges}

\\IfFontExistsTF{{{font}}}{{%
    \\LogWorking{{{safe_name}}}
    \\begin{{fontbox}}{{{safe_name}}}
        \\centering \\Large A B C D E 1 2 3
    \\end{{fontbox}}
    \\vspace{{0.5em}}
    {sample_code}
}}{{
    \\LogBroken{{{safe_name}}}
    \\begin{{errorbox}}{{{safe_name}}}
        Font exists in the system but is not loadable by LuaLaTeX.
    \\end{{errorbox}}
}}

\\vspace{{1em}}
"""
# --------------------------------------------
LATEX_END_CODE_1: str = r"""\newpage

% Chiusura file degli indici
\immediate\closeout\fileWorking
\immediate\closeout\fileBroken
\immediate\closeout\fileExcluded

\section{Summary and Statistics}

\begin{tcolorbox}[colback=white, colframe=gray]
\begin{center}
\Large\textbf{Final Statistics}
\vspace{1em}

\begin{tabular}{lr}
\toprule
\textbf{Category} & \textbf{Quantity} \\
\midrule
Font Analizzati (Post-Filtro) & """
# --------------------------------------------
LATEX_END_CODE_2: str = r""" \\
\textcolor{successcolor}{\textbf{Working Fonts}} & \textbf{\arabic{cntWorking}} \\
\textcolor{errorcolor}{\textbf{Broken Fonts}} & \textbf{\arabic{cntBroken}} \\
\textcolor{othercolor}{\textbf{Excluded Fonts}} & \textbf{\arabic{cntExcluded}} \\
\bottomrule
\end{tabular}
\end{center}
\end{tcolorbox}

\FileSec{\jobname.working}{Table of Working Fonts}

\FileSec{\jobname.broken}{Table of Broken Fonts}

\FileSec{\jobname.excluded}{Table of Excluded Fonts}

\end{document}
"""

# --------------------------------------------
# General helper functions
# --------------------------------------------


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


def nfss_family_id(font: dict) -> str:
    """
    Return a deterministic NFSS-safe identifier for a font.

    The identifier is derived from a stable SHA-256 digest of:
        <identity.file>#<ttc_index>

    Parameters
    ----------
    font : dict
        Font descriptor dictionary containing at least an `identity`
        mapping with optional `file` and `ttc_index` fields.

    Returns
    -------
    str
        Deterministic identifier prefixed with "FS" and truncated to
        10 hexadecimal characters.
    """
    identity = font.get("identity", {}) or {}
    file_path = identity.get("file", "")
    ttc_index = identity.get("ttc_index", 0)

    key = f"{file_path}#{ttc_index}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return "FS" + digest[:10]


def group_fonts_by_family(
    fonts: list[CatalogFontEntryV12],
) -> list[CatalogFontEntryV12]:
    """
    Reduce a list of font entries to one entry per family.

    Parameters
    ----------
    fonts : list[dict]
        List of font descriptor dictionaries.

    Returns
    -------
    list[dict]
        List containing a single representative font for each family.
        The first encountered font per family is preserved, and the
        order of first occurrence is maintained.
    """
    families: OrderedDict[str, Any] = OrderedDict()
    for font in fonts:
        fam = font_family(font)
        families.setdefault(fam, []).append(font)
    result = [entries[0] for entries in families.values()]

    log_trace_cat(
        log,
        "flow",
        "fonts grouped by family",
        extra={
            "families": len(result),
            "input_fonts": len(fonts),
        },
    )

    return result


# ============================================================
# Inventory loading (pipeline mode)
# ============================================================


def load_font_inventory(path: Path) -> list[dict]:
    """
    Load and validate a Fontshow inventory file.

    Parameters
    ----------
    path : pathlib.Path
        Path to the inventory JSON file.

    Returns
    -------
    list[dict]
        List of normalized font descriptor dictionaries.

    Raises
    ------
    RuntimeError
        If validation fails or the inventory is incompatible.

    Notes
    -----
    Delegates strict validation to `_load_inventory()` while preserving
    the exception-based contract expected by library callers.
    """
    rc, fonts = _load_inventory(path, require_platform=False)

    if rc != 0:
        msg = "Invalid or incompatible inventory"
        raise RuntimeError(msg)

    return fonts


def as_font_desc_list(fonts: Sequence[object]) -> list[CatalogFontEntryV12]:
    """
    Normalize a sequence of font descriptor objects.

    Parameters
    ----------
    fonts : collections.abc.Sequence[object]
        Sequence expected to contain font descriptor dictionaries.

    Returns
    -------
    list[CatalogFontEntryV12]
        List of validated font descriptor dictionaries.

    Raises
    ------
    TypeError
        If any element in `fonts` is not a dictionary.

    Notes
    -----
    Legacy coercion of non-dictionary entries is not supported.
    """
    out: list[CatalogFontEntryV12] = []
    for f in fonts:
        if not isinstance(f, dict):
            msg = f"Unexpected font entry type {type(f)} for font '{f}'"
            raise TypeError(msg)
        out.append(cast("CatalogFontEntryV12", f))
    return out


def _normalize_inventory_paths(inventory: dict) -> None:
    """
    Normalize inventory font entries so that `identity.file` is present when
    a file path is available.

    Parameters
    ----------
    inventory : dict
        Inventory dictionary expected to contain a `fonts` list with font
        descriptor mappings.

    Returns
    -------
    None

    Notes
    -----
    - Does not modify the schema version.
    - Does not delete fields.
    - Does not emit warnings.
    - Operation is idempotent.
    """

    fonts = inventory.get("fonts", [])
    for font in fonts:
        identity = font.get("identity")

        if not isinstance(identity, dict):
            continue

        if "file" in identity:
            continue

        if "path" in font:
            identity["file"] = font["path"]


def font_family(font: CatalogFontEntryV12 | dict[str, object]) -> str:
    """
    Return a best-effort font family name for rendering and sorting.

    Parameters
    ----------
    font : dict[str, object]
        Schema 1.2 font descriptor dictionary.

    Returns
    -------
    str
        Resolved family name if available, otherwise "Unknown Font".
    """
    fam = font.get("family") or font.get("postscript_name") or font.get("full_name")

    return fam if isinstance(fam, str) and fam else "Unknown Font"


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
    lang = inferred_languages[0] if inferred_languages else None
    if lang and lang in SAMPLE_TEXTS:
        sample = SAMPLE_TEXTS.get(lang)
        if isinstance(sample, str):
            return sample
        return None

    return None


def font_type_label(font: dict) -> str:
    """
    Classify font type for labeling purposes.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary containing an optional `classification`
        section.

    Returns
    -------
    str
        One of:
        - "EMOJI" if the font is classified as emoji
        - "DECORATIVE" if classified as decorative
        - "TEXT" otherwise
    """
    cls = font.get("classification", {}) or {}
    if cls.get("is_emoji"):
        return "EMOJI"
    if cls.get("is_decorative"):
        return "DECORATIVE"
    return "TEXT"


def primary_script(font: dict) -> str | None:
    """
    Determine the primary script associated with a font.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary possibly containing `inference`
        and `coverage` sections with script lists.

    Returns
    -------
    str | None
        First inferred script if available; otherwise the first declared
        coverage script; otherwise None.
    """
    inf = font.get("inference", {}) or {}
    scripts = inf.get("scripts", []) or []
    if scripts:
        return str(scripts[0])
    cov_scripts = font.get("coverage", {}).get("scripts", []) or []
    return str(cov_scripts[0]) if cov_scripts else None


def script_label(font: dict, max_scripts: int = 2) -> str:
    """
    Build a short uppercase label summarizing font scripts.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary possibly containing `inference`
        and `coverage` sections with script lists.
    max_scripts : int, optional
        Maximum number of scripts to include in the label (default is 2).

    Returns
    -------
    str
        Uppercase comma-separated script label, or "UNKNOWN" if no script
        information is available.
    """
    inf = font.get("inference", {}) or {}
    scripts = inf.get("scripts", []) or []
    if not scripts:
        scripts = font.get("coverage", {}).get("scripts", []) or []
    if not scripts:
        return "UNKNOWN"
    return ", ".join(str(s).upper() for s in scripts[:max_scripts])


def language_label(font: dict) -> str:
    """
    Build an uppercase language label for a font.

    Parameters
    ----------
    font : dict
        Font descriptor dictionary used to determine a representative
        language via `choose_sample_language()`.

    Returns
    -------
    str
        Uppercase language code if available, otherwise "N/A".
    """
    lang = choose_sample_language(font)
    return lang.upper() if lang else "N/A"


def render_badges(font: dict[str, object]) -> str:
    """
    Render informational badges for a font.

    Parameters
    ----------
    font : dict[str, object]
        Font descriptor dictionary used to extract script, language,
        and type information.

    Returns
    -------
    str
        LaTeX-formatted string containing ASCII-only badges rendered in
        monospace. May be an empty string if no badge data is available.

    Notes
    -----
    Badges are ASCII-only and typeset in monospace to avoid bidi and
    script-direction issues.
    """
    scripts = script_label(font)
    languages = language_label(font)
    ftype = font_type_label(font)

    parts: list[str] = []
    if scripts:
        parts.append(f"SCRIPTS: {scripts}")
    if languages:
        parts.append(f"LANG: {languages}")
    if ftype:
        parts.append(f"TYPE: {ftype}")

    if not parts:
        return ""

    badge_text = " | ".join(parts)

    return r"{\footnotesize\ttfamily " + badge_text + r"}" "\n"


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
    """
    cls = font.get("classification", {}) or {}
    fam = font_family(font)
    if cls.get("is_emoji"):
        return "😀 😃 😄 😁 😆 😅 😂 🤣 😊 😇"
    if cls.get("is_decorative"):
        return fam
    return choose_sample_text(cast("FontRef", font))


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

    # RTL: unchanged (TestNonLatin already isolates fonts)
    if ps in RTL_SCRIPTS:
        lang, opts = SCRIPT_TO_POLYGLOSSIA.get(ps, ("arabic", "Script=Arabic"))
        if not txt:
            txt = SAMPLE_TEXTS.get("ar" if ps == "arab" else "he", "")
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


# --- System Functions ---


def clean_font_name(name: str) -> str:
    """
    Normalize a raw font name to a base family-like name.

    Parameters
    ----------
    name : str
        Raw font name as obtained from system sources.

    Returns
    -------
    str
        Normalized base name with parenthetical hints removed and
        common variant suffixes (e.g., Bold, Italic) stripped.
    """
    clean_name = re.sub(r"\s*\((TrueType|OpenType|True Type|Type 1)\)\s*$", "", name)

    variants = r"\s+(Bold|Italic|Light|Regular|Medium|Semibold|Black|Thin|Heavy|Narrow|Condensed|Extended|Grassetto|Corsivo|Chiaro|Normale|Medio|Nero|Sottile|Pesante|Condensato|Esteso).*$"
    return re.sub(variants, "", clean_name, flags=re.IGNORECASE).strip()


class _FontDetail(TypedDict):
    raw_line: str
    extracted_names: list[str]
    base_names: list[str]


def generate_test_output(
    inventory_fonts: list[dict],
    limit: int | None = None,
    filter_test: bool = False,
) -> None:
    """
    Produce a small text file with parsing diagnostics for manual inspection.

    Parameters
    ----------
    limit : int | None, optional
        If positive, keep the first N items; if negative, keep the last |N|
        items; if None, no limit is applied.
    filter_test : bool, optional
        If True, include only fonts whose names match substrings listed
        in `TEST_FONTS`.

    Returns
    -------
    None
    """
    details: list[_FontDetail] = []

    families = {
        str(font_item.get("family", "")).strip()
        for font_item in inventory_fonts
        if font_item.get("family")
    }

    for family in sorted(families):
        details.append(
            {
                "raw_line": family,
                "extracted_names": [family],
                "base_names": [family],
            }
        )

    if filter_test:
        details = [
            item
            for item in details
            if any(name in TEST_FONTS for name in item["base_names"])
        ]

    if limit:
        details = details[:limit] if limit > 0 else details[limit:]

    # Sort alphabetically for the first base name
    details.sort(key=lambda x: x["base_names"][0].lower() if x["base_names"] else "")

    base_name = f"TODF_{platform.system()}_{DATE_STR}"
    try:
        test_filename = get_unique_filename(base_name, "txt")
    except ValueError as e:
        log_err(f"Error generating test file: {e}")
        return
    with Path(test_filename).open("w", encoding="utf-8") as f:
        for item in details:
            family = item["base_names"][0]

            f.write(f"Raw line: {family}\n")
            f.write(f"Extracted names: {family}\n")
            f.write(f"Base names: {family}\n")

            # List all files belonging to this family
            paths = sorted(
                str(font_item.get("path", "")).strip()
                for font_item in inventory_fonts
                if isinstance(font_item, dict)
                and str(font_item.get("family", "")).strip() == family
                and font_item.get("path")
            )

            if paths:
                f.write("Files:\n")
                for p in paths:
                    f.write(f"  - {p}\n")
            else:
                f.write("Files: (none)\n")

            f.write("\n")

    log_ok(f"Test file generated: {test_filename}")


def _normalize_path_for_latex(fullpath: str) -> tuple[str, str]:
    """
    Normalize a font file path for LaTeX/fontspec usage.

    Returns
    -------
    tuple[str, str]
        (dir_with_trailing_slash, filename)

    Notes
    -----
    - Uses forward slashes regardless of platform.
    - Guarantees a non-empty directory (defaults to "./").
    """
    norm = fullpath.replace("\\", "/")
    if "/" in norm:
        d, f = norm.rsplit("/", 1)
        d = (d + "/") if d else "./"
        return d, f
    return "./", norm


def generate_latex(font_list: list[CatalogFontEntryV12]) -> str:
    """
    Generate the full LaTeX document for the provided font descriptors.

    Parameters
    ----------
    font_list : list[dict]
        List of normalized font descriptor dictionaries as produced by
        `parse_font_inventory`.

    Returns
    -------
    str
        Complete LaTeX document as a string.
    """
    font_list = as_font_desc_list(font_list)

    # --- DEDUPLICATION BY FAMILY ---
    seen_families: set[str] = set()
    unique_fonts: list[CatalogFontEntryV12] = []
    for font in font_list:
        fam = font_family(font)
        if fam not in seen_families:
            seen_families.add(fam)
            unique_fonts.append(font)

    font_list = unique_fonts

    log_info(f"Generating LaTeX file for {len(font_list)} fonts...")

    latex_code: str = LATEX_INITIAL_CODE

    total = len(font_list)
    latex_code += "\\section{Font List (Stage 0)}\n"
    latex_code += "\\begin{itemize}\n"

    typed_font_list: list[CatalogFontEntryV12] = font_list
    for idx, font in enumerate(typed_font_list, start=1):
        fam = font_family(font)
        safe_name = escape_latex(fam)

        if idx % 500 == 0 or idx == total:
            log_info(f"  ... processed {idx}/{total}")

        specimen = str(font.get("specimen_text", ""))
        safe_specimen = escape_latex(specimen)
        inference_raw = font.get("inference") or {}
        inference = inference_raw if isinstance(inference_raw, dict) else {}

        coverage_raw = font.get("coverage") or {}
        coverage = coverage_raw if isinstance(coverage_raw, dict) else {}
        scripts_raw_obj = inference.get("scripts")
        scripts_raw: list[str] = (
            scripts_raw_obj if isinstance(scripts_raw_obj, list) else []
        )
        script0 = str(scripts_raw[0]) if scripts_raw else ""

        cov_scripts_obj = coverage.get("scripts")
        cov_scripts: list[str] = (
            cov_scripts_obj if isinstance(cov_scripts_obj, list) else []
        )

        path = str(font.get("path", "")).lower()
        fullpath = str(font.get("path", ""))
        fullpath_norm = fullpath.replace("\\", "/")
        detok_fullpath = "\\detokenize{" + fullpath_norm + "}"

        is_opentype = path.endswith((".ttf", ".otf", ".ttc"))

        render = ""
        if (
            script0 == "LATN"
            and isinstance(cov_scripts, list)
            and ("LATN" in cov_scripts)
            and is_opentype
        ):
            _dir, _file = _normalize_path_for_latex(fullpath)
            detok_dir = "\\detokenize{" + _dir + "}"
            detok_file = "\\detokenize{" + _file + "}"
            renderer_prefix = _renderer_option_prefix()
            render = (
                " {\\begingroup\\fontspec["
                + renderer_prefix
                + "Path="
                + detok_dir
                + "]{"
                + detok_file
                + "}"
                + safe_specimen
                + "\\endgroup}"
            )

        latex_code += (
            "\\item "
            + safe_name
            + " --- "
            + "\\IfFileExists{"
            + detok_fullpath
            + "}{[OK]\\newline"
            + render
            + "}{[MISSING]}"
            + "\n"
        )

    latex_code += "\\end{itemize}\n"

    latex_code += "\n\n"
    for excluded_font in sorted(list(EXCLUDED_FONTS)):
        excluded_block: str = r"\LogExcluded{" + excluded_font + "}\n"
        latex_code += excluded_block

    # Closing document and printing indices
    latex_code += LATEX_END_CODE_1 + str(total) + LATEX_END_CODE_2
    return latex_code


# ============================================================
# Platform integration and CLI orchestration
# ============================================================
#
# This section contains:
# - platform-specific helpers (Linux / Windows),
# - deterministic inventory-only operation,
# - LaTeX escaping utilities,
# - the CLI entry point (main).
#
# Design notes:
# - Platform detection is best-effort and defensive.
# - Failures in discovery or rendering provoke rejection of the specific
#   font but do not abort the whole process,
# - The CLI is intentionally thin: orchestration only, no business logic.
#
def build_parser(parser: argparse.ArgumentParser) -> None:
    """
    Register create-catalog CLI arguments on an existing parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Argument parser to be configured with create-catalog options.

    Returns
    -------
    None
    """
    parser.description = "Generate system font catalog in LaTeX"
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Generate auxiliary text file with parsing details",
    )
    parser.add_argument(
        "-T",
        "--test-font",
        nargs="?",
        const="__DEFAULT__",
        action="append",
        metavar="FONT_NAME",
        help=(
            "Restrict processing to a test font subset. "
            "If used without argument, enables the default test font set. "
            "If used with a font name, adds it to the test font set. "
            "Can be repeated multiple times."
        ),
    )
    parser.add_argument(
        "-l",
        "--list-test-fonts",
        action="store_true",
        help=(
            "List the effective test font set and the installed fonts matching it, then exit "
            "without generating the LaTeX catalog."
        ),
    )
    parser.add_argument(
        "-i",
        "--inventory",
        type=str,
        default=DEFAULT_INVENTORY,
        help="Path to font inventory JSON file to be used.",
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        help="Limit the number of processed fonts to the first N (if positive) or the last |N| (if negative)",
    )
    add_common_arguments(
        parser,
        include_output=True,
        output_default=None,
        output_help="Output LaTeX .tex file (optional; default is an auto-generated unique name)",
    )


def register_cli(parser) -> None:
    """
    Register create-catalog CLI arguments.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Argument parser to be configured for the create-catalog command.

    Returns
    -------
    None

    Notes
    -----
    Used by the top-level Fontshow dispatcher.
    """
    build_parser(parser)
    parser.set_defaults(func=main)


# ------------------------------------------------------------------
# TEST FONT CONFIGURATION
# ------------------------------------------------------------------


def _configure_test_fonts(args) -> set[str]:
    """
    Build the effective TEST_FONTS set from CLI arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments containing the `test_font` option.

    Returns
    -------
    set[str]
        Final set of font names to be used for test filtering.

    Notes
    -----
    Semantics:
    - "__DEFAULT__" enables DEFAULT_TEST_FONTS.
    - Explicit values extend the set.
    """
    cli_fonts: set[str] = set()

    if args.test_font:
        for value in args.test_font:
            cli_fonts.add(value)

        # Explicit CLI fonts extend defaults.
        return set(DEFAULT_TEST_FONTS) | cli_fonts

    # No --test-font provided → use DEFAULT_TEST_FONTS.
    return set(DEFAULT_TEST_FONTS)


def _handle_list_test_fonts(test_fonts: set[str], inventory_fonts: list[dict]) -> int:
    """
    Implement the --list-test-fonts CLI behavior.

    Parameters
    ----------
    test_fonts : set[str]
        Effective set of test font names used for filtering.

    Returns
    -------
    int
        Exit code (0 on success).

    Notes
    -----
    - Must ignore --quiet by contract.
    - Lists configured TEST_FONTS and matching inventory fonts (JSON is the single source of truth).
    """
    log_info("TEST_FONTS configuration:")

    if not test_fonts:
        log_info("  (empty)")
    else:
        for name in sorted(test_fonts):
            log_info(f"  - {name}")

    log_info("Inventory fonts matching TEST_FONTS (exact):")

    inv_families = {
        str(f.get("family", "")).strip() for f in inventory_fonts if isinstance(f, dict)
    }
    matched = [name for name in sorted(test_fonts) if name in inv_families]

    if not matched:
        log_info("  (none)")
    else:
        for name in matched:
            log_info(f"  - {name}")

    log_info("Missing TEST_FONTS (not present in inventory):")
    missing = [name for name in sorted(test_fonts) if name not in inv_families]

    if not missing:
        log_info("  (none)")
    else:
        for name in missing:
            log_info(f"  - {name}")

    return 0


# ------------------------------------------------------------------
# OUTPUT FILE PREPARATION
# ------------------------------------------------------------------


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


# ------------------------------------------------------------------
# INVENTORY / FONT SOURCE
# ------------------------------------------------------------------


def _resolve_inventory_path(args) -> Path | None:
    """
    Resolve the inventory file path according to CLI semantics.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments containing the `inventory` option.

    Returns
    -------
    pathlib.Path | None
        Resolved inventory path if found, otherwise None.

    Notes
    -----
    Resolution priority:
    1. Explicit --inventory path.
    2. DEFAULT_INVENTORY if it exists.
    3. None if no valid inventory can be resolved.
    """
    if args.inventory:
        return Path(args.inventory)

    default = Path(DEFAULT_INVENTORY)
    if default.exists():
        return default

    return None


def _inventory_platform_mismatch(inv_env: dict, runtime: dict) -> list[str]:
    """
    Compare inventory and runtime platform metadata and report mismatches.

    Parameters
    ----------
    inv_env : dict
        Inventory run-environment metadata.
    runtime : dict
        Runtime platform metadata collected from the current system.

    Returns
    -------
    list[str]
        List of metadata keys that differ between inventory and runtime.
        Empty if no mismatch is detected.
    """

    def _norm(v: object) -> str:
        """
        Normalize a value for platform metadata comparison.

        Parameters
        ----------
        v : object
            Value to normalize.

        Returns
        -------
        str
            Lowercased and stripped string representation of the value.
        """
        return str(v).strip().lower()

    mismatches: list[str] = []

    for key in ("os", "machine"):
        if _norm(inv_env.get(key)) != _norm(runtime.get(key)):
            mismatches.append(key)

    inv_ctx = inv_env.get("execution_context")
    run_ctx = runtime.get("execution_context")

    if _norm(inv_ctx) != _norm(run_ctx):
        mismatches.append("execution_context")

    return mismatches


def _enforce_platform(inv_env: dict) -> tuple[bool, list[str]]:
    """
    Enforce inventory/platform compatibility.

    Parameters
    ----------
    inv_env : dict
        Inventory run-environment metadata.

    Returns
    -------
    tuple[bool, list[str]]
        A pair (ok, mismatches):
        - ok is True if inventory matches runtime platform.
        - mismatches contains the differing metadata keys.
    """
    runtime = collect_platform_metadata()
    mismatches = _inventory_platform_mismatch(inv_env, runtime)
    return (not mismatches), mismatches


def _validate_fonts_structure(inventory: dict) -> tuple[bool, list]:
    """
    Validate the structure of the `fonts` section in an inventory.

    Parameters
    ----------
    inventory : dict
        Inventory dictionary expected to contain a `fonts` list.

    Returns
    -------
    tuple[bool, list]
        A pair (ok, fonts):
        - ok is True if the `fonts` section exists, is a non-empty list,
          and all elements are dictionaries.
        - fonts is the extracted list (or an empty list on failure).
    """
    if "fonts" not in inventory:
        return False, []

    fonts = inventory.get("fonts")
    if not isinstance(fonts, list):
        return False, []

    if not fonts:
        return False, []

    if any(not isinstance(f, dict) for f in fonts):
        return False, []

    return True, fonts


def _load_inventory(
    inv_path: Path, *, require_platform: bool = True
) -> tuple[int, list]:
    """
    Load and strictly validate an inventory file.

    Parameters
    ----------
    inv_path : pathlib.Path
        Path to the inventory JSON file.
    require_platform : bool, optional
        If True, enforce platform compatibility between inventory metadata
        and the current runtime environment.

    Returns
    -------
    tuple[int, list]
        A pair (exit_code, fonts):
        - exit_code == 0 → success, fonts contains validated descriptors.
        - exit_code == 1 → validation or load error (already logged), fonts empty.

    Notes
    -----
    Validation rejects:
    - Invalid schema version.
    - Missing required metadata.
    - Platform-incompatible inventories (when require_platform is True).
    - Malformed or empty `fonts` section.
    - Semantic validation failures.

    Validation is always strict; non-strict operation is not supported.
    """
    try:
        with inv_path.open(encoding="utf-8") as f:
            inventory = json.load(f)

        if not isinstance(inventory, dict):
            log_err("Invalid inventory JSON: expected top-level object.")
            return 1, []

        metadata = inventory.get("metadata", {}) or {}
        if not isinstance(metadata, dict):
            log_err("Invalid inventory JSON: expected 'metadata' to be an object.")
            return 1, []

        schema_version = metadata.get("schema_version")
        if schema_version != SCHEMA_VERSION:
            log_err(
                f"Unsupported inventory schema_version: {schema_version!r} "
                f"(required {SCHEMA_VERSION})"
            )
            return 1, []

        inv_env = metadata.get("run_environment")
        if require_platform and not isinstance(inv_env, dict):
            log_err("Inventory missing required metadata.run_environment (schema v1.2)")
            return 1, []

        if require_platform and isinstance(inv_env, dict):
            ok, mismatches = _enforce_platform(inv_env)
            if not ok:
                log_err(f"Inventory platform mismatch: {', '.join(mismatches)}")
                return 1, []

        log_trace_cat(
            log,
            "flow",
            "inventory JSON loaded",
            extra={
                "fonts_count": len(inventory.get("fonts", [])),
                "path": str(inv_path),
            },
        )

        normalize_loaded_enums(inventory)

        ok_fonts, fonts = _validate_fonts_structure(inventory)
        if not ok_fonts:
            log_err("Invalid inventory JSON: malformed or empty 'fonts' section.")
            return 1, []

        _normalize_inventory_paths(inventory)

        ok, semantic_warnings = enforce_semantic_validation(
            inventory,
            strict=True,
        )
        log_trace_cat(
            log,
            "flow",
            "semantic validation completed",
            extra={
                "ok": ok,
                "warnings": len(semantic_warnings),
            },
        )

        if not ok:
            for w in semantic_warnings:
                sev = w.get("severity", Severity.INFO)
                if sev in (Severity.ERROR, Severity.WARN):
                    log_err(w.get("message", "semantic validation error"))
            return 1, []

        log_ok(f"Inventory loaded: {inv_path} ({len(fonts)} fonts)")

    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
        log_err(f"failed to load inventory: {e}")
        return 1, []
    else:
        return 0, fonts


# ------------------------------------------------------------------
# DIAGNOSTICS
# ------------------------------------------------------------------


def _run_inventory_diagnostics(fonts: list) -> None:
    """
    Run consistency diagnostics for inventory-based execution.

    Parameters
    ----------
    fonts : list
        List of validated font descriptor dictionaries.

    Returns
    -------
    None

    Notes
    -----
    Applies only when inventory mode is active and CLI is not in quiet mode.
    Emits informational or warning messages if language coverage is missing
    for a significant fraction of fonts.
    """
    missing_lang_count = 0
    total_fonts = 0

    for font in fonts:
        if not isinstance(font, dict):
            continue

        total_fonts += 1
        declared = set(font.get("coverage", {}).get("languages", []))

        if not declared:
            missing_lang_count += 1

    if not missing_lang_count:
        return

    ratio = missing_lang_count / total_fonts if total_fonts else 0.0

    if ratio < 0.10:
        log_info(
            f"{missing_lang_count} fonts have no declared language coverage "
            f"({ratio:.0%})"
        )
    elif ratio < 0.50:
        log_warn(
            f"{missing_lang_count} fonts have no declared language coverage "
            f"({ratio:.0%})"
        )
    else:
        log_warn(
            f"{missing_lang_count} fonts have no declared language coverage "
            f"({ratio:.0%}) — catalog usefulness may be severely degraded"
        )


# ------------------------------------------------------------------
# FONT FILTERING / OUTPUT GENERATION
# ------------------------------------------------------------------


def _filter_and_prepare_fonts(
    fonts: list[CatalogFontEntryV12], args, test_fonts: set[str]
) -> list[CatalogFontEntryV12]:
    """
    Filter and prepare fonts for catalog generation.

    Parameters
    ----------
    fonts : list
        List of font descriptor objects.
    args : argparse.Namespace
        Parsed CLI arguments controlling filtering and limiting.
    test_fonts : set[str]
        Set of font name substrings used for test filtering.

    Returns
    -------
    list
        List of filtered, sorted, and deduplicated font descriptor dictionaries.
    """
    log_trace_cat(
        log,
        "flow",
        "font filtering started",
        extra={
            "input_fonts": len(fonts),
        },
    )

    if test_fonts:
        fonts = [f for f in as_font_desc_list(fonts) if font_family(f) in test_fonts]

    if args.number:
        fonts = fonts[: args.number] if args.number > 0 else fonts[args.number :]

    fonts = sorted(
        as_font_desc_list(fonts),
        key=lambda f: font_family(f),
    )

    # Schema v1.2 forbids adding non-schema keys (e.g. 'name').
    # Rendering code must derive display name dynamically instead of mutating the descriptor.
    for f in fonts:
        _ = (
            f.get("full_name")
            or f.get("postscript_name")
            or f"{(f.get('family') or '')} {(f.get('subfamily') or '')}".strip()
        )
    result = group_fonts_by_family(fonts)
    log_trace_cat(
        log,
        "flow",
        "font filtering completed",
        extra={
            "output_fonts": len(result),
        },
    )

    return result


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
    """
    log_info(f"Writing file {output_filename}...")

    with Path(output_filename).open("w", encoding="utf-8") as f:
        f.write(latex_content)

    log_ok("Done! LaTeX file generated successfully.")
    log_ok("Ready for compilation.")
    log_ok(
        f"  Execute: lualatex -interaction=nonstopmode {output_filename} | texlogsieve (twice)"
    )


def run_create_catalog(args) -> int:
    """
    Execute the create-catalog workflow.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments controlling catalog generation.

    Returns
    -------
    int
        Process exit code:
        - 0 on success
        - non-zero on failure

    Notes
    -----
    Workflow:
    - Configure TEST_FONTS.
    - Handle --list-test-fonts early exit.
    - Prepare output filename.
    - Resolve inventory source.
    - Run diagnostics (inventory mode only).
    - Filter and prepare fonts.
    - Generate and write LaTeX output.

    Behavior is identical to the pre-refactor implementation.
    """
    global TEST_FONTS

    # --------------------------------------------------------------
    # TEST FONT CONFIGURATION
    # --------------------------------------------------------------
    TEST_FONTS = _configure_test_fonts(args)

    # --------------------------------------------------------------
    # OUTPUT FILE PREPARATION
    # --------------------------------------------------------------
    output_arg = getattr(args, "output", None)
    if output_arg is not None:
        output_filename = str(output_arg)
    else:
        rc, out_name = _prepare_output_filename()
        if rc != 0 or out_name is None:
            return 1
        output_filename = out_name

    # --------------------------------------------------------------
    # INVENTORY / FONT SOURCE
    # --------------------------------------------------------------
    inv_path = _resolve_inventory_path(args)

    if not inv_path or not inv_path.exists():
        log_err(
            "Font inventory not found. Catalog generation requires a valid v1.2 inventory."
        )
        return 1  # MUST fail deterministically even in --quiet mode

    rc, fonts = _load_inventory(inv_path)
    if rc != 0:
        return 1

    if args.test:
        generate_test_output(fonts, args.number, bool(TEST_FONTS))

    if args.list_test_fonts:
        return _handle_list_test_fonts(TEST_FONTS, fonts)

    # --------------------------------------------------------------
    # CONSISTENCY DIAGNOSTICS (inventory mode only)
    # --------------------------------------------------------------
    if inv_path and inv_path.exists():
        _run_inventory_diagnostics(fonts)

    # --------------------------------------------------------------
    # FONT FILTERING / OUTPUT PREPARATION
    # --------------------------------------------------------------
    fonts = _filter_and_prepare_fonts(fonts, args, TEST_FONTS)

    # Invariant guard: rendering requires normalized font descriptors.
    if not isinstance(fonts, list) or any(not isinstance(f, dict) for f in fonts):
        log_err("Internal error: invalid font descriptor list after filtering.")
        return 1

    latex_content = generate_latex(fonts)

    # --------------------------------------------------------------
    # WRITE OUTPUT
    # --------------------------------------------------------------
    try:
        _write_latex_output(output_filename, latex_content)
    except OSError as exc:
        log_err(f"Failed to write output file: {exc}")
        return 1

    log_trace_cat(
        log,
        "io",
        "catalog tex written",
        extra={
            "path": str(output_filename),
        },
    )
    log_trace_cat(
        log,
        "flow",
        "create-catalog completed",
        extra={
            "fonts_used": len(fonts),
            "output": str(output_filename),
        },
    )

    return 0


def _run_create_catalog(args) -> int:
    """
    Indirection layer for CLI testing.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments forwarded to the core implementation.

    Returns
    -------
    int
        Exit code returned by `run_create_catalog`.

    Notes
    -----
    Exists so CLI tests can monkeypatch this function without
    modifying the core implementation.
    """
    return run_create_catalog(args)


def run(args):
    """
    Public CLI entrypoint for create-catalog.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Exit code returned by `main`.

    Notes
    -----
    Thin wrapper around `main` kept stable for compatibility with
    the top-level dispatcher and tests.
    """
    return main(args)


def main(args) -> int:
    """
    CLI entrypoint for create-catalog.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments controlling catalog execution.

    Returns
    -------
    int
        Process exit code returned by the catalog workflow.

    Notes
    -----
    Handles user-facing output and delegates execution to the core
    implementation. Unexpected exceptions are converted to exit code 2.
    """
    set_cli_mode(getattr(args, "quiet", False), getattr(args, "verbose", False))

    try:
        exit_code = _run_create_catalog(args)
    except Exception as exc:  # noqa: BLE001
        # (Crash barrier: convert unexpected failure → exit code 2)
        log_err(f"create-catalog failed: {exc}")
        log_trace_cat(
            log,
            "perf",
            "catalog metrics",
            extra={
                "exit_code": 2,
                "exception": True,
            },
        )
        return 2

    if exit_code == 0:
        log_ok("Done", verbose="catalog created successfully")
    else:
        # Do not mask failure - CLI nust propagate real exit code even in --quiet mode
        log_err(f"create-catalog failed with exit code {exit_code}")

    log_trace_cat(
        log,
        "perf",
        "catalog metrics",
        extra={
            "exit_code": exit_code,
        },
    )

    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="create-catalog")
    build_parser(parser)
    args = parser.parse_args()
    sys.exit(main(args))
