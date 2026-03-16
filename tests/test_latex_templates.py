"""
Verify LaTeX template invariants used by catalog generation.
"""

from fontshow.latex import templates


def test_testnonlatin_macro_is_not_defined_in_template():
    """
    Ensure non-Latin rendering no longer depends on a TeX-side helper macro.
    """
    macro = templates.LATEX_INITIAL_CODE

    assert r"\newcommand{\TestNonLatin}[4]{" not in macro
