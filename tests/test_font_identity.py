from fontshow.dump_fonts import make_font_id


def test_font_identity_id_stable():
    id1 = make_font_id("/path/font.ttc", 0)
    id2 = make_font_id("/path/font.ttc", 0)
    id3 = make_font_id("/path/font.ttc", 1)
    id4 = make_font_id("/path/font.ttf", None)

    assert id1 == id2
    assert id1 != id3
    assert id1 != id4
