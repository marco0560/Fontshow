from fontshow.parse_font_inventory import infer_languages


def test_infer_languages_latn():
    scripts = ["latn"]

    languages = infer_languages(scripts)

    # We do not enforce ordering, only content
    assert "en" in languages
    assert "it" in languages
    assert "fr" in languages


def test_infer_languages_cyrillic():
    scripts = ["cyrl"]

    languages = infer_languages(scripts)

    assert "ru" in languages
    assert "uk" in languages


def test_infer_languages_mixed_scripts():
    scripts = ["latn", "grek"]

    languages = infer_languages(scripts)

    assert "en" in languages
    assert "it" in languages
    assert "el" in languages


def test_infer_languages_unknown_script():
    scripts = ["unknown"]

    languages = infer_languages(scripts)

    assert languages == []


def test_infer_languages_empty_input():
    scripts = []

    languages = infer_languages(scripts)

    assert languages == []
