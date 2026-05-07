"""
LaTeX rendering policy helpers.

This module contains helpers that determine how fonts, scripts, and
languages should be represented when generating LaTeX catalog output.

Responsibilities
----------------
- Determine script display labels used in catalog entries.
- Compute rendering policies for fonts based on script and language
  metadata.
- Collect secondary language declarations required by Polyglossia.

Design principles
-----------------
These functions implement policy decisions about how font metadata is
mapped to LaTeX constructs, but they do not perform document generation
or string escaping. Low-level LaTeX-safe text handling lives in
``latex.render``.

Architectural role
------------------
This module belongs to the LaTeX subsystem and acts as a bridge between
inventory metadata and the LaTeX rendering layer used by the catalog
generation pipeline.
"""

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fontshow.constants.runtime import SUBPROCESS_TIMEOUT_SECONDS
from fontshow.core.types import CatalogFontEntryV12, ScriptISO
from fontshow.latex.render import _latex_detokenize_safe, _renderer_option_prefix
from fontshow.ontology.language_tables import LANGUAGE_INFO, SCRIPT_INFO


@dataclass(frozen=True)
class _FontspecScriptRegistry:
    """
    Installed ``fontspec`` script names indexed by name and OpenType tag.

    Parameters
    ----------
    names : frozenset[str]
        Script option names accepted by the installed ``fontspec`` file.
    names_by_tag : dict[str, str]
        Accepted script names keyed by normalized OpenType script tag.
    """

    names: frozenset[str]
    names_by_tag: dict[str, str]


