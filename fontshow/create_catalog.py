"""
Fontshow – create_catalog.py
==========================

LaTeX catalog generator for Fontshow.

This module consumes the canonical font inventory JSON produced by
``dump_fonts.py`` and generates a printable LaTeX catalog.

Design principles
-----------------
- **Pure rendering stage**: this module never inspects font binaries.
- **Inventory-driven**: all semantic information comes from the JSON inventory.
- **Conservative defaults**: missing or partial metadata is handled gracefully.
- **LaTeX-first**: output is optimized for XeLaTeX/LuaLaTeX workflows.

This file intentionally mixes:
- inventory glue logic,
- rendering helpers,
- platform-specific fallbacks,
- CLI orchestration.

The architecture is procedural by design and mirrors the historical evolution
of the project.

Pipeline for creating a LuaLaTeX font catalog from a Fontshow inventory.

This module contains utilities for loading the JSON inventory, inferring
rendering choices and producing the final LaTeX source used by the main
`create_catalog` workflow. Key entrypoints:
- `generate_latex(font_list)` — produce full LaTeX document
- `get_installed_fonts()` — fallback discovery for legacy mode

Keep changes minimal: the LaTeX templates in the module are whitespace-
sensitive and used directly by the renderer.
"""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

# Platform-specific imports (deferred)
if sys.platform == "win32":
    import winreg
else:
    winreg = None

if sys.platform == "win32":
    # modulo specifico Windows
    IS_WINDOWS = True
    IS_LINUX = False
    WINDOWS_MODULE = winreg
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


SCRIPT_BADGE_MAP = {
    "latin": "LAT",
    "greek": "GRK",
    "cyrillic": "CYR",
    "arabic": "ARB",
    "hebrew": "HEB",
    "devanagari": "DEV",
    "han": "HAN",
    "japanese": "JPN",
    "korean": "KOR",
    "emoji": "EMOJI",
}


def script_badges(font: dict) -> list[str]:
    scripts = font.get("inference", {}).get("scripts", [])
    return [SCRIPT_BADGE_MAP[s] for s in scripts if s in SCRIPT_BADGE_MAP]


def get_unique_filename(base_name, extension):
    """Genera un nome file unico aggiungendo un contatore a tre cifre (000-999)."""
    for i in range(1000):
        suffix = f"_{i:03d}"
        filename = f"{base_name}{suffix}.{extension}"
        if not os.path.exists(filename):
            return filename
    raise ValueError(
        f"Impossibile trovare un nome file unico per {base_name}.{extension} dopo 1000 tentativi."
    )


def nfss_family_id(font: dict) -> str:
    """Return a short NFSS-safe identifier for a font (used as temporary family).

    This produces a stable short id prefixed with 'FS' used in `fontspec`
    calls when a normalized family name is required.
    """
    return "FS" + str(abs(hash(font.get("identity", {}).get("file", ""))) % 10**8)


def fontspec_options(font: dict) -> str:
    """
    Build fontspec options string.

    Uses TTC index if present, e.g.:
      Index=3
    """
    ttc_index = font.get("identity", {}).get("ttc_index")
    if ttc_index is not None:
        return f"Index={ttc_index}"
    return ""


def group_fonts_by_family(fonts: list[dict]) -> list[dict]:
    """Reduce a list of font entries to one entry per family.

    Keeps the first encountered font for each family (usually Regular or
    `ttc_index` 0). Preserves order of first occurrence.
    """
    families = OrderedDict()
    for font in fonts:
        fam = font_family(font)
        families.setdefault(fam, []).append(font)
    return [entries[0] for entries in families.values()]


# --- Configurazione ---
# OUTPUT_FILENAME now includes the platform name and current date (YYYYMMDD)
DATE_STR = datetime.now().strftime("%Y%m%d")

# Font per test fisso
TEST_FONTS = {"arial", "times", "courier", "helvetica", "dejavu"}

