"""Exercise CLI formatting helper boundaries."""

from fontshow.core.cli_utils import _format_extra


def test_format_extra_handles_empty_and_boundary_sizes():
    """
    Ensure empty, compact, and multiline boundaries are stable.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert _format_extra({}) == ""
    assert _format_extra({"b": 2, "a": 1}) == " | a=1 | b=2"

    large = {f"k{i}": i for i in range(6)}
    formatted = _format_extra(large)

    assert formatted.startswith("\n")
    assert "k0" in formatted
    assert "k5" in formatted
