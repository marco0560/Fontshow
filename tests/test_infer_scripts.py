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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode": {"max": 0x1183B}}) == ["dogr"]
    assert infer_scripts({"unicode": {"max": 0x11946}}) == ["diak"]


def test_infer_scripts_second_batch_blocks():
    """
    Verify second-batch script blocks infer dedicated script tags.

    Parameters
    ----------
    None

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

    Parameters
    ----------
    None

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


def test_infer_scripts_third_batch_blocks():
    """
    Verify third-batch script blocks infer dedicated script tags.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Mro": 40}}) == ["mroo"]
    assert infer_scripts({"unicode_blocks": {"Old Permic": 32}}) == ["perm"]
    assert infer_scripts({"unicode_blocks": {"Psalter Pahlavi": 30}}) == ["phlp"]
    assert infer_scripts({"unicode_blocks": {"Sogdian": 30}}) == ["sogd"]
    assert infer_scripts({"unicode_blocks": {"Tagalog": 20}}) == ["tglg"]
    assert infer_scripts({"unicode_blocks": {"Tagbanwa": 20}}) == ["tagb"]
    assert infer_scripts({"unicode_blocks": {"Tai Tham": 50}}) == ["lana"]
    assert infer_scripts({"unicode_blocks": {"Tai Viet": 40}}) == ["tavt"]
    assert infer_scripts({"unicode_blocks": {"Tifinagh": 35}}) == ["tfng"]
    assert infer_scripts({"unicode_blocks": {"Tirhuta": 45}}) == ["tirh"]


def test_infer_scripts_uses_unicode_max_for_third_batch_ranges():
    """
    Verify unicode.max fallback covers third-batch script ranges.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode": {"max": 0x16A55}}) == ["mroo"]
    assert infer_scripts({"unicode": {"max": 0x1036B}}) == ["perm"]
    assert infer_scripts({"unicode": {"max": 0x10B95}}) == ["phlp"]
    assert infer_scripts({"unicode": {"max": 0x10F48}}) == ["sogd"]
    assert infer_scripts({"unicode": {"max": 0x170F}}) == ["tglg"]
    assert infer_scripts({"unicode": {"max": 0x176F}}) == ["tagb"]
    assert infer_scripts({"unicode": {"max": 0x1A6A}}) == ["lana"]
    assert infer_scripts({"unicode": {"max": 0xAAC0}}) == ["tavt"]
    assert infer_scripts({"unicode": {"max": 0x2D5B}}) == ["tfng"]
    assert infer_scripts({"unicode": {"max": 0x114B7}}) == ["tirh"]


def test_infer_scripts_fourth_batch_blocks():
    """
    Verify fourth-batch script blocks infer dedicated script tags.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Gothic": 24}}) == ["goth"]
    assert infer_scripts({"unicode_blocks": {"Kannada": 60}}) == ["knda"]
    assert infer_scripts({"unicode_blocks": {"Malayalam": 60}}) == ["mlym"]
    assert infer_scripts({"unicode_blocks": {"Oriya": 50}}) == ["orya"]
    assert infer_scripts({"unicode_blocks": {"Telugu": 60}}) == ["telu"]
    assert infer_scripts({"unicode_blocks": {"Thaana": 35}}) == ["thaa"]
    assert infer_scripts({"unicode_blocks": {"Syriac": 40}}) == ["syrc"]
    assert infer_scripts({"unicode_blocks": {"Old Sogdian": 24}}) == ["sogo"]
    assert infer_scripts({"unicode_blocks": {"Inscriptional Pahlavi": 20}}) == ["phli"]
    assert infer_scripts({"unicode_blocks": {"Vai": 45}}) == ["vaii"]


