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

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace language normalization.

    Returns
    -------
    None
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

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace environment variables, logging, and language data.

    Returns
    -------
    None
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

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace charset decoding.

    Returns
    -------
    None
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


def test_process_charset_emits_warning_on_block_mismatch() -> None:
    """
    Ensure charset/canonical block mismatches emit structured diagnostics.

    Returns
    -------
    None
    """
    font: dict[str, object] = {"charset": {"ranges": [[0x0020, 0x007E]]}}
    coverage: dict[str, object] = {
        "unicode_blocks": {
            "Basic Latin": 94,
            "Latin-1 Supplement": 10,
        }
    }

    mp._process_charset(font, coverage, "/tmp/font.ttf")

    warning = font["warnings"][0]
    assert warning["code"] == "charset_block_mismatch"
    assert warning["severity"] is Severity.WARN
    assert warning["extra"]["canonical_only_blocks"] == ["Latin-1 Supplement"]
    assert warning["extra"]["charset_only_blocks"] == []
    assert warning["extra"]["differing_counts"] == [
        {
            "block": "Basic Latin",
            "canonical_count": 94,
            "charset_count": 95,
        }
    ]


def test_infer_and_attach_metadata_emits_charset_script_mismatch(
    monkeypatch,
) -> None:
    """
    Ensure script mismatch diagnostics preserve canonical precedence.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace downstream language inference.

    Returns
    -------
    None
    """
    font: dict[str, object] = {"warnings": []}
    coverage: dict[str, object] = {
        "unicode_blocks": {"Arabic": 40},
        "script_coverage_from_charset": {"HEBR": 1.0, "ARAB": 0.1},
        "languages": [],
        "scripts": [],
    }

    monkeypatch.setattr(mp, "infer_languages", lambda *args, **kwargs: {})

    mp._infer_and_attach_metadata(
        font,
        coverage,
        level="medium",
        font_path="/tmp/font.ttf",
    )

    assert font["warnings"][-1] == {
        "code": "charset_script_mismatch",
        "message": (
            "Charset-derived primary script differs from canonical inferred script"
        ),
        "severity": Severity.INFO,
        "source": "fontconfig_charset",
        "extra": {
            "font_path": "/tmp/font.ttf",
            "canonical_primary_script": "ARAB",
            "charset_primary_script": "HEBR",
        },
    }
    assert font["inference"]["scripts"][0] == "ARAB"
