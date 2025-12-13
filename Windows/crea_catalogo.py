import winreg
import re
import os
import sys
import platform
import subprocess

# --- Configurazione ---
OUTPUT_FILENAME = "catalogo_font_sistema.tex"
# Font da escludere che causano crash o problemi noti
# Un font simbolico classico, spesso problematico in LuaTeX ma non installato in questo sistema è
#    "Hololens MDL2 Assets"
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
    "Yu Gothic"
}

# Font non-Latini con configurazione linguistica/script specifica (polyglossia + fontspec options)
# NUOVO: Aggiunto il campo 'options' per specificare Script=...
SPECIAL_SCRIPT_FONTS = {
    # Font esistenti
    "Noto Sans Arabic": {"lang": "arabic", "options": "Script=Arabic", "text": "أهلا وسهلاً! هذا نص تجريبي باللغة العربية. (Scrittura RTL corretta)"},  # Arabo (RTL)
    "Noto Sans Hebrew": {"lang": "hebrew", "options": "Script=Hebrew", "text": "שלום עולם! זה טקסט בדיקה בעברית. (Scrittura RTL corretta)"},  # Ebraico (RTL)
    "Noto Sans CJK JP": {"lang": "japanese", "options": "Script=CJK", "text": "こんにちは、世界！これは日本語のテストテキストです。"},  # Giapponese (CJK)
    "Noto Sans Thai": {"lang": "thai", "options": "Script=Thai", "text": "สวัสดีครับ นี่คือข้อความทดสอบภาษาไทย"},  # Tailandese
    
    # --- NUOVE VOCI PER CINESE, GIAPPONESE E HINDI ---
    "Yu Gothic": {"lang": "japanese", "options": "Script=Japanese", "text": "こんにちは世界！これは日本語のテストテキストです。"},  # Giapponese (Script=Japanese)
    "Microsoft YaHei": {"lang": "chinese", "options": "Script=Han", "text": "你好世界! 这是一个中文测试文本。"}, # Cinese Semplificato (Script=Han)
    "Nirmala UI": {"lang": "hindi", "options": "Script=Devanagari", "text": "नमस्ते दुनिया! यह एक हिन्दी परीक्षण पाठ है।"}, # Hindi (Devanagari)
    # --- FINE NUOVE VOCI ---
    
    # Aggiungi qui eventuali altri font speciali
}

# --- Funzioni di Sistema (Identiche alla V3) ---

def clean_font_name(name):
    """Pulisce il nome del font per ottenere il nome della famiglia."""
    # Rimuove "(TrueType)", "(OpenType)" e simili
    clean_name = re.sub(r'\s*\((TrueType|OpenType|True Type|Type 1)\)\s*$', '', name)
    
    # Regex potente per catturare varianti comuni (Bold, Italic, ecc. in ITA/ENG)
    variants = r'\s+(Bold|Italic|Light|Regular|Medium|Semibold|Black|Thin|Heavy|Condensed|Extended|Grassetto|Corsivo|Chiaro|Normale|Medio|Nero|Sottile|Pesante|Condensato|Esteso).*$'
    base_name = re.sub(variants, '', clean_name, flags=re.IGNORECASE).strip()
    
    return base_name

def get_installed_fonts_windows():
    """Recupera la lista dei font installati dal registro di Windows."""
    print("Sistema: Windows. Scansione registro...")
    font_list = set()
    registry_paths = [
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Fonts"
    ]
    
    for path in registry_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                for i in range(winreg.QueryInfoKey(key)[1]):
                    name, value, _ = winreg.EnumValue(key, i)
                    
                    if re.search(r'\.(ttf|otf|ttc|fon)$', value, re.IGNORECASE):
                        base_name = clean_font_name(name)
                        if base_name and base_name not in EXCLUDED_FONTS:
                            font_list.add(base_name)
                        
        except FileNotFoundError:
            continue
            
    return sorted(list(font_list))