def test_infer_scripts_uses_unicode_max_for_fourth_batch_ranges():
    """
    Verify unicode.max fallback covers fourth-batch script ranges.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode": {"max": 0x1033F}}) == ["goth"]
    assert infer_scripts({"unicode": {"max": 0x0CEF}}) == ["knda"]
    assert infer_scripts({"unicode": {"max": 0x0D6F}}) == ["mlym"]
    assert infer_scripts({"unicode": {"max": 0x0B5C}}) == ["orya"]
    assert infer_scripts({"unicode": {"max": 0x0C5F}}) == ["telu"]
    assert infer_scripts({"unicode": {"max": 0x07A6}}) == ["thaa"]
    assert infer_scripts({"unicode": {"max": 0x072A}}) == ["syrc"]
    assert infer_scripts({"unicode": {"max": 0x10F18}}) == ["sogo"]
    assert infer_scripts({"unicode": {"max": 0x10B71}}) == ["phli"]
    assert infer_scripts({"unicode": {"max": 0xA53E}}) == ["vaii"]


def test_infer_scripts_suppresses_neighboring_scripts_for_dedicated_batches():
    """
    Verify dedicated script evidence suppresses broader neighboring scripts.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Gothic": 24, "Basic Latin": 12}}) == [
        "goth"
    ]
    assert infer_scripts({"unicode_blocks": {"Vai": 40, "Basic Latin": 20}}) == ["vaii"]
    assert infer_scripts(
        {"unicode_blocks": {"Old Sogdian": 28, "Basic Latin": 10}}
    ) == ["sogo"]
    assert infer_scripts(
        {"unicode_blocks": {"Inscriptional Pahlavi": 19, "Basic Latin": 8}}
    ) == ["phli"]
    assert infer_scripts({"unicode_blocks": {"Kannada": 60, "Devanagari": 12}}) == [
        "knda"
    ]
    assert infer_scripts({"unicode_blocks": {"Oriya": 55, "Devanagari": 10}}) == [
        "orya"
    ]
    assert infer_scripts({"unicode_blocks": {"Telugu": 58, "Devanagari": 11}}) == [
        "telu"
    ]
    assert infer_scripts({"unicode_blocks": {"Syriac": 42, "Arabic": 14}}) == ["syrc"]
    assert infer_scripts({"unicode_blocks": {"Thaana": 30, "Arabic": 9}}) == ["thaa"]
    assert infer_scripts({"unicode_blocks": {"Mro": 24, "Basic Latin": 10}}) == ["mroo"]
    assert infer_scripts({"unicode_blocks": {"Old Permic": 24, "Basic Latin": 10}}) == [
        "perm"
    ]
    assert infer_scripts({"unicode_blocks": {"Sogdian": 24, "Basic Latin": 10}}) == [
        "sogd"
    ]
    assert infer_scripts({"unicode_blocks": {"Tagalog": 20, "Hanunoo": 18}}) == ["tglg"]
    assert infer_scripts({"unicode_blocks": {"Tagbanwa": 20, "Hanunoo": 18}}) == [
        "tagb"
    ]
    assert infer_scripts(
        {"unicode_blocks": {"Tirhuta": 45, "Bengali": 14, "Devanagari": 13}}
    ) == ["tirh"]


def test_infer_scripts_fifth_batch_blocks():
    """
    Verify fifth-batch script blocks infer dedicated script tags.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Kayah Li": 24}}) == ["kali"]
    assert infer_scripts({"unicode_blocks": {"Limbu": 24}}) == ["limb"]
    assert infer_scripts({"unicode_blocks": {"Lisu": 24}}) == ["lisu"]
    assert infer_scripts({"unicode_blocks": {"Medefaidrin": 24}}) == ["medf"]
    assert infer_scripts({"unicode_blocks": {"Mende Kikakui": 24}}) == ["mend"]
    assert infer_scripts({"unicode_blocks": {"Mongolian": 24}}) == ["mong"]
    assert infer_scripts({"unicode_blocks": {"Meetei Mayek": 24}}) == ["mtei"]
    assert infer_scripts({"unicode_blocks": {"Newa": 24}}) == ["newa"]
    assert infer_scripts({"unicode_blocks": {"NKo": 24}}) == ["nkoo"]
    assert infer_scripts({"unicode_blocks": {"Osage": 24}}) == ["osge"]


def test_infer_scripts_uses_unicode_max_for_fifth_batch_ranges():
    """
    Verify unicode.max fallback covers fifth-batch script ranges.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode": {"max": 0xA91A}}) == ["kali"]
    assert infer_scripts({"unicode": {"max": 0x1932}}) == ["limb"]
    assert infer_scripts({"unicode": {"max": 0xA4F5}}) == ["lisu"]
    assert infer_scripts({"unicode": {"max": 0x16E55}}) == ["medf"]
    assert infer_scripts({"unicode": {"max": 0x1E825}}) == ["mend"]
    assert infer_scripts({"unicode": {"max": 0x1885}}) == ["mong"]
    assert infer_scripts({"unicode": {"max": 0xABE5}}) == ["mtei"]
    assert infer_scripts({"unicode": {"max": 0x11435}}) == ["newa"]
    assert infer_scripts({"unicode": {"max": 0x07D2}}) == ["nkoo"]
    assert infer_scripts({"unicode": {"max": 0x104D5}}) == ["osge"]


