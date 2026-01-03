from fontshow.parse_font_inventory import validate_inventory
from tests.helpers import minimal_valid_entry


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


def test_missing_family_adds_warning():
    entry = {
        "identity": {},
        "base_names": [],
        "path": "/tmp/font.ttf",
    }

    data = {"fonts": [entry], "metadata": {}}
    validate_inventory(data)

    assert "warnings" in entry
    assert entry["warnings"][0]["code"] == "missing_family"


def test_quiet_suppresses_output(capsys):
    data = {"fonts": [], "metadata": {}}
    validate_inventory(data, quiet=True)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_verbose_shows_warning(capsys):
    entry = {"identity": {}, "base_names": []}
    data = {"fonts": [entry], "metadata": {}}
    validate_inventory(data, verbose=True)
    captured = capsys.readouterr()
    assert "missing_family" in captured.out


def test_inventory_warnings_are_serialized():
    entry = {"identity": {}, "base_names": []}
    data = {"fonts": [entry], "metadata": {}}

    validate_inventory(data)

    assert "warnings" in data
    assert isinstance(data["warnings"], list)
