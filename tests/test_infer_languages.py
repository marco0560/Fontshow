from fontshow.inventory.infer_languages import infer_languages


def test_infer_languages_latn():
    coverage = {
        "unicode_blocks": {
            "Basic Latin": 95,
        }
    }

    result = infer_languages(coverage)
    languages = result.keys()

    assert "en" in languages


def test_infer_languages_cyrillic():
    coverage = {
        "unicode_blocks": {
            "Cyrillic": 128,
        }
    }

    result = infer_languages(coverage)
    languages = result.keys()

    assert "ru" in languages


def test_infer_languages_mixed_scripts():
    coverage = {
        "unicode_blocks": {
            "Basic Latin": 95,
            "Greek and Coptic": 120,
        }
    }

    result = infer_languages(coverage)
    languages = result.keys()

    assert "en" in languages
    assert "el" in languages


def test_infer_languages_unknown_script():
    coverage = {"unicode_blocks": {}}

    result = infer_languages(coverage)

    assert result == {}


def test_infer_languages_empty_input():
    result = infer_languages({})

    assert result == {}
