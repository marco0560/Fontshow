"""
Exercise Unicode table generator helper edge cases.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "generate_unicode_tables.py"
)
_SPEC = importlib.util.spec_from_file_location("generate_unicode_tables", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
generate_unicode_tables = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = generate_unicode_tables
_SPEC.loader.exec_module(generate_unicode_tables)


def test_merge_contiguous_ranges_handles_empty_and_singleton():
    """
    Ensure the helper handles the documented lower-boundary inputs.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert generate_unicode_tables._merge_contiguous_ranges([]) == []
    assert generate_unicode_tables._merge_contiguous_ranges([(1, 2)]) == [(1, 2)]


def test_merge_contiguous_ranges_rejects_malformed_tuples():
    """
    Ensure malformed tuple shapes fail clearly instead of merging silently.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    with pytest.raises(IndexError):
        generate_unicode_tables._merge_contiguous_ranges([(1, 2), (3,)])
