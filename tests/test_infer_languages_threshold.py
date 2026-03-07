from fontshow.inventory.infer_languages import infer_languages


def test_greek_not_inferred_from_symbolic_coverage():
    coverage = {
        "unicode_blocks": {
            "Greek and Coptic": 2,  # presenza simbolica
            "Basic Latin": 95,
        }
    }

    languages = infer_languages(coverage)
    codes = set(languages.keys())

    assert "el" not in codes


def test_greek_inferred_with_sufficient_block_coverage():
    # Greek and Coptic size ≈ 135
    # 72 / 135 ≈ 0.53 > 0.40
    coverage = {
        "unicode_blocks": {
            "Greek and Coptic": 72,
        }
    }

    languages = infer_languages(coverage)
    codes = set(languages.keys())

    assert "el" in codes


def test_latin_languages_not_regressed():
    coverage = {
        "unicode_blocks": {
            "Basic Latin": 95,  # 95 / 128 ≈ 0.74
            "Latin-1 Supplement": 96,  # 96 / 128 = 0.75
            "Latin Extended-A": 110,  # supporto opzionale
        }
    }

    languages = infer_languages(coverage)
    codes = set(languages.keys())

    assert "en" in codes
    assert "fr" in codes
    assert "de" in codes
