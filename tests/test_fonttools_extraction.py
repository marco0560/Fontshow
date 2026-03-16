"""
Exercise fontTools extraction helper branches.

Responsibilities
----------------
- Cover container detection and sample-text extraction edge cases.
- Verify best-effort extraction helpers wrap malformed table data.
- Cover cache, TTC, and fallback paths in the top-level extractor.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from fontshow.inventory import fonttools_extraction as extraction


class _FakeNameRecord:
    """
    Minimal ``name`` table record stand-in for extraction tests.

    Notes
    -----
    Instances can return Unicode text, fall back to ``str()``, or raise.
    """

    def __init__(
        self,
        name_id: int,
        text: str | None = None,
        *,
        exc: Exception | None = None,
        str_value: str | None = None,
    ) -> None:
        """
        Initialize the fake name record.

        Parameters
        ----------
        name_id : int
            Name ID exposed by the fake record.
        text : str | None, optional
            Unicode text returned by ``toUnicode`` when no exception is configured.
        exc : Exception | None, optional
            Exception raised by ``toUnicode`` when configured.
        str_value : str | None, optional
            String fallback returned by ``__str__``.

        Returns
        -------
        None
        """
        self.nameID = name_id
        self._text = text
        self._exc = exc
        self._str_value = str_value if str_value is not None else text or ""

    def toUnicode(self) -> str:
        """
        Return the configured Unicode string or raise the configured error.

        Returns
        -------
        str
            Stored Unicode string when no exception is configured.

        Raises
        ------
        Exception
            Re-raises the configured exception when present.
        """
        if self._exc is not None:
            raise self._exc
        return self._text or ""

    def __str__(self) -> str:
        return self._str_value


class _FakeUnicodeSubtable:
    def __init__(self, codepoints: list[int], *, unicode: bool = True) -> None:
        self.cmap = {cp: f"g{cp}" for cp in codepoints}
        self._unicode = unicode

    def isUnicode(self) -> bool:
        return self._unicode


class _FakeTT(dict):
    def keys(self):
        return super().keys()


def test_detect_font_container_prefers_header_bytes(tmp_path):
    """
    Ensure container detection handles magic bytes and extension fallbacks.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage fake font files.

    Returns
    -------
    None

    Raises
    ------
    extraction.TTLibError
        Raised by the nested fake font opener and converted into error payloads.
    """
    cases = [
        ("font.woff", b"wOFF", "WOFF"),
        ("font.woff2", b"wOF2", "WOFF2"),
        ("font.otf", b"OTTO", "OTF"),
        ("font.ttf", b"\x00\x01\x00\x00", "TTF"),
        ("font.ttc", b"ttcf", "TTC"),
        ("font.unknown", b"????", "UNKNOWN"),
    ]

    for name, header, expected in cases:
        path = tmp_path / name
        path.write_bytes(header + b"rest")
        assert extraction.detect_font_container(path) == expected


def test_extract_sample_text_filters_duplicates_and_decode_failures(monkeypatch):
    """
    Ensure sample-text extraction deduplicates values and ignores bad records.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace ``TTFont`` with a deterministic fake.

    Returns
    -------
    None
    """

    class FakeTTFont(dict):
        def __init__(self, _path, lazy=True) -> None:
            """
            Build a fake font containing duplicate and malformed sample-text records.

            Parameters
            ----------
            _path : str
                Font path accepted for interface compatibility.
            lazy : bool, optional
                Lazy-loading flag accepted for interface compatibility.

            Returns
            -------
            None
            """
            super().__init__(
                name=SimpleNamespace(
                    names=[
                        _FakeNameRecord(extraction.NAME_ID_SAMPLE_TEXT, " Alpha "),
                        _FakeNameRecord(extraction.NAME_ID_SAMPLE_TEXT, "Alpha"),
                        _FakeNameRecord(
                            extraction.NAME_ID_SAMPLE_TEXT,
                            exc=UnicodeError("boom"),
                        ),
                        _FakeNameRecord(999, "ignored"),
                    ]
                )
            )
            self.closed = False

        def close(self) -> None:
            """
            Mark the fake font as closed.

            Returns
            -------
            None
            """
            self.closed = True

    monkeypatch.setattr(extraction, "TTFont", FakeTTFont)

    assert extraction.extract_sample_text("/tmp/font.ttf") == ["Alpha"]


def test_extract_name_table_falls_back_to_str_and_skips_unusable_records():
    """
    Ensure malformed name records use ``str()`` fallback when possible.

    Returns
    -------
    None
    """
    tt = _FakeTT(
        name=SimpleNamespace(
            names=[
                _FakeNameRecord(1, "Alpha"),
                _FakeNameRecord(1, exc=ValueError("bad"), str_value="Alt Alpha"),
                _FakeNameRecord(1, exc=TypeError("bad"), str_value=""),
                _FakeNameRecord(2, "Regular"),
            ]
        )
    )

    assert extraction._extract_name_table(tt) == {
        "1": ["Alpha", "Alt Alpha"],
        "2": ["Regular"],
    }


def test_extract_os2_unicode_coverage_and_features_are_best_effort():
    """
    Ensure low-level helpers normalize values and tolerate malformed subtables.

    Returns
    -------
    None
    """
    tt = _FakeTT(
        **{
            "OS/2": SimpleNamespace(
                usWeightClass=400,
                usWidthClass=5,
                fsType=0,
                achVendID=b"ABCD",
                version=4,
            ),
            "cmap": SimpleNamespace(
                tables=[
                    _FakeUnicodeSubtable([0x41, 0x42]),
                    SimpleNamespace(cmap={"bad": "glyph"}),
                ]
            ),
            "GSUB": SimpleNamespace(
                table=SimpleNamespace(
                    FeatureList=SimpleNamespace(
                        FeatureRecord=[
                            SimpleNamespace(FeatureTag="liga"),
                            SimpleNamespace(FeatureTag="kern"),
                        ]
                    )
                )
            ),
            "GPOS": SimpleNamespace(table=SimpleNamespace(FeatureList=None)),
        }
    )

    assert extraction._extract_os2_table(tt) == {
        "weight_class": 400,
        "width_class": 5,
        "embedding_rights": 0,
        "vendor_id": "ABCD",
        "version": 4,
    }
    assert extraction._extract_unicode_coverage(tt) == {
        "count": 2,
        "min": 65,
        "max": 66,
    }
    assert extraction._extract_opentype_features(tt) == ["kern", "liga"]


def test_fonttools_extract_from_tt_wraps_helper_failures(monkeypatch):
    """
    Ensure face extraction converts helper failures into stable error payloads.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace low-level extraction helpers.

    Returns
    -------
    None
    """
    cmap = SimpleNamespace(
        tables=[
            _FakeUnicodeSubtable([0x41, 0x42, 0x43]),
            SimpleNamespace(isUnicode=lambda: False, cmap={0x44: "ignored"}),
        ]
    )
    tt = _FakeTT(
        cmap=cmap,
        head=SimpleNamespace(unitsPerEm=1000),
        hhea=SimpleNamespace(ascent=800, descent=-200),
        post=SimpleNamespace(italicAngle=12, isFixedPitch=1),
        maxp=SimpleNamespace(numGlyphs=7),
        glyf=object(),
        fvar=object(),
    )

    monkeypatch.setattr(
        extraction,
        "_extract_name_table",
        lambda _tt: (_ for _ in ()).throw(ValueError("bad names")),
    )
    monkeypatch.setattr(
        extraction,
        "_extract_os2_table",
        lambda _tt: (_ for _ in ()).throw(TypeError("bad os2")),
    )
    monkeypatch.setattr(
        extraction,
        "_extract_unicode_coverage",
        lambda _tt: (_ for _ in ()).throw(ValueError("bad unicode")),
    )
    monkeypatch.setattr(
        extraction,
        "_detect_color_tables",
        lambda _tt: (_ for _ in ()).throw(AttributeError("bad color")),
    )
    monkeypatch.setattr(
        extraction,
        "_extract_opentype_features",
        lambda _tt: (_ for _ in ()).throw(TypeError("bad features")),
    )

    data = extraction._fonttools_extract_from_tt(
        _path=SimpleNamespace(),
        container="TTF",
        tt=tt,
        ttc_index=None,
    )

    assert data["ok"] is True
    assert data["font_type"] == "TrueType"
    assert data["names"] == {"error": "name: bad names"}
    assert data["os2"] == {"error": "OS/2: bad os2"}
    assert data["unicode"] == {"error": "unicode: bad unicode"}
    assert data["unicode_blocks"]
    assert data["variable"] == {"fvar": True, "STAT": False}
    assert data["color_tables"] == []
    assert data["opentype_features"] == []
    assert data["units_per_em"] == 1000
    assert data["ascent"] == 800
    assert data["descent"] == -200
    assert data["italic_angle"] == 12.0
    assert data["is_fixed_pitch"] is True
    assert data["glyph_count"] == 7


def test_fonttools_extract_all_handles_cache_and_open_failures(tmp_path, monkeypatch):
    """
    Ensure single-face extraction reuses cache and reports open failures deterministically.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage cache and font files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace cache, logging, and font opening helpers.

    Returns
    -------
    None

    Raises
    ------
    extraction.TTLibError
        Raised by the nested fake font opener and converted into error payloads.
    """
    font_path = tmp_path / "font.ttf"
    font_path.write_bytes(b"\x00\x01\x00\x00")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    key = extraction.font_cache_key(font_path, None)
    cache_file = cache_dir / f"{key}.json"
    cache_file.write_text(json.dumps({"ok": True, "cached": True}), encoding="utf-8")

    monkeypatch.setattr(extraction, "log_trace_cat", lambda *_args, **_kwargs: None)

    assert extraction.fonttools_extract_all(font_path, cache_dir, use_cache=True) == [
        {"ok": True, "cached": True}
    ]

    cache_file.write_text("{", encoding="utf-8")

    class BrokenTTFont:
        def __init__(self, *_args, **_kwargs) -> None:
            """
            Raise a deterministic font-open failure.

            Parameters
            ----------
            *_args : object
                Ignored positional arguments preserved for interface compatibility.
            **_kwargs : object
                Ignored keyword arguments preserved for interface compatibility.

            Returns
            -------
            None

            Raises
            ------
            extraction.TTLibError
                Always raised with a fixed message.
            """
            msg = "cannot open"
            raise extraction.TTLibError(msg)

    monkeypatch.setattr(extraction, "TTFont", BrokenTTFont)

    result = extraction.fonttools_extract_all(font_path, cache_dir, use_cache=True)

    assert result == [
        {
            "ok": False,
            "container": "TTF",
            "ttc_index": None,
            "error": "Cannot open font: cannot open",
        }
    ]
    assert json.loads(cache_file.read_text(encoding="utf-8"))["ok"] is False


def test_fonttools_extract_all_ttc_uses_cached_faces_and_reports_per_face_failures(
    tmp_path, monkeypatch
):
    """
    Ensure TTC extraction mixes cached and freshly extracted faces deterministically.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage cache and TTC files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace TTC loading, extraction, and tracing helpers.

    Returns
    -------
    None

    Raises
    ------
    extraction.TTLibError
        Raised by the nested face extractor and converted into per-face errors.
    """
    font_path = tmp_path / "font.ttc"
    font_path.write_bytes(b"ttcfrest")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    key0 = extraction.font_cache_key(font_path, 0)
    (cache_dir / f"{key0}.json").write_text(
        json.dumps({"ok": True, "cached": 0}), encoding="utf-8"
    )

    class Face0:
        pass

    class Face1:
        pass

    class FakeCollection:
        def __init__(self, _path) -> None:
            self.fonts = [Face0(), Face1()]

    monkeypatch.setattr(extraction, "TTCollection", FakeCollection)
    monkeypatch.setattr(extraction, "log_trace_cat", lambda *_args, **_kwargs: None)

    def fake_extract(*, _path, container, tt, ttc_index):
        """
        Return a face payload or raise for the failing TTC face.

        Parameters
        ----------
        _path : pathlib.Path
            Font path accepted for interface compatibility.
        container : str
            Container label accepted for interface compatibility.
        tt : object
            Face object accepted for interface compatibility.
        ttc_index : int | None
            TTC face index being extracted.

        Returns
        -------
        dict[str, object]
            Extracted payload for successful TTC faces.

        Raises
        ------
        extraction.TTLibError
            Raised for the sentinel failing face.
        """
        if ttc_index == 1:
            msg = "face boom"
            raise extraction.TTLibError(msg)
        return {"ok": True, "container": container, "ttc_index": ttc_index}

    monkeypatch.setattr(extraction, "_fonttools_extract_from_tt", fake_extract)

    result = extraction.fonttools_extract_all(font_path, cache_dir, use_cache=True)

    assert result == [
        {"ok": True, "cached": 0, "container": "TTC", "ttc_index": 0, "ttc_count": 2},
        {
            "ok": False,
            "container": "TTC",
            "ttc_index": 1,
            "ttc_count": 2,
            "error": "TTC face extract failed: face boom",
        },
    ]


def test_extract_opentype_features_ignores_malformed_feature_records():
    """
    Ensure malformed feature records are ignored instead of raising.

    Returns
    -------
    None
    """
    tt = _FakeTT(
        GSUB=SimpleNamespace(
            table=SimpleNamespace(FeatureList=SimpleNamespace(FeatureRecord=[object()]))
        )
    )

    assert extraction._extract_opentype_features(tt) == []


def test_fonttools_extract_all_propagates_cache_write_failures(tmp_path, monkeypatch):
    """
    Ensure cache write failures are not silently swallowed.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage cache and font files.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace extraction, font opening, and cache writing helpers.

    Returns
    -------
    None

    Raises
    ------
    PermissionError
        Raised by the cache write path under test.
    """
    font_path = tmp_path / "font.ttf"
    font_path.write_bytes(b"\x00\x01\x00\x00")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    monkeypatch.setattr(extraction, "log_trace_cat", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        extraction,
        "_fonttools_extract_from_tt",
        lambda **_kwargs: {"ok": True, "container": "TTF", "ttc_index": None},
    )

    class DummyTTFont:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

    monkeypatch.setattr(extraction, "TTFont", DummyTTFont)
    from pathlib import Path

    monkeypatch.setattr(
        Path,
        "write_text",
        lambda self, *args, **kwargs: (_ for _ in ()).throw(PermissionError("denied")),
    )

    with pytest.raises(PermissionError, match="denied"):
        extraction.fonttools_extract_all(font_path, cache_dir, use_cache=False)