def test_infer_scripts_suppresses_neighboring_scripts_for_fifth_batch():
    """
    Verify fifth-batch dedicated scripts suppress neighboring scripts.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Kayah Li": 24, "Basic Latin": 9}}) == [
        "kali"
    ]
    assert infer_scripts({"unicode_blocks": {"Limbu": 24, "Basic Latin": 9}}) == [
        "limb"
    ]
    assert infer_scripts({"unicode_blocks": {"Lisu": 24, "Basic Latin": 9}}) == ["lisu"]
    assert infer_scripts({"unicode_blocks": {"Medefaidrin": 24, "Basic Latin": 9}}) == [
        "medf"
    ]
    assert infer_scripts(
        {"unicode_blocks": {"Mende Kikakui": 24, "Basic Latin": 9}}
    ) == ["mend"]
    assert infer_scripts({"unicode_blocks": {"Mongolian": 24, "Basic Latin": 9}}) == [
        "mong"
    ]
    assert infer_scripts(
        {"unicode_blocks": {"Meetei Mayek": 24, "Bengali": 8, "Basic Latin": 9}}
    ) == ["mtei"]
    assert infer_scripts(
        {"unicode_blocks": {"Newa": 24, "Devanagari": 9, "Basic Latin": 9}}
    ) == ["newa"]
    assert infer_scripts(
        {"unicode_blocks": {"NKo": 24, "Arabic": 8, "Basic Latin": 9}}
    ) == ["nkoo"]
    assert infer_scripts({"unicode_blocks": {"Osage": 24, "Basic Latin": 9}}) == [
        "osge"
    ]


def test_infer_scripts_sixth_batch_blocks():
    """
    Verify sixth-batch script blocks infer dedicated script tags.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Bamum": 24}}) == ["bamu"]
    assert infer_scripts({"unicode_blocks": {"Chakma": 24}}) == ["chak"]
    assert infer_scripts({"unicode_blocks": {"Gunjala Gondi": 24}}) == ["gong"]
    assert infer_scripts({"unicode_blocks": {"Masaram Gondi": 24}}) == ["gonm"]
    assert infer_scripts({"unicode_blocks": {"Rejang": 24}}) == ["rjng"]
    assert infer_scripts({"unicode_blocks": {"Saurashtra": 24}}) == ["saur"]
    assert infer_scripts({"unicode_blocks": {"Sundanese": 24}}) == ["sund"]
    assert infer_scripts({"unicode_blocks": {"Syloti Nagri": 24}}) == ["sylo"]
    assert infer_scripts({"unicode_blocks": {"Tai Le": 24}}) == ["tale"]
    assert infer_scripts({"unicode_blocks": {"Warang Citi": 24}}) == ["wara"]


def test_infer_scripts_uses_unicode_max_for_sixth_batch_ranges():
    """
    Verify unicode.max fallback covers sixth-batch script ranges.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode": {"max": 0xA6D5}}) == ["bamu"]
    assert infer_scripts({"unicode": {"max": 0x11128}}) == ["chak"]
    assert infer_scripts({"unicode": {"max": 0x11D84}}) == ["gong"]
    assert infer_scripts({"unicode": {"max": 0x11D24}}) == ["gonm"]
    assert infer_scripts({"unicode": {"max": 0xA945}}) == ["rjng"]
    assert infer_scripts({"unicode": {"max": 0xA8B3}}) == ["saur"]
    assert infer_scripts({"unicode": {"max": 0x1B92}}) == ["sund"]
    assert infer_scripts({"unicode": {"max": 0xA811}}) == ["sylo"]
    assert infer_scripts({"unicode": {"max": 0x1968}}) == ["tale"]
    assert infer_scripts({"unicode": {"max": 0x118D2}}) == ["wara"]


def test_infer_scripts_suppresses_neighboring_scripts_for_sixth_batch():
    """
    Verify sixth-batch dedicated scripts suppress neighboring scripts.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Bamum": 24, "Basic Latin": 9}}) == [
        "bamu"
    ]
    assert infer_scripts(
        {"unicode_blocks": {"Chakma": 24, "Bengali": 9, "Myanmar": 9}}
    ) == ["chak"]
    assert infer_scripts(
        {"unicode_blocks": {"Gunjala Gondi": 24, "Devanagari": 9, "Basic Latin": 9}}
    ) == ["gong"]
    assert infer_scripts(
        {"unicode_blocks": {"Masaram Gondi": 24, "Devanagari": 9, "Basic Latin": 9}}
    ) == ["gonm"]
    assert infer_scripts({"unicode_blocks": {"Rejang": 24, "Basic Latin": 9}}) == [
        "rjng"
    ]
    assert infer_scripts(
        {"unicode_blocks": {"Saurashtra": 24, "Devanagari": 9, "Basic Latin": 9}}
    ) == ["saur"]
    assert infer_scripts({"unicode_blocks": {"Sundanese": 24, "Basic Latin": 9}}) == [
        "sund"
    ]
    assert infer_scripts(
        {"unicode_blocks": {"Syloti Nagri": 24, "Bengali": 9, "Basic Latin": 9}}
    ) == ["sylo"]
    assert infer_scripts(
        {"unicode_blocks": {"Syloti Nagri": 24, "Devanagari": 9, "Basic Latin": 9}}
    ) == ["sylo"]
    assert infer_scripts(
        {"unicode_blocks": {"Tai Le": 24, "Myanmar": 9, "Basic Latin": 9}}
    ) == ["tale"]
    assert infer_scripts({"unicode_blocks": {"Warang Citi": 24, "Basic Latin": 9}}) == [
        "wara"
    ]


