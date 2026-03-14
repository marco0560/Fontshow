"""
Exercise catalog pipeline helper branches.

Responsibilities
----------------
- Cover test-font configuration and listing behavior.
- Verify inventory diagnostics severity thresholds.
- Cover filtering, slicing, sorting, and type-error propagation.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from fontshow.catalog import pipeline


def test_configure_test_fonts_extends_defaults(monkeypatch):
    """
    Ensure explicit CLI fonts are unioned with default test fonts.
    """
    monkeypatch.setattr(pipeline, "DEFAULT_TEST_FONTS", {"Default", "Shared"})

    configured = pipeline._configure_test_fonts(
        SimpleNamespace(test_font=["CLI", "Shared"])
    )

    assert configured == {"Default", "Shared", "CLI"}


def test_handle_list_test_fonts_reports_matches_and_missing(monkeypatch):
    """
    Ensure matching uses trimmed inventory family names and reports missing entries.
    """
    messages: list[str] = []
    monkeypatch.setattr(pipeline, "log_info", messages.append)

    rc = pipeline._handle_list_test_fonts(
        {"Bravo", "Alpha"},
        [{"family": " Alpha "}, {"family": "Gamma"}, "ignored"],
    )

    assert rc == 0
    assert messages == [
        "TEST_FONTS configuration:",
        "  - Alpha",
        "  - Bravo",
        "Inventory fonts matching TEST_FONTS (exact):",
        "  - Alpha",
        "Missing TEST_FONTS (not present in inventory):",
        "  - Bravo",
    ]


@pytest.mark.parametrize(
    ("fonts", "expected_log", "expected_message"),
    [
        (
            [{"coverage": {"languages": []}}] * 11
            + [{"coverage": {"languages": ["en"]}}] * 189,
            "info",
            "11 fonts have no declared language coverage (6%)",
        ),
        (
            [{"coverage": {"languages": []}}] * 2
            + [{"coverage": {"languages": ["en"]}}] * 3,
            "warn",
            "2 fonts have no declared language coverage (40%)",
        ),
        (
            [{"coverage": {"languages": []}}],
            "warn",
            "1 fonts have no declared language coverage (100%) — catalog usefulness may be severely degraded",
        ),
    ],
)
def test_run_inventory_diagnostics_uses_ratio_thresholds(
    monkeypatch, fonts, expected_log, expected_message
):
    """
    Ensure missing-language ratios map to the intended severity buckets.
    """
    infos: list[str] = []
    warnings: list[str] = []
    monkeypatch.setattr(pipeline, "log_info", infos.append)
    monkeypatch.setattr(pipeline, "log_warn", warnings.append)

    pipeline._run_inventory_diagnostics(fonts + ["ignored"])

    assert infos == ([expected_message] if expected_log == "info" else [])
    assert warnings == ([expected_message] if expected_log == "warn" else [])


def test_filter_and_prepare_fonts_filters_sorts_and_slices(monkeypatch):
    """
    Ensure filtering happens before slicing and final output is family-grouped.
    """
    trace_calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        pipeline,
        "log_trace_cat",
        lambda _log, _cat, msg, extra: trace_calls.append((msg, extra)),
    )
    monkeypatch.setattr(pipeline, "as_font_desc_list", lambda fonts: list(fonts))
    monkeypatch.setattr(
        pipeline,
        "group_fonts_by_family",
        lambda fonts: [{"family": font["family"]} for font in fonts],
    )

    fonts = [
        {"family": "Zulu"},
        {"family": "Alpha"},
        {"family": "Beta"},
    ]

    result = pipeline._filter_and_prepare_fonts(
        fonts,
        SimpleNamespace(number=-1),
        {"Alpha", "Beta"},
    )

    assert result == [{"family": "Beta"}]
    assert trace_calls == [
        ("font filtering started", {"input_fonts": 3}),
        ("font filtering completed", {"output_fonts": 1}),
    ]


def test_filter_and_prepare_fonts_propagates_type_errors(monkeypatch):
    """
    Ensure invalid entries still surface the normalization TypeError.
    """
    monkeypatch.setattr(
        pipeline,
        "log_trace_cat",
        lambda _log, _cat, _msg, extra: None,
    )

    with pytest.raises(TypeError, match="Unexpected font entry type"):
        pipeline._filter_and_prepare_fonts(
            [{"family": "Alpha"}, object()],
            SimpleNamespace(number=None),
            {"Alpha"},
        )
