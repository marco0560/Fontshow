"""
Exercise metadata processing edge cases.

Responsibilities
----------------
- Cover language warning emission and inference-derived coverage copies.
- Verify debug inference dumping and charset failure handling.
"""

from __future__ import annotations

from fontshow.core.types import Severity
from fontshow.inventory import metadata_processing as mp


def test_process_language_metadata_emits_all_warning_kinds(monkeypatch):
    """
    Ensure deprecated, normalized, duplicate, and dropped warnings are attached.
    """
    font = {"inference": {"languages": ["en"], "scripts": ["latn"]}}
    coverage: dict[str, object] = {}

    monkeypatch.setattr(
        mp,
        "normalize_languages",
        lambda raw, strict_bcp47: {
            "normalized": ["en"],
            "deprecated": [{"from_": "iw", "raw": "iw", "to": "he"}],
            "dropped": [
                {"raw": "en-US", "reason": "variant_stripped"},
                {"raw": "en", "reason": "duplicate_normalized", "normalized": "en"},
                {"raw": "zzz", "reason": "invalid"},
            ],
        },
    )

    mp._process_language_metadata(font, coverage, strict_bcp47=False)

    assert coverage["languages"] == ["en"]
    assert coverage["scripts"] == ["latn"]
    assert coverage["languages_raw"] == ["en"]
    assert [w["code"] for w in font["warnings"]] == [
        "language_deprecated",
        "language_normalized",
        "language_duplicate",
        "language_dropped",
    ]
    assert font["warnings"][-1]["severity"] is Severity.WARN


def test_debug_dump_inference_respects_env_and_handles_missing_profiles(
    monkeypatch,
):
    """
    Ensure debug dumping is gated by env and tolerates missing script profiles.
    """
    messages: list[str] = []
    monkeypatch.setenv("FONTSHOW_DEBUG_INFERENCE", "1")
    monkeypatch.setattr(mp, "log_info", messages.append)
    monkeypatch.setattr(mp, "LANGUAGE_INFO", {"en": {"scripts": ["LATN"]}, "zz": {}})

    mp._debug_dump_inference(
        {
            "family": "Alpha",
            "subfamily": "Regular",
            "inference": {"scripts": ["LATN"]},
        },
        {"unicode_blocks": {"Basic Latin": 10}},
        {
            "en": {"confidence": "high", "evidence": ["x"]},
            "zz": {"confidence": "medium", "evidence": []},
        },
        ["en", "zz"],
    )

    assert any("Font inference diagnostics" in message for message in messages)
    assert any("primary_script=LATN" in message for message in messages)
    assert any("primary_script=None" in message for message in messages)


def test_process_charset_emits_warning_on_decode_failure(monkeypatch):
    """
    Ensure charset decode failures attach structured warnings and stop cleanly.
    """
    font = {"charset": {"raw": "bad-bitmap"}}
    coverage: dict[str, object] = {}

    monkeypatch.setattr(
        mp,
        "decode_fc_charset_bitmap",
        lambda raw: (_ for _ in ()).throw(ValueError("broken bitmap")),
    )

    mp._process_charset(font, coverage, "/tmp/font.ttf")

    assert font["charset"]["ranges"] == []
    assert coverage == {}
    assert font["warnings"] == [
        {
            "code": "charset_decode_failed",
            "message": "Fontconfig charset bitmap decoding failed",
            "severity": Severity.WARN,
            "source": "fontconfig_charset",
            "extra": {
                "font_path": "/tmp/font.ttf",
                "error_type": "ValueError",
                "error_reason": "broken bitmap",
            },
        }
    ]