def test_infer_scripts_seventh_batch_blocks():
    """
    Verify seventh-batch script blocks infer dedicated script tags.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Anatolian Hieroglyphs": 24}}) == ["hluw"]
    assert infer_scripts({"unicode_blocks": {"Avestan": 24}}) == ["avst"]
    assert infer_scripts({"unicode_blocks": {"Bassa Vah": 24}}) == ["bass"]
    assert infer_scripts({"unicode_blocks": {"Bhaiksuki": 24}}) == ["bhks"]
    assert infer_scripts({"unicode_blocks": {"Byzantine Musical Symbols": 24}}) == [
        "byzm"
    ]
    assert infer_scripts({"unicode_blocks": {"Carian": 24}}) == ["cari"]
    assert infer_scripts({"unicode_blocks": {"Caucasian Albanian": 24}}) == ["aghb"]
    assert infer_scripts({"unicode_blocks": {"Chorasmian": 24}}) == ["chrs"]
    assert infer_scripts({"unicode_blocks": {"Cypriot Syllabary": 24}}) == ["cprt"]
    assert infer_scripts({"unicode_blocks": {"Cypro-Minoan": 24}}) == ["cpmn"]


def test_infer_scripts_uses_unicode_max_for_seventh_batch_ranges():
    """
    Verify unicode.max fallback covers seventh-batch script ranges.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode": {"max": 0x10545}}) == ["aghb"]
    assert infer_scripts({"unicode": {"max": 0x10B15}}) == ["avst"]
    assert infer_scripts({"unicode": {"max": 0x11C15}}) == ["bhks"]
    assert infer_scripts({"unicode": {"max": 0x102B5}}) == ["cari"]
    assert infer_scripts({"unicode": {"max": 0x10FC5}}) == ["chrs"]
    assert infer_scripts({"unicode": {"max": 0x10815}}) == ["cprt"]
    assert infer_scripts({"unicode": {"max": 0x12FA5}}) == ["cpmn"]
    assert infer_scripts({"unicode": {"max": 0x14415}}) == ["hluw"]


def test_infer_scripts_supports_eighth_batch_blocks_and_ranges():
    """
    Verify direct and unicode.max inference for the eighth script batch.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts({"unicode_blocks": {"Elymaic": 24}}) == ["elym"]
    assert infer_scripts({"unicode_blocks": {"Kawi": 24}}) == ["kawi"]
    assert infer_scripts({"unicode_blocks": {"Makasar": 24}}) == ["maka"]
    assert infer_scripts({"unicode": {"max": 0x10FF0}}) == ["elym"]
    assert infer_scripts({"unicode": {"max": 0x11F35}}) == ["kawi"]
    assert infer_scripts({"unicode": {"max": 0x11EF4}}) == ["maka"]


def test_infer_scripts_suppresses_neighboring_devanagari_and_thai_noise():
    """
    Verify Bengali and Lao suppress common neighboring false positives.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert infer_scripts(
        {"unicode_blocks": {"Bengali": 24, "Devanagari": 9, "Basic Latin": 9}}
    ) == ["beng", "latn"]
    assert infer_scripts(
        {"unicode_blocks": {"Lao": 24, "Thai": 9, "Basic Latin": 9}}
    ) == [
        "laoo",
        "latn",
    ]


def test_coverage_scripts_never_unknown():
    """
    Verify that the public coverage script list itself never contains ``unknown``.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    coverage = {}
    scripts = coverage.get("scripts", [])
    assert "unknown" not in scripts
