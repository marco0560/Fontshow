from helpers import minimal_valid_entry

from fontshow.parse_font_inventory import validate_inventory


def test_validate_inventory_valid_minimal():
    data = {"metadata": {"schema_version": "1.0"}, "fonts": [minimal_valid_entry()]}

    result = validate_inventory(data)
    assert result == 0


def test_validate_inventory_invalid_root():
    result = validate_inventory([])
    assert result > 0


def test_validate_inventory_missing_fonts():
    data = {"metadata": {"schema_version": "1.0"}}

    result = validate_inventory(data)
    assert result > 0


def test_validate_inventory_with_invalid_entry():
    data = {
        "metadata": {"schema_version": "1.0"},
        "fonts": [
            {
                "path": "/tmp/broken.ttf"
                # missing format, style, family
            }
        ],
    }

    result = validate_inventory(data)
    assert result > 0


def test_validate_inventory_warning_only():
    entry = minimal_valid_entry({"base_names": None})

    data = {"metadata": {"schema_version": "1.0"}, "fonts": [entry]}

    result = validate_inventory(data)
    assert result == 0


def test_validate_inventory_missing_schema_version():
    data = {"fonts": [minimal_valid_entry()]}

    result = validate_inventory(data)
    assert result == 0
