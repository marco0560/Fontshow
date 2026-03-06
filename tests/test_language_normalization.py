from fontshow.inventory.semantic_validation import normalize_languages


def test_empty_input():
    result = normalize_languages([])
    assert result["normalized"] == []
    assert result["deprecated"] == []
    assert result["dropped"] == []


def test_basic_normalization():
    result = normalize_languages(["en", "fr"])
    assert result["normalized"] == ["en", "fr"]
    assert result["deprecated"] == []
    assert result["dropped"] == []


def test_case_normalization():
    result = normalize_languages(["EN", "Fr"])
    assert result["normalized"] == ["en", "fr"]
    assert result["deprecated"] == []
    assert result["dropped"] == []


def test_deprecated_language_mapping():
    result = normalize_languages(["mo"])
    assert result["normalized"] == ["ro"]
    assert result["deprecated"] == [{"raw": "mo", "from_": "mo", "to": "ro"}]
    assert result["dropped"] == []


def test_variant_stripping():
    result = normalize_languages(["zh-hk", "pt_BR"])
    assert result["normalized"] == ["zh", "pt"]
    assert result["deprecated"] == []
    assert result["dropped"] == [
        {"raw": "zh-hk", "reason": "variant_stripped"},
        {"raw": "pt_BR", "reason": "variant_stripped"},
    ]


def test_duplicate_languages():
    result = normalize_languages(["en", "EN", "en"])
    assert result["normalized"] == ["en"]
    assert result["deprecated"] == []
    assert result["dropped"] == [
        {"raw": "EN", "reason": "duplicate_normalized", "normalized": "en"},
        {"raw": "en", "reason": "duplicate_normalized", "normalized": "en"},
    ]


def test_unknown_language():
    result = normalize_languages(["xx"])
    assert result["normalized"] == []
    assert result["deprecated"] == []
    assert result["dropped"] == [
        {"raw": "xx", "reason": "unknown_language"},
    ]


def test_mixed_case():
    result = normalize_languages(["ar_IN", "ar_IQ", "ar_JO"])
    assert result["normalized"] == ["ar"]
    assert result["deprecated"] == []
    assert result["dropped"] == [
        {"raw": "ar_IN", "reason": "variant_stripped"},
        {"raw": "ar_IQ", "reason": "duplicate_normalized", "normalized": "ar"},
        {"raw": "ar_JO", "reason": "duplicate_normalized", "normalized": "ar"},
    ]