# --- Definizione dei blocchi statici (o quasi) di coodice LATTEX ---
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
LATEX_INITIAL_CODE = (
    r"""% !TeX TS-program = lualatex
% !TeX spellcheck = it_IT
% !TeX encoding = UTF-8
\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\usepackage{polyglossia} % Gestione multilingue avanzata
\usepackage{lipsum}
\usepackage{xcolor}
\usepackage{tcolorbox}
\usepackage{geometry}
\usepackage{fancyhdr}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{multicol}

\setmainlanguage{italian}
% Definisci le lingue secondarie necessarie per il test dei font complessi
\setotherlanguage{latin}
\setotherlanguage{arabic}
\setotherlanguage{hebrew}
\setotherlanguage{japanese}
\setotherlanguage{chinese}  % Aggiunto Cinese
\setotherlanguage{hindi}    % Aggiunto Hindi
\setotherlanguage{thai}

\geometry{margin=2cm}

% Colori
\definecolor{titlecolor}{HTML}{667eea}
\definecolor{boxcolor}{HTML}{f0f0f0}
\definecolor{successcolor}{HTML}{28a745}
\definecolor{errorcolor}{HTML}{dc3545}
\definecolor{othercolor}{HTML}{0d6efd}

% Setup Box
\tcbuselibrary{skins}
\newtcolorbox{fontbox}[1]{
    colback=boxcolor, colframe=titlecolor, boxrule=1pt, arc=3pt,
    title={\textbf{#1}}, coltitle=white, colbacktitle=titlecolor
}
\newtcolorbox{errorbox}[1]{
    colback=errorcolor!10, colframe=errorcolor!80!black, boxrule=1pt, arc=3pt,
    title={\textbf{Non Caricato: #1}}, coltitle=white, colbacktitle=errorcolor!80!black
}

% --- MACRO PER CARATTERI NON LATINI (FIXED) ---
% #1: Font Name, #2: Language Tag (polyglossia), #3: Font Options (e.g., Script=Arabic), #4: Sample Text
\newcommand{\TestNonLatin}[4]{%
	\par\noindent\textbf{Test in Lingua (\texttt{#2}) con Opzioni: \texttt{[#3]}}

	\foreignlanguage{#2}{%
		\fontspec{#1}[#3]%
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
    \immediate\write\fileWorking{\unexpanded{\item} #1}%
}

\protected\def\LogBroken#1{%
    \stepcounter{cntBroken}%
    \immediate\write\fileBroken{\unexpanded{\item} #1}%
}

\protected\def\LogExcluded#1{%
    \stepcounter{cntExcluded}%
    \immediate\write\fileExcluded{\unexpanded{\item} #1}%
}
% -----------------------------------

\SetLipsumText{cicero}
\newcommand{\Li}{\lipsum[1][1-4]}

\title{\Huge\textbf{\color{titlecolor}Catalogo Font di Sistema}}
\author{Generato da Python in \texttt{"""
    + platform.system()
    + r"""}}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
Questo documento cataloga i font installati.
I font problematici noti sono stati esclusi preventivamente. La compilazione è eseguita con \textbf{LuaLaTeX}.
\end{abstract}

\tableofcontents
\newpage

\section{Catalogo Dettagliato}"""
)
# -------------------------------------------
SAMPLE_1 = r"""\textbf{Test Latino (Lipsum):}
    {\mdseries\upshape\fontspec{"""
# --------------------------------------------
SAMPLE_2 = r"""}
    \Li
    }"""
# --------------------------------------------

# ============================================================
# Inventory loading (pipeline mode)
# ============================================================

DEFAULT_INVENTORY = "font_inventory_enriched.json"


