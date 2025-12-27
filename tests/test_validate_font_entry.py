from helpers import minimal_valid_entry

from fontshow.parse_font_inventory import validate_font_entry


def test_validate_font_entry_valid_minimal():
    entry = minimal_valid_entry()

    errors = validate_font_entry(entry, index=0)
    assert errors == []


def test_validate_font_entry_not_a_dict():
    entry = "not a dict"

    errors = validate_font_entry(entry, index=0)
    assert errors  # must contain at least one error


def test_validate_font_entry_missing_identity_and_base_names():
    entry = {"identity": {}}

    errors = validate_font_entry(entry, index=0)
    assert errors  # fatal error expected


def test_validate_font_entry_missing_identity_but_base_names_present():
    entry = minimal_valid_entry({"identity": None})

    errors = validate_font_entry(entry, index=0)
    assert errors == []


def test_validate_font_entry_missing_base_names_but_identity_present():
    entry = minimal_valid_entry({"base_names": None})

    errors = validate_font_entry(entry, index=0)
    assert errors == []


def test_validate_font_entry_identity_wrong_type():
    entry = {"identity": "not a dict", "base_names": ["Name"]}

    errors = validate_font_entry(entry, index=0)
    assert errors  # structural error
