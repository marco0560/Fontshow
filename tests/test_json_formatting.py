"""
Verify JSON formatting utilities.

Responsibilities
----------------
- Ensure pretty-printing compacts short numeric lists.
- Verify long lists remain expanded for readability.

Design principles
----------------
Formatting tests validate output structure so that JSON formatting
behavior remains stable and deterministic.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the JSON formatting utilities used by Fontshow.
"""

from fontshow.core.json_format import dumps_pretty


def test_dumps_pretty_compacts_short_numeric_lists():
    data = {"ranges": [[32, 95], [97, 127]]}
    s = dumps_pretty(data, indent=2, ensure_ascii=False)

    assert "  [32, 95]" in s
    assert "  [97, 127]" in s
    assert '"ranges": [\n' in s


def test_dumps_pretty_does_not_compact_long_numeric_lists():
    data = {"nums": list(range(20))}
    s = dumps_pretty(data, indent=2, ensure_ascii=False)

    assert '"nums": [\n' in s
    assert "[0, 1, 2, 3" not in s