def load_font_inventory(path: Path) -> list[dict]:
    """
    Load a Fontshow inventory JSON file.

    Expected structure:
        { "fonts": [ { ...font descriptor... }, ... ], "metadata": { ... } }

    Returns:
        List of font descriptor dicts.

    Notes:
        - This function does not touch font files.
        - It is safe to call on both Linux and Windows.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    fonts = data.get("fonts", [])
    if not isinstance(fonts, list):
        raise TypeError("Invalid inventory JSON: expected key 'fonts' to be a list.")
    return fonts


def as_font_desc_list(fonts: list) -> list[dict]:
    """
    Normalize input fonts into a list of descriptors.

    If `fonts` is already a list of dicts, it is returned as-is.
    If `fonts` is a list of strings (legacy mode), each item becomes:
        {"identity": {"family": "<name>"}, "classification": {}, "inference": {}}
    """
    out: list[dict] = []
    for f in fonts:
        if isinstance(f, dict):
            out.append(f)
        else:
            out.append(
                {
                    "identity": {"family": str(f)},
                    "classification": {},
                    "inference": {},
                    "coverage": {},
                }
            )
    return out


def font_family(font: dict) -> str:
    """Best-effort family name for LaTeX rendering and sorting."""
    ident = font.get("identity", {}) if isinstance(font, dict) else {}
    return (
        ident.get("family")
        or ident.get("postscript_name")
        or ident.get("fullname")
        or "Unknown Font"
    )


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
}

RTL_SCRIPTS = {"arab", "hebr"}

SCRIPT_TO_POLYGLOSSIA = {
    "arab": ("arabic", "Script=Arabic"),
    "hebr": ("hebrew", "Script=Hebrew"),
}


def choose_sample_language(font: dict) -> str | None:
    inf = font.get("inference", {}) or {}
    langs = inf.get("languages", []) or []
    if langs:
        return str(langs[0])
    cov_langs = font.get("coverage", {}).get("languages", []) or []
    return str(cov_langs[0]) if cov_langs else None


def choose_sample_text(font: dict) -> str | None:
    lang = choose_sample_language(font)
    if lang and lang in SAMPLE_TEXTS:
        return SAMPLE_TEXTS[lang]
    return None


def font_type_label(font: dict) -> str:
    cls = font.get("classification", {}) or {}
    if cls.get("is_emoji"):
        return "EMOJI"
    if cls.get("is_decorative"):
        return "DECORATIVE"
    return "TEXT"


def primary_script(font: dict) -> str | None:
    inf = font.get("inference", {}) or {}
    scripts = inf.get("scripts", []) or []
    if scripts:
        return str(scripts[0])
    cov_scripts = font.get("coverage", {}).get("scripts", []) or []
    return str(cov_scripts[0]) if cov_scripts else None


def script_label(font: dict, max_scripts: int = 2) -> str:
    inf = font.get("inference", {}) or {}
    scripts = inf.get("scripts", []) or []
    if not scripts:
        scripts = font.get("coverage", {}).get("scripts", []) or []
    if not scripts:
        return "UNKNOWN"
    return ", ".join(str(s).upper() for s in scripts[:max_scripts])


def language_label(font: dict) -> str:
    lang = choose_sample_language(font)
    return lang.upper() if lang else "N/A"


def render_badges(font: dict) -> str:
    """
    Render informational badges for a font.

    Badges are ASCII-only and typeset in monospace to avoid bidi
    and script-direction issues. The returned string is valid LaTeX
    and may be empty.
    """
    scripts = script_label(font)
    languages = language_label(font)
    ftype = font_type_label(font)

    parts = []
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
    cls = font.get("classification", {}) or {}
    fam = font_family(font)
    if cls.get("is_emoji"):
        return "😀 😃 😄 😁 😆 😅 😂 🤣 😊 😇"
    if cls.get("is_decorative"):
        return fam
    return choose_sample_text(font)


def render_sample_code(font: dict, fam: str) -> str:
    """
    Build the LaTeX snippet for the sample.

    For sample rendering we MUST be conservative:
    - Never request Bold / Italic / BI shapes.
    - Never propagate weight/width/style inferred metadata.
    - For RTL scripts use TestNonLatin (polyglossia + harfbuzz).
    - For LTR scripts use a minimal, NFSS-safe fontspec call.
    """
    txt = render_sample_text(font)
    ps = primary_script(font)

    nfss_id = "FS" + str(abs(hash(fam)) % 10**8)

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
        return SAMPLE_1 + escape_latex(fam) + SAMPLE_2

    return (
        r"\textbf{Esempio:}"
        "\n"
        r"{\mdseries\upshape\fontspec["
        r"Renderer=Harfbuzz,"
        f"Family={nfss_id},"
        r"UprightFont=*,"
        r"BoldFont={},"
        r"ItalicFont={},"
        r"BoldItalicFont={}"
        r"]{" + escape_latex(fam) + r"}" + escape_latex(txt) + r"}"
    )


NORMAL_BLOCK = """\\subsection{{{safe_name}}}

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
        Il font risulta nel sistema ma LuaLaTeX non riesce a caricarlo.
    \\end{{errorbox}}
}}

