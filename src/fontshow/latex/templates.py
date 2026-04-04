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

\setmainlanguage{english}
% Secondary languages for testing non-Latin scripts
%%FONTSHOW_OTHER_LANGUAGES%%

\geometry{margin=2cm}

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
%    title={\textbf{Not Loadable: #1}}, coltitle=white, colbacktitle=errorcolor!80!black%
%}
\newenvironment{errorbox}[1]{}{}

\SetLipsumText{cicero}
\newcommand{\Li}{\lipsum[1][1-4]}

\title{\Huge\textbf{\color{titlecolor}System Font Catalog}}
\author{Generated with fontshow create-catalog """
    + escape_latex(__version__)
    + r"""}
\date{%%FONTSHOW_GENERATED_AT%%}

\begin{document}

\maketitle

\begin{center}
{\small\ttfamily System: %%FONTSHOW_SYSTEM_NAME%%}\\
{\small\ttfamily Host: %%FONTSHOW_HOSTNAME%%}\\
\vspace{0.5em}
\parbox{0.95\linewidth}{\raggedright\emph{\footnotesize\ttfamily %%FONTSHOW_COMMAND_LINE%%}}
\end{center}
\vspace{0.75em}

\begin{abstract}
This document catalogs the fonts installed on the system.
Problematic fonts are excluded in advance. The compilation is performed with \textbf{LuaLaTeX}.
\end{abstract}
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

\section{Summary and Statistics}

\begin{tcolorbox}[colback=white, colframe=gray]
\begin{center}
\Large\textbf{Final Statistics}
\vspace{1em}

\begin{tabular}{lr}
\toprule
\textbf{Category} & \textbf{Quantity} \\
\midrule
Analyzed Families & """
# --------------------------------------------
LATEX_END_CODE_2: str = r""" \\
\bottomrule
\end{tabular}
\end{center}
\end{tcolorbox}

\end{document}
"""
