"""
Exercise inventory warning aggregation edges.
"""

from __future__ import annotations

from fontshow.core.types import Severity
from fontshow.diagnostics import inventory_warnings as iw


def test_collect_language_warnings_groups_and_filters_payloads():
    """
    Ensure grouping handles missing extras and filters info-only non-language warnings.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    font = {
        "warnings": [
            {
                "code": "language_normalized",
                "message": "Normalized language 'en-US' -> 'en'",
                "severity": Severity.INFO,
                "extra": {},
            },
            {
                "code": "language_duplicate",
                "message": "Duplicate language 'fr'",
                "severity": Severity.INFO,
            },
            {
                "code": "language_dropped",
                "message": "Dropped language 'zzz'",
                "severity": Severity.WARN,
                "extra": {"raw": "zzz"},
            },
            {"code": "other_info", "message": "ignore me", "severity": Severity.INFO},
            {"code": "other_warn", "message": "keep me", "severity": Severity.WARN},
        ]
    }

    norm, dups, dropped, other = iw._collect_language_warnings(font)

    assert norm == ["en-US"]
    assert dups == ["fr"]
    assert dropped == ["zzz"]
    assert other == [("warn", "other_warn", "keep me")]


def test_emit_verbose_warnings_handles_non_list_fonts_and_deduplicates(monkeypatch):
    """
    Ensure verbose emission tolerates malformed inventory roots and deduplicates entries.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to capture info and warning log messages.

    Returns
    -------
    None
    """
    infos: list[str] = []
    warns: list[str] = []
    monkeypatch.setattr(iw, "log_info", infos.append)
    monkeypatch.setattr(iw, "log_warn", warns.append)

    iw._emit_verbose_warnings({"fonts": "bad"})
    assert infos == []
    assert warns == []

    iw._emit_verbose_warnings(
        {
            "fonts": [
                {
                    "path": "/tmp/font.ttf",
                    "family": "Alpha",
                    "warnings": [
                        {
                            "code": "language_duplicate",
                            "message": "Duplicate language 'fr'",
                            "severity": Severity.INFO,
                        },
                        {
                            "code": "language_duplicate",
                            "message": "Duplicate language 'fr'",
                            "severity": Severity.INFO,
                        },
                        {
                            "code": "other_warn",
                            "message": "warn",
                            "severity": Severity.WARN,
                        },
                    ],
                }
            ]
        }
    )

    assert any("duplicate_languages: fr" in message for message in infos)
    assert any("other_warn: warn" in message for message in warns)
