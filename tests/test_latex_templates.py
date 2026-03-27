"""
Verify LaTeX template invariants used by catalog generation.
"""

from fontshow.latex import templates


def test_testnonlatin_macro_is_not_defined_in_template():
    """
    Ensure non-Latin rendering no longer depends on a TeX-side helper macro.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    macro = templates.LATEX_INITIAL_CODE

    assert r"\newcommand{\TestNonLatin}[4]{" not in macro


def test_template_logging_macros_write_auxiliary_lists():
    """
    Ensure summary logging macros feed the auxiliary list files again.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    macro = templates.LATEX_INITIAL_CODE

    assert r"\immediate\write\fileWorking{\string\item\space\detokenize{#1}}" in macro
    assert r"\immediate\write\fileBroken{\string\item\space\detokenize{#1}}" in macro
    assert r"\immediate\write\fileExcluded{\string\item\space\detokenize{#1}}" in macro