def get_installed_fonts_linux():
    """Recupera la lista dei font installati su Linux usando fc-list."""
    print("Sistema: Linux. Uso 'fc-list' per l'estrazione dei font...")
    try:
        # Esegue fc-list e cattura l'output
        result = subprocess.run(['fc-list', ':family'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        font_list = set()
        for line in lines:
            if ':' in line:
                family_part = line.split(':')[-1].strip()
                for name in family_part.split(','):
                    base_name = name.strip()
                    if base_name and base_name not in EXCLUDED_FONTS:
                        font_list.add(base_name)
                        
        return sorted(list(font_list))
        
    except FileNotFoundError:
        print("Errore: 'fc-list' non trovato. Assicurati che fontconfig sia installato.")
        return []
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione di fc-list: {e}")
        return []

def get_installed_fonts():
    """Determina il sistema operativo e richiama la funzione appropriata."""
    system = platform.system()
    
    if system == "Windows":
        return get_installed_fonts_windows()
    elif system == "Linux":
        return get_installed_fonts_linux()
    else:
        print(f"Sistema operativo '{system}' non supportato o non riconosciuto.")
        return []

def escape_latex(text):
    """Esegue l'escape dei caratteri speciali LaTeX."""
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}'
    }
    return "".join(replacements.get(c, c) for c in text)

# --- Funzione di Generazione LaTeX Aggiornata ---

def generate_latex(font_list):
    """Genera il codice LaTeX completo, con la nuova macro per Script/Opzioni."""
    print(f"Generazione file LaTeX per {len(font_list)} font...")
    
    latex_code = r"""\documentclass[11pt,a4paper]{article}
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
\author{Generato da Python in \texttt{""" + platform.system() + r"""}}
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

    # Loop sui font
    total = len(font_list)
    for idx, font in enumerate(font_list):
        safe_name = escape_latex(font)
        
        if idx % 50 == 0:
            print(f"  ... processati {idx}/{total}")

        # Inizializza l'esempio di testo standard (Lipsum)
        sample_code = r"""\textbf{Test Latino (Lipsum):}
    {\fontspec{""" + font + r"""}
    \Li
    }"""
        
        # Gestione Esempi: Testo specifico per lingua
        if font in SPECIAL_SCRIPT_FONTS:
            spec = SPECIAL_SCRIPT_FONTS[font]
            sample_text = escape_latex(spec["text"])
            lang_tag = spec["lang"]
            font_options = spec["options"] # <-- NUOVO: Opzioni Fontspec

            sample_code = f"""\\TestNonLatin{{{font}}}{{{lang_tag}}}{{{font_options}}}{{{sample_text}}}
            """
        else:
             # Usa il codice standard se non è un font con script speciale
             sample_code = r"""\textbf{Test Latino (Lipsum):}
    {\fontspec{""" + font + r"""}
    \Li
    }"""


        # Blocco LaTeX per il singolo font
        block =f"""\\subsection{{{safe_name}}}

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
\\vspace{{1em}}"""
        latex_code += "\n\n"
        latex_code += block

    latex_code += "\n\n"
    for font in sorted(list(EXCLUDED_FONTS)):
        block = r"\LogExcluded{" + font + "}\n"
        latex_code += block


    # Chiusura documento e stampa indici
    latex_code += r"""\newpage

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
Font Analizzati (Post-Filtro) & """ + str(total) + r""" \\
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
    return latex_code

def main():
    print("[1/3] Rilevamento font in corso...")
    fonts = get_installed_fonts()
    if not fonts:
        print("✗ Nessun font da catalogare o errore di sistema.")
        sys.exit(1)
        
    latex_content = generate_latex(fonts)
    
    print(f"[2/3] Scrittura file {OUTPUT_FILENAME}...")
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write(latex_content)
        print("✓ Fatto! File LaTeX generato correttamente.")
        print(f"[3/3] Pronto per la compilazione.")
        print(f"  Esegui: lualatex {OUTPUT_FILENAME} (due volte)")
    except Exception as e:
        print(f"✗ Errore scrittura file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()