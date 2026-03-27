"""
Verify font identity generation utilities.

Responsibilities
----------------
- Ensure the generated font identifier is stable for identical inputs.
- Ensure different font indices or file paths produce distinct identifiers.

Design principles
-----------------
Identity tests rely on deterministic synthetic inputs so that the
identifier generation logic can be validated without accessing real fonts.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the deterministic construction of font identity values.
"""

from fontshow.inventory.utils import make_font_id


def test_font_identity_id_stable():
    """
    Verify that font identifiers are stable for identical inputs and differ otherwise.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    id1 = make_font_id("/path/font.ttc", 0)
    id2 = make_font_id("/path/font.ttc", 0)
    id3 = make_font_id("/path/font.ttc", 1)
    id4 = make_font_id("/path/font.ttf", None)

    assert id1 == id2
    assert id1 != id3
    assert id1 != id4
