import os
import sys
from datetime import date

# --- Configurazione ---
OUTPUT_FILENAME = "catalogo_font_esclusi.tex"

# Lista dei font esclusi dal catalogo principale
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
    "Symbol"
}

# Stringhe di testo per il test
TEST_STRING_ALPHA = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9"
LIPSUM_TEXT = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."

def generate_excluded_latex(excluded_fonts):
    """Genera il codice LaTeX per il catalogo dei font esclusi."""
    latex_parts = []

    # Intestazione LaTeX
    latex_parts.append(r"""
\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\usepackage{xcolor}
\usepackage{tcolorbox}
\usepackage{geometry}
\usepackage{lipsum}

\geometry{margin=2cm}

\definecolor{errorcolor}{HTML}{dc3545}

% Box per evidenziare i font esclusi
\tcbuselibrary{skins}
\newtcolorbox{excludebox}[1]{
    colback=errorcolor!10, colframe=errorcolor!80!black, boxrule=1pt, arc=3pt,
    title={\textbf{Font Escluso: #1}}, coltitle=white, colbacktitle=errorcolor!80!black
}

\begin{document}

\title{\Huge Catalogo dei Font Esclusi}
\author{Script Python}
\date{""" + str(date.today()) + r"""}
\maketitle
\tableofcontents

\section{Motivazione dell'Esclusione}
Questi font sono stati esclusi dal catalogo principale per i seguenti motivi:
\begin{itemize}
    \item Sono font simbolici (\texttt{Wingdings}, \texttt{Marlett}, ecc.) che non contengono un set completo di caratteri latini standard.
    \item Hanno causato errori, crash o problemi di compatibilità significativi con \texttt{LuaLaTeX} in test precedenti.
    \item Non sono destinati alla composizione di testo standard.
\end{itemize}

\section{Esempi dei Font Esclusi}
""")

    # Corpo del documento: test per ogni font escluso
    for font_name in sorted(excluded_fonts):
        latex_parts.append(f"\\subsection{{{font_name}}}\n")
        latex_parts.append(f"\\begin{{excludebox}}{{{font_name}}}\n")
        latex_parts.append(f"    \\centering \\Large {TEST_STRING_ALPHA}\n")
        latex_parts.append(r"    \vspace{0.5em}")
        latex_parts.append(r"    \textbf{Test Lipsum (Visualizza i caratteri simbolici):}")
        latex_parts.append(f"    {{\\fontspec{{{font_name}}}\\small {LIPSUM_TEXT}}}\n")
        latex_parts.append(f"\\end{{excludebox}}\n")
        latex_parts.append(r"\vspace{1em}")


    # Chiusura LaTeX
    latex_parts.append(r"""
\end{document}
""")

    return "\n".join(latex_parts)

def main():
    """Generazione principale del catalogo dei font esclusi"""
    print("===========================================")
    print("  GENERATORE CATALOGO FONT ESCLUSI (Py)")
    print("===========================================")
    print(f"Font da catalogare: {len(EXCLUDED_FONTS)}")

    # Genera il contenuto LaTeX
    latex_content = generate_excluded_latex(EXCLUDED_FONTS)

    # Scrivi il file
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        print("\n" + "="*50)
        print(f"✓ File LaTeX creato con successo: {OUTPUT_FILENAME}")
        print(f"Per compilare: lualatex \"{OUTPUT_FILENAME}\"")
        print("="*50 + "\n")

    except Exception as e:
        print(f"✗ Errore durante la scrittura del file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