\\vspace{{1em}}
"""
# --------------------------------------------
LATEX_END_CODE_1 = r"""\newpage

% Chiusura file degli indici
\immediate\closeout\fileWorking
\immediate\closeout\fileBroken
\immediate\closeout\fileExcluded

\section{Riepilogo e Statistiche}

\begin{tcolorbox}[colback=white, colframe=gray]
\begin{center}
\Large\textbf{Statistiche Finali}
\vspace{1em}

\begin{tabular}{lr}
\toprule
\textbf{Categoria} & \textbf{Quantità} \\
\midrule
Font Analizzati (Post-Filtro) & """
# --------------------------------------------
LATEX_END_CODE_2 = r""" \\
\textcolor{successcolor}{\textbf{Font Funzionanti}} & \textbf{\arabic{cntWorking}} \\
\textcolor{errorcolor}{\textbf{Font Problematici}} & \textbf{\arabic{cntBroken}} \\
\textcolor{othercolor}{\textbf{Font Esclusi}} & \textbf{\arabic{cntExcluded}} \\
\bottomrule
\end{tabular}
\end{center}
\end{tcolorbox}

\section{Indice: Font Funzionanti}
\begin{multicols}{2}
\begin{itemize}
    \input{\jobname.working}
\end{itemize}
\end{multicols}

\section{Indice: Font Problematici}
\begin{multicols}{2}
\begin{itemize}
    \input{\jobname.broken}
\end{itemize}
\end{multicols}

\section{Indice: Font Esclusi}
\begin{multicols}{2}
\begin{itemize}
    \input{\jobname.excluded}
\end{itemize}
\end{multicols}

