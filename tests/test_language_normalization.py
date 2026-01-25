from fontshow.semantic_validation import normalize_languages


def test_empty_input():
    result = normalize_languages([])
    assert result["normalized"] == []
    assert result["dropped"] == []


def test_basic_normalization():
    result = normalize_languages(["en", "fr"])
    assert result["normalized"] == ["en", "fr"]
    assert result["dropped"] == []


def test_case_normalization():
    result = normalize_languages(["EN", "Fr"])
    assert result["normalized"] == ["en", "fr"]
    assert result["dropped"] == []


def test_variant_stripping():
    result = normalize_languages(["zh-hk", "pt_BR"])
    assert result["normalized"] == ["zh", "pt"]
    assert result["dropped"] == [
        {"raw": "zh-hk", "reason": "variant_stripped"},
        {"raw": "pt_BR", "reason": "variant_stripped"},
    ]


def test_duplicate_languages():
    result = normalize_languages(["en", "EN", "en"])
    assert result["normalized"] == ["en"]
    assert result["dropped"] == [
        {"raw": "EN", "reason": "duplicate"},
        {"raw": "en", "reason": "duplicate"},
    ]


def test_unknown_language():
    result = normalize_languages(["xx"])
    assert result["normalized"] == []
    assert result["dropped"] == [
        {"raw": "xx", "reason": "unknown_language"},
    ]


def test_mixed_case():
    result = normalize_languages(["ar_IN", "ar_IQ", "ar_JO"])
    assert result["normalized"] == ["ar"]
    assert result["dropped"] == [
        {"raw": "ar_IN", "reason": "variant_stripped"},
        {"raw": "ar_IQ", "reason": "duplicate"},
        {"raw": "ar_JO", "reason": "duplicate"},
    ]
