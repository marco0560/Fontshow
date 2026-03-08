"""
Verify decoding of Fontconfig charset bitmaps.

Responsibilities
----------------
- Ensure bitmap representations of charset ranges are decoded correctly.
- Validate handling of single bits, contiguous ranges, and merged blocks.

Design principles
----------------
Decoding tests use synthetic Fontconfig bitmap strings so that charset
range decoding behavior can be verified deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the bitmap decoding utilities used to interpret Fontconfig charset data.
"""

from fontshow.unicode.charset_ranges import decode_fc_charset_bitmap


def test_decode_single_bit():
    raw = (
        "0000: 80000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000"
    )
    assert decode_fc_charset_bitmap(raw) == [[0, 0]]


def test_decode_contiguous_range():
    raw = (
        "0000: ffffffff 00000000 00000000 00000000 00000000 00000000 00000000 00000000"
    )
    assert decode_fc_charset_bitmap(raw) == [[0, 31]]


def test_decode_multiple_blocks_merge():
    raw = (
        "0000: 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000001\n"
        "0001: 80000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000"
    )
    assert decode_fc_charset_bitmap(raw) == [[255, 256]]
