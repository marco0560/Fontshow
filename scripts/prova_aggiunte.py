"""Quick helper to produce a small LaTeX file listing excluded fonts.

This is a development convenience used to preview the set of excluded fonts
and produce an index file that can be included in the main catalog.
"""

import sys

# --- Configurazione ---
OUTPUT_FILENAME = "catalogo_font_esclusi.tex"
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
}

latex_text = r"""\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\usepackage{polyglossia} % Gestione multilingue avanzata
\setmainlanguage{italian}

% --------------------------------------

% Definiamo file di output temporanei per gli indici
\newwrite\fileExcluded
\immediate\openout\fileExcluded=\jobname.excluded

\protected\def\LogExcluded#1{%
    \immediate\write\fileExcluded{\unexpanded{\item} #1}%
}

\begin{document}

"""

for font in sorted(list(EXCLUDED_FONTS)):
    block = r"\LogExcluded{" + font + "}\n"
    latex_text += block

latex_text += r"""
\newpage

% Chiusura file degli indici
\immediate\closeout\fileExcluded

\section{Indice: Font Esclusi}
\begin{itemize}
    \input{\jobname.excluded}
\end{itemize}

\end{document}
"""
try:
    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        f.write(latex_text)
    print("✓ Fatto! File LaTeX generato correttamente.")
    print(f"  Esegui: lualatex {OUTPUT_FILENAME} (due volte)")
except Exception as e:
    print(f"✗ Errore scrittura file: {e}")
    sys.exit(1)
