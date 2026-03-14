"""
Exercise specimen selection fallbacks.

Responsibilities
----------------
- Cover direct language selection, script fallback, and no-match cases.
- Ensure malformed ontology entries are ignored rather than breaking.
"""

from fontshow.common import specimens


def test_choose_language_sample_prefers_first_language_with_sample(monkeypatch):
    """
    Ensure selection skips unusable language entries and returns the first valid sample.
    """
    monkeypatch.setattr(
        specimens,
        "LANGUAGE_INFO",
        {
            "bad": {"sample": ""},
            "en": {"sample": "Hello"},
            "fr": {"sample": "Bonjour"},
        },
    )

    assert specimens.choose_language_sample(["bad", "en", "fr"]) == "Hello"


def test_choose_language_sample_falls_back_via_script_display_language(monkeypatch):
    """
    Ensure the first script tag can resolve a representative fallback sample.
    """
    monkeypatch.setattr(specimens, "tag_to_iso", lambda tag: "LATN")
    monkeypatch.setattr(specimens, "SCRIPT_INFO", {"LATN": {"display_language": "en"}})
    monkeypatch.setattr(specimens, "LANGUAGE_INFO", {"en": {"sample": "Hello"}})

    assert specimens.choose_language_sample(None, ["latn"]) == "Hello"


def test_choose_language_sample_returns_none_for_unknown_or_malformed_entries(
    monkeypatch,
):
    """
    Ensure malformed ontology rows are ignored cleanly.
    """
    monkeypatch.setattr(specimens, "tag_to_iso", lambda tag: "ARAB")
    monkeypatch.setattr(specimens, "SCRIPT_INFO", {"ARAB": {"display_language": 7}})
    monkeypatch.setattr(specimens, "LANGUAGE_INFO", {"en": "invalid"})

    assert specimens.choose_language_sample(["en"], ["arab"]) is None
