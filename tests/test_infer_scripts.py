from fontshow.parse_font_inventory import infer_scripts


def test_infer_scripts_latn_from_unicode_blocks():
    coverage = {
        "unicode_blocks": {
            "Latin Extended-A": 100,
            "Basic Latin": 200,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["latn"]


def test_infer_scripts_arabic_from_unicode_blocks():
    coverage = {
        "unicode_blocks": {
            "Arabic": 150,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["arab"]


def test_infer_scripts_mixed_latin_greek():
    coverage = {
        "unicode_blocks": {
            "Latin Extended-A": 120,
            "Greek and Coptic": 80,
        }
    }

    scripts = infer_scripts(coverage)
    assert set(scripts) == {"latn", "grek"}


def test_infer_scripts_cjk_japanese_disambiguation():
    coverage = {
        "unicode_blocks": {
            "Hiragana": 80,
            "Katakana": 90,
            "CJK Unified Ideographs": 200,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["jpan"]


def test_infer_scripts_unknown_when_no_coverage():
    coverage = {}

    scripts = infer_scripts(coverage)
    assert scripts == ["unknown"]


def test_infer_scripts_cyrillic():
    coverage = {
        "unicode_blocks": {
            "Cyrillic": 150,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["cyrl"]
