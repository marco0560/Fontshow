"""
LaTeX template fragments used by the catalog generator.

This module contains static LaTeX code blocks that form the structure
of the generated catalog document (preamble, headers, entry templates,
and footer).

Responsibilities
----------------
- Provide reusable LaTeX template strings.
- Keep large LaTeX fragments separate from Python logic.
- Allow document rendering code to assemble the final output
  without embedding long LaTeX blocks.

Design principles
-----------------
Templates are pure data and must not contain program logic. All LaTeX
escaping and rendering helpers live in ``latex.render`` and rendering
policy decisions live in ``latex.policy``.

Architectural role
------------------
This module belongs to the LaTeX infrastructure layer and is used by
catalog rendering modules such as ``catalog.document``.

IMPORTANT REMARK
----------------
Whitespace inside LaTeX templates is semantically relevant.
Changes here must avoid altering indentation or line breaks unless
explicitly intended.
"""

import platform

from fontshow import __version__
from fontshow.latex.render import escape_latex

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
%%FONTSHOW_OTHER_LANGUAGES%%

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

% --- Macros for summary sections ---
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

% Colors
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

% --- Counters and Indices ---
\newcounter{cntWorking}
\newcounter{cntBroken}
\newcounter{cntExcluded}
\setcounter{cntWorking}{0}
\setcounter{cntBroken}{0}
\setcounter{cntExcluded}{0}

% Temporary output file definition for indices
\newwrite\fileWorking
\immediate\openout\fileWorking=\jobname.working
\newwrite\fileBroken
\immediate\openout\fileBroken=\jobname.broken
\newwrite\fileExcluded
\immediate\openout\fileExcluded=\jobname.excluded

% Robust Macro for counting fonts (avoids expansion errors)
\protected\def\LogWorking#1{%
    \stepcounter{cntWorking}%
    \immediate\write\fileWorking{\string\item\space\detokenize{#1}}%
}

\protected\def\LogBroken#1{%
    \stepcounter{cntBroken}%
    \immediate\write\fileBroken{\string\item\space\detokenize{#1}}%
}

\protected\def\LogExcluded#1{%
    \stepcounter{cntExcluded}%
    \immediate\write\fileExcluded{\string\item\space\detokenize{#1}}%
}
% -----------------------------------

\SetLipsumText{cicero}
\newcommand{\Li}{\lipsum[1][1-4]}

\title{\Huge\textbf{\color{titlecolor}Catalogo Font di Sistema}}
\author{Generated with fontshow create-catalog """
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