def get_render_policy_version() -> str:
    """
    Return a deterministic version fingerprint for render-policy inputs.

    Parameters
    ----------
    None

    Returns
    -------
    str
        Stable SHA-256-based fingerprint derived from the ontology
        fields that influence LaTeX render policy.

    Notes
    -----
    The fingerprint is derived from ``SCRIPT_INFO`` entries relevant to
    render-policy decisions so inventories can record which policy set
    was active when validation metadata was collected.
    """
    policy_snapshot = {
        str(script_iso): {
            "fontspec_opts": _fontspec_compatible_script_opts(
                script_iso,
                str(info.get("fontspec_opts", "")),
            ),
            "polyglossia_language": info.get("polyglossia_language", ""),
            "requires_polyglossia": bool(info.get("requires_polyglossia", False)),
        }
        for script_iso, info in sorted(
            SCRIPT_INFO.items(), key=lambda item: str(item[0])
        )
    }
    encoded = json.dumps(
        policy_snapshot,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _normalize_fontspec_token(value: str) -> str:
    """
    Normalize a ``fontspec`` script name or tag for matching.

    Parameters
    ----------
    value : str
        Raw script name or OpenType script tag.

    Returns
    -------
    str
        Lowercase alphanumeric token.
    """
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _format_fontspec_script_option(script_name: str) -> str:
    """
    Format an accepted ``fontspec`` script name as an option string.

    Parameters
    ----------
    script_name : str
        Human-readable script name accepted by ``fontspec``.

    Returns
    -------
    str
        ``Script=...`` option with braces when the name contains
        non-letter characters.
    """
    if script_name.replace("-", "").isalpha():
        return f"Script={script_name}"
    return f"Script={{{script_name}}}"


def _extract_fontspec_script_name(fontspec_opts: str) -> str | None:
    """
    Extract the ``Script=`` value from a fontspec option string.

    Parameters
    ----------
    fontspec_opts : str
        Comma-separated fontspec options.

    Returns
    -------
    str | None
        Script option value without braces, or ``None`` when absent.
    """
    for part in fontspec_opts.split(","):
        stripped = part.strip()
        if not stripped.startswith("Script="):
            continue
        value = stripped.removeprefix("Script=").strip()
        if value.startswith("{") and value.endswith("}") and len(value) >= 2:
            value = value[1:-1].strip()
        return value or None
    return None


def _parse_fontspec_script_registry(text: str) -> _FontspecScriptRegistry:
    r"""
    Parse installed ``\newfontscript`` declarations.

    Parameters
    ----------
    text : str
        Contents of ``fontspec-luatex.sty`` or equivalent generated
        ``fontspec`` source.

    Returns
    -------
    _FontspecScriptRegistry
        Accepted script names and normalized OpenType tag mappings.
    """
    names: set[str] = set()
    names_by_tag: dict[str, str] = {}
    pattern = re.compile(r"\\newfontscript\{([^{}]+)\}\{([^{}]+)\}")
    for match in pattern.finditer(text):
        raw_name, raw_tags = match.groups()
        script_name = raw_name.replace("~", " ").strip()
        if not script_name:
            continue
        names.add(script_name)
        for raw_tag in raw_tags.split(","):
            tag_key = _normalize_fontspec_token(raw_tag.replace("~", ""))
            if tag_key and tag_key not in names_by_tag:
                names_by_tag[tag_key] = script_name
    return _FontspecScriptRegistry(
        names=frozenset(names),
        names_by_tag=names_by_tag,
    )


def _read_installed_fontspec_luatex() -> str | None:
    """
    Read the installed ``fontspec-luatex.sty`` source when available.

    Parameters
    ----------
    None

    Returns
    -------
    str | None
        File contents when ``kpsewhich`` locates the package, otherwise
        ``None``.
    """
    kpsewhich_bin = shutil.which("kpsewhich")
    if kpsewhich_bin is None:
        return None
    try:
        proc = subprocess.run(
            [kpsewhich_bin, "fontspec-luatex.sty"],
            check=False,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    resolved = proc.stdout.strip().splitlines()
    if not resolved:
        return None
    path = Path(resolved[0].strip())
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


@lru_cache(maxsize=1)
def _installed_fontspec_script_registry() -> _FontspecScriptRegistry | None:
    """
    Return the installed ``fontspec`` script registry.

    Parameters
    ----------
    None

    Returns
    -------
    _FontspecScriptRegistry | None
        Parsed registry when the local TeX installation exposes one,
        otherwise ``None``.
    """
    text = _read_installed_fontspec_luatex()
    if text is None:
        return None
    registry = _parse_fontspec_script_registry(text)
    if not registry.names:
        return None
    return registry


def _fontspec_compatible_script_opts(script_iso: ScriptISO, opts: str) -> str:
    """
    Normalize ``Script=`` options against the installed ``fontspec`` table.

    Parameters
    ----------
    script_iso : ScriptISO
        Canonical script code whose OpenType tag may identify the
        installed ``fontspec`` spelling.
    opts : str
        Ontology-provided fontspec option string.

    Returns
    -------
    str
        Compatible option string. When the installed table is
        unavailable, the original options are returned. When the table
        is available and the script is unsupported, ``Script=`` is
        suppressed.
    """
    if not opts:
        return ""
    script_name = _extract_fontspec_script_name(opts)
    if script_name is None:
        return opts

    registry = _installed_fontspec_script_registry()
    if registry is None:
        return opts

    tag_key = _normalize_fontspec_token(str(script_iso))
    installed_name = registry.names_by_tag.get(tag_key)
    if installed_name:
        return _format_fontspec_script_option(installed_name)

    name_key = _normalize_fontspec_token(script_name)
    for installed in sorted(registry.names):
        if _normalize_fontspec_token(installed) == name_key:
            return _format_fontspec_script_option(installed)

    return ""


def _format_script_display(script_iso: str) -> str:
    """
    Convert ISO script code to human-readable display form.

    Parameters
    ----------
    script_iso : str
        ISO-15924 script code to format.

    Returns
    -------
    str
        Human-readable display label including the canonical script
        name when available.

    Notes
    -----
    Example: ``"TAML" -> "Tamil (TAML)"``.
    Unknown script codes are returned in their normalized uppercase form.
    """
    iso = ScriptISO(script_iso.upper())
    info = SCRIPT_INFO.get(iso)
    if info:
        human = info["canonical_name"]
        return f"{human} ({iso})"
    return str(iso)


def _format_language_display(language_code: str) -> str:
    """
    Convert a language code to a human-readable display form.

    Parameters
    ----------
    language_code : str
        ISO 639 language code to format.

    Returns
    -------
    str
        Human-readable display label including the canonical language
        name when available.

    Notes
    -----
    Example: ``"en" -> "English (en)"``.
    Unknown language codes are returned as-is.
    """
    info = LANGUAGE_INFO.get(language_code)
    if info:
        human = info["canonical_name"]
        return f"{human} ({language_code})"
    return language_code


def _get_render_policy(script_iso: ScriptISO) -> tuple[str, str]:
    """
    Return Polyglossia language and fontspec options for a script.

    Parameters
    ----------
    script_iso : ScriptISO
        Canonical script code used to look up rendering policy.

    Returns
    -------
    tuple[str, str]
        Two-element tuple ``(polyglossia_language, fontspec_options)``.

    Notes
    -----
    The policy is driven entirely by the ontology table. This helper
    must not synthesize `Script=` names from ISO-15924 codes because
    those values are not guaranteed to match the names accepted by
    `fontspec`.
    """
    info = SCRIPT_INFO.get(script_iso)

    if not info:
        return "", ""

    lang = info["polyglossia_language"]
    opts = info["fontspec_opts"] or ""
    opts = _fontspec_compatible_script_opts(script_iso, opts)

    return lang, opts


def _collect_polyglossia_other_languages(font_list: list[CatalogFontEntryV12]) -> str:
    r"""
    Collect secondary Polyglossia languages required by the font list.

    Parameters
    ----------
    font_list : list[CatalogFontEntryV12]
        Catalog font entries whose inferred scripts determine required
        Polyglossia declarations.

    Returns
    -------
    str
        Concatenated ``\\setotherlanguage{{...}}`` declarations for the
        LaTeX preamble.

    Notes
    -----
    Deterministic behavior:
    - stable ordering (sorted)
    - never fails rendering if a mapping is missing
    - always includes ``latin`` to preserve legacy template assumptions
    """
    # Always include latin to preserve legacy template assumptions
    langs: set[str] = {"latin"}  # preserve previous template behavior

    for font in font_list:
        inf_raw = font.get("inference") or {}
        inf = inf_raw if isinstance(inf_raw, dict) else {}
        scripts_raw_obj = inf.get("scripts")
        scripts_raw: list[str] = (
            scripts_raw_obj if isinstance(scripts_raw_obj, list) else []
        )

        for s in scripts_raw:
            if not isinstance(s, str) or not s:
                continue
            script_iso = ScriptISO(s.upper())
            info = SCRIPT_INFO.get(script_iso)
            if info:
                lang = info["polyglossia_language"]
                if lang and lang != "english":
                    langs.add(lang)

    return "".join(f"\\setotherlanguage{{{lang}}}\n" for lang in sorted(langs))


def _collect_polyglossia_font_setup(font_list: list[CatalogFontEntryV12]) -> str:
    r"""
    Collect Polyglossia font-command declarations using real catalog fonts.

    Each language-specific ``\\<language>font`` command is declared once in the
    preamble so specimen entries can use a direct local ``\\renewfontfamily``
    without any TeX-side conditionals.

    Parameters
    ----------
    font_list : list[CatalogFontEntryV12]
        Catalog font entries whose inferred scripts may require
        Polyglossia-aware placeholder font declarations.

    Returns
    -------
    str
        Concatenated LaTeX preamble declarations for the required
        Polyglossia language font commands.

    Notes
    -----
    The first eligible catalog font encountered for a given Polyglossia
    language is used as the preamble-level definition. This keeps the
    selection deterministic while avoiding placeholder bindings such as
    ``Latin Modern Roman`` for unrelated scripts.
    """
    declarations: dict[str, str] = {}

    for font in font_list:
        inf_raw = font.get("inference") or {}
        inf = inf_raw if isinstance(inf_raw, dict) else {}
        scripts_raw_obj = inf.get("scripts")
        scripts_raw: list[str] = (
            scripts_raw_obj if isinstance(scripts_raw_obj, list) else []
        )

        for s in scripts_raw:
            if not isinstance(s, str) or not s:
                continue
            script_iso = ScriptISO(s.upper())
            info = SCRIPT_INFO.get(script_iso)
            if info:
                lang = info["polyglossia_language"]
                if (
                    lang
                    and lang != "english"
                    and lang not in declarations
                    and _font_has_supported_extension(font)
                ):
                    declaration = _build_polyglossia_font_setup(font, lang, script_iso)
                    if declaration:
                        declarations[lang] = declaration

    return "".join(declarations[lang] for lang in sorted(declarations))


def _font_has_supported_extension(font: CatalogFontEntryV12) -> bool:
    """
    Return whether a catalog font entry points to a supported font file.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Catalog font entry whose `path` field is inspected.

    Returns
    -------
    bool
        ``True`` when the path ends with ``.ttf``, ``.otf``, or ``.ttc``.
    """
    path = str(font.get("path", "")).lower()
    return path.endswith((".ttf", ".otf", ".ttc"))


def _normalize_font_path_for_latex(fullpath: str) -> tuple[str, str]:
    """
    Normalize a font file path for LaTeX/fontspec usage.

    Parameters
    ----------
    fullpath : str
        Original font file path, possibly using platform-specific
        separators.

    Returns
    -------
    tuple[str, str]
        Two-element tuple ``(dir_with_trailing_slash, filename)``.
    """
    norm = fullpath.replace("\\", "/")
    if "/" in norm:
        directory, filename = norm.rsplit("/", 1)
        directory = (directory + "/") if directory else "./"
        return directory, filename
    return "./", norm


def _build_polyglossia_font_setup(
    font: CatalogFontEntryV12, lang: str, script_iso: ScriptISO
) -> str:
    r"""
    Build a preamble ``\\newfontfamily`` declaration for one language.

    Parameters
    ----------
    font : CatalogFontEntryV12
        Catalog font entry providing the actual file path used for the
        declaration.
    lang : str
        Polyglossia language name whose font command will be defined.
    script_iso : ScriptISO
        Script whose render policy determines the emitted fontspec
        options.

    Returns
    -------
    str
        Complete ``\\newfontfamily`` declaration ending with a newline,
        or an empty string if the entry cannot be emitted.
    """
    fullpath = str(font.get("path", ""))
    if not _font_has_supported_extension(font):
        return ""

    directory, filename = _normalize_font_path_for_latex(fullpath)
    file_suffix = Path(filename).suffix
    file_stem = Path(filename).stem
    detok_dir = "\\detokenize{" + _latex_detokenize_safe(directory) + "}"
    detok_stem = "\\detokenize{" + _latex_detokenize_safe(file_stem) + "}"
    renderer_prefix = _renderer_option_prefix()
    _, script_opt = _get_render_policy(script_iso)

    render_options: list[str] = []
    if renderer_prefix:
        render_options.append(renderer_prefix.rstrip(","))
    render_options.append("Path=" + detok_dir)
    if script_opt and file_suffix:
        render_options.append("Extension=" + file_suffix)
    if script_opt:
        render_options.append(script_opt)
    opts = ",".join(render_options)

    return (
        "\\newfontfamily\\"
        + lang
        + "font[BoldFont={},ItalicFont={},BoldItalicFont={},"
        + opts
        + "]{"
        + detok_stem
        + "}\n"
    )


def nfss_family_id(font: CatalogFontEntryV12) -> str:
    """
    Return a deterministic NFSS-safe identifier for a font.

    The identifier is derived from a stable SHA-256 digest of:
        <path>#0

    Parameters
    ----------
    font : CatalogFontEntryV12
        Font descriptor dictionary containing a filesystem `path`
        field.

    Returns
    -------
    str
        Deterministic identifier prefixed with "FS" and truncated to
        10 hexadecimal characters.

    Notes
    -----
    The identifier is stable for a given ``path`` and is suitable for use as an internal NFSS
    family token rather than a user-facing label.
    """
    file_path = font.get("path", "")

    key = f"{file_path}#0"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return "FS" + digest[:10]