\end{document}
"""

# Font da escludere che causano crash o problemi noti
# Un font simbolico classico, spesso problematico in LuaTeX ma non installato in questo sistema è
#    "Hololens MDL2 Assets"
if IS_WINDOWS:
    EXCLUDED_FONTS = {
        "Segoe MDL2 Assets",
        "Segoe Fluent Icons",
        "MT Extra",
        "MS Reference Specialty",
        "MS Outlook",
        "Bookshelf Symbol 7",
        "Webdings",
        "Wingdings",
        "Wingdings 2",
        "Wingdings 3",
        "Marlett",
        "Symbol",
        "Microsoft YaHei",
        "Noto Sans Arabic",
        "Noto Sans Hebrew",
        "Yu Gothic",
    }

    TEST_FONTS = {"Times New Roman", "Arial", "Calibri", "Noto Sans"}
elif IS_LINUX:
    EXCLUDED_FONTS = {"Noto Emoji", "KacstScreen"}
    TEST_FONTS = {
        "Times New Roman",
        "Arial",
        "Calibri",
        "Noto Sans",
        "KaitiM",
        "Devanagari",
    }
else:
    EXCLUDED_FONTS = set()
    TEST_FONTS = set()

# Font non-Latini con configurazione linguistica/script specifica (polyglossia + fontspec options)
# NUOVO: Aggiunto il campo 'options' per specificare Script=...
# --- Funzioni di Sistema ---


def clean_font_name(name: str) -> str:
    """Normalize a raw font name to a family-like base name.

    Removes parenthetical hints like `(TrueType)`, and strips common
    variant suffixes (Bold, Italic, etc.).
    """
    # Rimuove "(TrueType)", "(OpenType)" e simili
    clean_name = re.sub(r"\s*\((TrueType|OpenType|True Type|Type 1)\)\s*$", "", name)

    # Regex potente per catturare varianti comuni (Bold, Italic, ecc. in ITA/ENG)
    variants = r"\s+(Bold|Italic|Light|Regular|Medium|Semibold|Black|Thin|Heavy|Narrow|Condensed|Extended|Grassetto|Corsivo|Chiaro|Normale|Medio|Nero|Sottile|Pesante|Condensato|Esteso).*$"
    base_name = re.sub(variants, "", clean_name, flags=re.IGNORECASE).strip()

    return base_name


def get_installed_fonts_windows():
    """Return a sorted list of installed font family names on Windows.

    The function reads the Windows registry and normalizes names via
    `clean_font_name`. Excluded names from `EXCLUDED_FONTS` are filtered out.
    """
    print("Sistema: Windows. Scansione registro...")
    font_list = set()
    registry_paths = [
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Fonts",
    ]

    for path in registry_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                for i in range(winreg.QueryInfoKey(key)[1]):
                    name, value, _ = winreg.EnumValue(key, i)

                    if re.search(r"\.(ttf|otf|ttc|fon)$", value, re.IGNORECASE):
                        base_name = clean_font_name(name)
                        if base_name and base_name not in EXCLUDED_FONTS:
                            font_list.add(base_name)

        except FileNotFoundError:
            continue

    return sorted(list(font_list))


def get_font_details_windows():
    """Return diagnostic details for installed Windows fonts (for tests).

    The returned list contains small dicts with `raw_line`, `extracted_names`
    and `base_names` useful for debugging parsing logic.
    """
    details = []
    registry_paths = [
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Fonts",
    ]

    for path in registry_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                for i in range(winreg.QueryInfoKey(key)[1]):
                    name, value, _ = winreg.EnumValue(key, i)

                    if re.search(r"\.(ttf|otf|ttc|fon)$", value, re.IGNORECASE):
                        base_name = clean_font_name(name)
                        details.append(
                            {
                                "raw_line": name,
                                "extracted_names": [name],
                                "base_names": [base_name],
                            }
                        )

        except FileNotFoundError:
            continue

    return details


def extract_font_family(line):
    """Extract the family portion from a `fc-list` line.

    Example input: '/usr/share/fonts/foo.ttf:Family Name:style'
    Returns the family part (comma-separated families are left intact).
    """
    parts = line.split(":")

    if len(parts) < 2:
        return ""
    elif len(parts) == 2:
        # Formato: path:family
        return parts[1].strip()
    else:
        # Formato: path:family:style o path:family:altro:style
        # Unisci tutti gli elementi tranne primo e ultimo
        return ":".join(parts[1:2]).strip()


def get_installed_fonts_linux() -> list[str]:
    """Return a sorted list of installed font family names on Linux using `fc-list`.

    Excluded families listed in `EXCLUDED_FONTS` are filtered out.
    """
    print("Sistema: Linux. Uso 'fc-list' per l'estrazione dei font...")
    try:
        # Esegue fc-list e cattura l'output
        result = subprocess.run(
            ["fc-list", ":family"], capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split("\n")

        font_list = set()
        for line in lines:
            if ":" in line:
                family_part = extract_font_family(line)
                for name in family_part.split(","):
                    base_name = name.strip()
                    if base_name and base_name not in EXCLUDED_FONTS:
                        font_list.add(base_name)

        return sorted(list(font_list))

    except FileNotFoundError:
        print(
            "Errore: 'fc-list' non trovato. Assicurati che fontconfig sia installato."
        )
        return []
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione di fc-list: {e}")
        return []


def get_font_details_linux() -> list[dict]:
    """Return diagnostic details for installed Linux fonts (for tests).

    Each item contains `raw_line`, `extracted_names` and `base_names` for
    easier inspection while tuning parsers.
    """
    details = []
    try:
        # Esegue fc-list e cattura l'output
        result = subprocess.run(
            ["fc-list", ":family"], capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split("\n")

        for line in lines:
            if ":" in line:
                family_part = extract_font_family(line)
                extracted_names = [
                    name.strip() for name in family_part.split(",") if name.strip()
                ]
                base_names = [clean_font_name(name) for name in extracted_names]
                details.append(
                    {
                        "raw_line": line,
                        "extracted_names": extracted_names,
                        "base_names": base_names,
                    }
                )

    except FileNotFoundError:
        print(
            "Errore: 'fc-list' non trovato. Assicurati che fontconfig sia installato."
        )
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione di fc-list: {e}")

    return details


def get_installed_fonts() -> list[str]:
    """Dispatch to platform-specific font discovery.

    Returns a sorted list of family names or an empty list on unsupported OS.
    """
    if IS_WINDOWS:
        return get_installed_fonts_windows()
    elif IS_LINUX:
        return get_installed_fonts_linux()
    else:
        print(f"Sistema operativo '{sys.platform}' non supportato o non riconosciuto.")
        return []


def generate_test_output(limit: int | None = None, filter_test: bool = False) -> None:
    """Produce a small text file with parsing details for manual inspection.

    Args:
        limit: if positive, limit first N items; if negative, take last |N|.
        filter_test: if True, keep only fonts matching `TEST_FONTS` substrings.
    """
    if IS_LINUX:
        details = get_font_details_linux()
    elif IS_WINDOWS:
        details = get_font_details_windows()
    else:
        print("Sistema non supportato per test.")
        return

    if filter_test:
        details = [
            item
            for item in details
            if any(
                sub.lower() in name.lower()
                for name in item["base_names"]
                for sub in TEST_FONTS
            )
        ]

    if limit:
        if limit > 0:
            details = details[:limit]
        else:
            details = details[limit:]

    # Ordina alfabeticamente per il primo nome base
    details.sort(key=lambda x: x["base_names"][0].lower() if x["base_names"] else "")

    base_name = f"test_output_{platform.system()}_{DATE_STR}"
    try:
        test_filename = get_unique_filename(base_name, "txt")
    except ValueError as e:
        print(f"Errore generazione file di test: {e}")
        return
    with open(test_filename, "w", encoding="utf-8") as f:
        for item in details:
            f.write(f"Raw line: {item['raw_line']}\n")
            f.write(f"Extracted names: {', '.join(item['extracted_names'])}\n")
            f.write(f"Base names: {', '.join(item['base_names'])}\n")
            f.write("\n")
    print(f"File di test generato: {test_filename}")


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in `text`.

    Returns a string safe to embed in LaTeX source.
    """
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(c, c) for c in text)


