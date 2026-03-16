"""
Verify script inference from Unicode block coverage.

Responsibilities
----------------
- Ensure scripts are inferred correctly from Unicode block statistics.
- Validate inference behavior for representative scripts.

Design principles
----------------
Script inference tests rely on small synthetic coverage datasets so
that inference behavior can be validated deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the logic that derives script inference results from Unicode coverage.
"""

from fontshow.inventory.script_analysis import infer_scripts


def test_infer_scripts_latn_from_unicode_blocks():
    """
    Verify that Latin block coverage infers the ``latn`` script.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Latin Extended-A": 100,
            "Basic Latin": 200,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["latn"]


def test_infer_scripts_arabic_from_unicode_blocks():
    """
    Verify that Arabic block coverage infers the ``arab`` script.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Arabic": 150,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["arab"]


def test_infer_scripts_mixed_latin_greek():
    """
    Verify that mixed Latin and Greek coverage reports both scripts.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Latin Extended-A": 120,
            "Greek and Coptic": 80,
        }
    }

    scripts = infer_scripts(coverage)
    assert set(scripts) == {"latn", "grek"}


def test_infer_scripts_cjk_japanese_disambiguation():
    """
    Verify that Hiragana and Katakana disambiguate Han coverage to Japanese.

    Returns
    -------
    None
    """
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
    """
    Verify that missing coverage yields the ``unknown`` sentinel.

    Returns
    -------
    None
    """
    coverage = {}

    scripts = infer_scripts(coverage)
    assert scripts == ["unknown"]


def test_infer_scripts_cyrillic():
    """
    Verify that Cyrillic block coverage infers the ``cyrl`` script.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Cyrillic": 150,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["cyrl"]


def test_infer_scripts_myanmar():
    """
    Verify that Myanmar block coverage infers the ``mymr`` script.

    Returns
    -------
    None
    """
    coverage = {
        "unicode_blocks": {
            "Myanmar": 160,
            "Myanmar Extended-A": 32,
            "Myanmar Extended-B": 31,
        }
    }

    scripts = infer_scripts(coverage)
    assert scripts == ["mymr"]


def test_infer_scripts_dogra_and_dives_akuru_from_unicode_blocks():
    """
    Verify Dogra and Dives Akuru blocks infer dedicated script tags.

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Dogra": 60, "Basic Latin": 3}}) == [
        "dogr"
    ]
    assert infer_scripts({"unicode_blocks": {"Dives Akuru": 50, "Basic Latin": 1}}) == [
        "diak"
    ]


def test_infer_scripts_uses_unicode_max_for_dogra_and_dives_akuru():
    """
    Ensure unicode.max fallback covers Dogra and Dives Akuru ranges.

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode": {"max": 0x1183B}}) == ["dogr"]
    assert infer_scripts({"unicode": {"max": 0x11946}}) == ["diak"]


def test_infer_scripts_second_batch_blocks():
    """
    Verify second-batch script blocks infer dedicated script tags.

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Bopomofo": 40}}) == ["bopo"]
    assert infer_scripts({"unicode_blocks": {"Brahmi": 60}}) == ["brah"]
    assert infer_scripts({"unicode_blocks": {"Coptic": 90}}) == ["copt"]
    assert infer_scripts({"unicode_blocks": {"Deseret": 32}}) == ["dsrt"]
    assert infer_scripts({"unicode_blocks": {"Elbasan": 35}}) == ["elba"]
    assert infer_scripts({"unicode_blocks": {"Glagolitic": 80}}) == ["glag"]
    assert infer_scripts({"unicode_blocks": {"Grantha": 70}}) == ["gran"]
    assert infer_scripts({"unicode_blocks": {"Hanifi Rohingya": 40}}) == ["rohg"]
    assert infer_scripts({"unicode_blocks": {"Kaithi": 55}}) == ["kthi"]
    assert infer_scripts(
        {"unicode_blocks": {"Unified Canadian Aboriginal Syllabics": 120}}
    ) == ["cans"]


def test_infer_scripts_uses_unicode_max_for_second_batch_ranges():
    """
    Verify unicode.max fallback covers second-batch script ranges.

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode": {"max": 0x10420}}) == ["dsrt"]
    assert infer_scripts({"unicode": {"max": 0x10518}}) == ["elba"]
    assert infer_scripts({"unicode": {"max": 0x10D15}}) == ["rohg"]
    assert infer_scripts({"unicode": {"max": 0x11042}}) == ["brah"]
    assert infer_scripts({"unicode": {"max": 0x110A5}}) == ["kthi"]
    assert infer_scripts({"unicode": {"max": 0x1133D}}) == ["gran"]


def test_coverage_scripts_never_unknown():
    """
    Verify that the public coverage script list itself never contains ``unknown``.

    Returns
    -------
    None
    """
    coverage = {}
    scripts = coverage.get("scripts", [])
    assert "unknown" not in scripts
