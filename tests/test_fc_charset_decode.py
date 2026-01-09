from fontshow.parse_font_inventory import decode_fc_charset_bitmap


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