# --- Funzione di Generazione LaTeX Aggiornata ---


def generate_latex(font_list: list[dict]) -> str:
    """Generate the full LaTeX document for the provided font descriptors.

    The input may be a list of descriptors (as produced by
    `parse_font_inventory.py`) or a legacy list of strings (family names).
    """

    font_list = as_font_desc_list(font_list)

    # --- DEDUPLICAZIONE PER FAMIGLIA ---
    seen_families = set()
    unique_fonts = []
    for font in font_list:
        fam = font_family(font)
        if fam not in seen_families:
            seen_families.add(fam)
            unique_fonts.append(font)

    font_list = unique_fonts

    print(f"Generazione file LaTeX per {len(font_list)} font...")

    latex_code = LATEX_INITIAL_CODE

    total = len(font_list)
    for idx, font in enumerate(font_list, start=1):
        fam = font_family(font)
        safe_name = escape_latex(fam)
        badges = render_badges(font)
        sample_code = render_sample_code(font, fam)

        if idx % 500 == 0 or idx == total:
            print(f"  ... processati {idx}/{total}")

        block = NORMAL_BLOCK.format(
            safe_name=safe_name,
            font=fam,
            badges=badges,
            sample_code=sample_code,
        )
        latex_code += "\n" + block

    latex_code += "\n\n"
    for font in sorted(list(EXCLUDED_FONTS)):
        block = r"\LogExcluded{" + font + "}\n"
        latex_code += block

    # Chiusura documento e stampa indici
    latex_code += LATEX_END_CODE_1 + str(total) + LATEX_END_CODE_2
    return latex_code


