from fontshow.inventory.semantic_validation import validate_language_codes


def test_valid_language_codes_no_warnings():
    inventory = {
        "fonts": [
            {
                "coverage": {"languages": ["en", "fr"]},
                "inference": {"languages": ["de"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert warnings == []


def test_invalid_inferred_language_code_emits_warning():
    inventory = {
        "fonts": [
            {
                "inference": {"languages": ["zz"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert len(warnings) == 1
    w = warnings[0]
    assert w["code"] == "invalid_language_code"
    assert w["language"] == "zz"


def test_invalid_declared_language_code_emits_warning():
    inventory = {
        "fonts": [
            {
                "coverage": {"languages": ["xx"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert len(warnings) == 1
    assert warnings[0]["language"] == "xx"


def test_unknown_language_code_is_ignored():
    inventory = {
        "fonts": [
            {
                "inference": {"languages": ["unknown"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert warnings == []


def test_duplicate_language_codes_emit_single_warning():
    inventory = {
        "fonts": [
            {
                "coverage": {"languages": ["zz"]},
                "inference": {"languages": ["zz"]},
            }
        ]
    }

    warnings = validate_language_codes(inventory)

    assert len(warnings) == 1