# ============================================================
# Platform integration and CLI orchestration
# ============================================================
#
# This section contains:
# - platform-specific helpers (Linux / Windows),
# - optional legacy fallbacks,
# - LaTeX escaping utilities,
# - the CLI entry point (main).
#
# Design notes:
# - Platform detection is best-effort and defensive.
# - Failures in discovery or rendering should degrade gracefully,
#   producing partial output rather than aborting the whole run.
# - The CLI is intentionally thin: orchestration only, no business logic.
#


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera catalogo font di sistema in LaTeX"
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Genera file di testo ausiliario con dettagli del parsing",
    )
    parser.add_argument(
        "-T",
        "--TestFixed",
        action="store_true",
        help="Filtra solo i font che contengono sottostringhe in TEST_FONTS",
    )
    parser.add_argument(
        "--inventory",
        type=str,
        default=None,
        help="Percorso a font_inventory_enriched.json (se omesso, usa il default se presente).",
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        help="Limita il numero di font processati ai primi N (se positivo) o agli ultimi |N| (se negativo)",
    )
    args = parser.parse_args()

    # Genera nome file unico per il catalogo LaTeX
    base_name = f"catalogo_font_sistema_{platform.system()}_{DATE_STR}"
    try:
        OUTPUT_FILENAME = get_unique_filename(base_name, "tex")
    except ValueError as e:
        print(f"Errore: {e}")
        sys.exit(1)

    if args.test:
        generate_test_output(args.number, args.TestFixed)

    print("[1/3] Caricamento inventario font (pipeline)...")
    inv_path = None
    if args.inventory:
        inv_path = Path(args.inventory)
    else:
        default = Path(DEFAULT_INVENTORY)
        if default.exists():
            inv_path = default

    if inv_path and inv_path.exists():
        fonts = load_font_inventory(inv_path)
        print(f"✓ Inventario caricato: {inv_path} ({len(fonts)} font)")
    else:
        print("[1/3] Inventario non trovato, fallback a rilevamento legacy...")
        fonts = get_installed_fonts()
        if not fonts:
            print("✗ Nessun font da catalogare o errore di sistema.")
            sys.exit(1)
    if args.TestFixed:
        fonts = [
            f
            for f in as_font_desc_list(fonts)
            if any(sub.lower() in font_family(f).lower() for sub in TEST_FONTS)
        ]

    if args.number:
        if args.number > 0:
            fonts = fonts[: args.number]
        else:
            fonts = fonts[args.number :]

    # Ordina alfabeticamente la lista dei font
    fonts = sorted(as_font_desc_list(fonts), key=font_family)
    fonts = group_fonts_by_family(fonts)

    latex_content = generate_latex(fonts)

    print(f"[2/3] Scrittura file {OUTPUT_FILENAME}...")
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write(latex_content)
        print("✓ Fatto! File LaTeX generato correttamente.")
        print("[3/3] Pronto per la compilazione.")
        print(f"  Esegui: lualatex {OUTPUT_FILENAME} (due volte)")
    except Exception as e:
        print(f"✗ Errore scrittura file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
