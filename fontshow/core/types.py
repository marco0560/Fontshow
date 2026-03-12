"""
Core shared type definitions.

This module defines fundamental data types used throughout the
Fontshow codebase.

Responsibilities
----------------
- Define typed structures used across the pipeline.
- Provide canonical representations of script identifiers.
- Provide shared enums and TypedDict structures used by multiple
  subsystems.

Design principles
-----------------
Core types must remain lightweight and dependency-free so they can be
imported from any subsystem without introducing circular dependencies.

Architectural role
------------------
This module belongs to the **core infrastructure layer** and defines
shared type abstractions used across the inventory, catalog, platform,
and CLI subsystems.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Literal, NewType, NotRequired, TypedDict

# ------------------------------------------------------------------
# Script identifier canonical types (Phase 5)
# ------------------------------------------------------------------

# ISO-15924 uppercase (canonical internal representation)
ScriptISO = NewType("ScriptISO", str)

# lowercase tag representation (serialization / coverage field)
ScriptTag = NewType("ScriptTag", str)


def iso_to_tag(script: ScriptISO | str) -> ScriptTag:
    """
    Convert ISO15924 uppercase identifier to lowercase tag form.

    Parameters
    ----------
    script : ScriptISO | str
        Canonical ISO-15924 script identifier or equivalent string.

    Returns
    -------
    ScriptTag
        Lowercase tag representation of the input script.

    Notes
    -----
    Example: ``LATN`` -> ``latn``.
    """
    return ScriptTag(str(script).lower())


def tag_to_iso(tag: ScriptTag | str) -> ScriptISO:
    """
    Convert lowercase tag to ISO15924 uppercase identifier.

    Parameters
    ----------
    tag : ScriptTag | str
        Lowercase script tag or equivalent string.

    Returns
    -------
    ScriptISO
        Uppercase ISO-15924 representation of the input tag.

    Notes
    -----
    Example: ``latn`` -> ``LATN``.
    """
    return ScriptISO(str(tag).upper())


# ------------------------------------------------------------------
# Script normalization helpers (Phase 6 — canonical identity)
# ------------------------------------------------------------------


def normalize_script_iso(value: ScriptISO | ScriptTag | str | None) -> ScriptISO | None:
    """
    Normalize any script identifier to canonical ScriptISO.

    Parameters
    ----------
    value : ScriptISO | ScriptTag | str | None
        Script identifier to normalize.

    Returns
    -------
    ScriptISO | None
        Canonical uppercase script identifier, or None if the input is
        None.

    Notes
    -----
    Behavior-preserving helper:
        None  -> None
        other -> uppercase ISO form
    This centralizes scattered `.upper()` conversions without
    changing semantics.
    """
    if value is None:
        return None
    return ScriptISO(str(value).upper())


def normalize_script_tag(value: ScriptISO | ScriptTag | str | None) -> ScriptTag | None:
    """
    Normalize any script identifier to canonical ScriptTag.

    Parameters
    ----------
    value : ScriptISO | ScriptTag | str | None
        Script identifier to normalize.

    Returns
    -------
    ScriptTag | None
        Canonical lowercase script tag, or None if the input is None.

    Notes
    -----
    Behavior-preserving helper mirroring historical `.lower()` usage.
    """
    if value is None:
        return None
    return ScriptTag(str(value).lower())


# ------------------------------------------------------------------
# Script Rendering Policy (Phase 6)
# ------------------------------------------------------------------


@dataclass(frozen=True)
class ScriptRenderPolicy:
    """
    Rendering policy for a script.

    language:
        polyglossia language ("" if none)

    fontspec_opts:
        options passed to fontspec

    rtl:
        render right-to-left

    requires_polyglossia:
        whether TestNonLatin must be used
    """

    language: str
    fontspec_opts: str
    rtl: bool
    requires_polyglossia: bool


Confidence = Literal["high", "medium"]


class LanguageInferenceInfo(TypedDict):
    """
    Structured language-inference evidence for a single candidate.

    Parameters
    ----------
    None

    Notes
    -----
    This structure captures both the qualitative confidence bucket and
    the evidence strings supporting a language inference result.
    """

    confidence: Confidence
    evidence: list[str]


class InferenceInfo(TypedDict, total=False):
    """
    Lightweight inference payload attached to generic font references.

    Parameters
    ----------
    None

    Notes
    -----
    This typed dictionary is used in shared code paths that only require
    a minimal subset of inference data such as languages, primary
    script, and numeric confidence.
    """

    languages: list[str]
    script: str | None
    confidence: float | None


class ExecutionContext(Enum):
    """
    Execution environment classification.

    Notes
    -----
    JSON representation follows ADR-0019 using lowercase stable string
    tokens.
    """

    NATIVE = auto()
    WSL = auto()
    CONTAINER = auto()
    OTHER = auto()

    def to_json(self) -> str:
        """
        Convert the enum value to its serialized JSON token.

        Parameters
        ----------
        None

        Returns
        -------
        str
            Lowercase token representing the execution context.
        """
        return self.name.lower()

    @classmethod
    def from_str(cls, value: str) -> ExecutionContext:
        """
        Parse a serialized execution-context token.

        Parameters
        ----------
        value : str
            Input token to normalize.

        Returns
        -------
        ExecutionContext
            Matching execution-context enum member.

        Raises
        ------
        ValueError
            If `value` does not correspond to a supported execution
            context token.
        """
        v = value.lower()
        if v == "native":
            return cls.NATIVE
        if v == "wsl":
            return cls.WSL
        if v == "container":
            return cls.CONTAINER
        if v == "other":
            return cls.OTHER
        error_msg = f"Invalid execution_context: {value!r}"
        raise ValueError(error_msg)


class Severity(Enum):
    """
    Canonical severity levels used by CLI and structured warnings.

    Notes
    -----
    The enum supports both in-memory routing decisions and explicit JSON
    serialization via `to_json()` and `from_str()`.
    """

    INFO = auto()
    OK = auto()
    WARN = auto()
    ERROR = auto()

    def to_json(self) -> str:
        """
        Convert the severity enum to its serialized JSON token.

        Parameters
        ----------
        None

        Returns
        -------
        str
            Stable lowercase severity token, with `WARN` serialized as
            ``"warning"``.
        """
        if self is Severity.WARN:
            return "warning"
        if self is Severity.INFO:
            return "info"
        if self is Severity.ERROR:
            return "error"
        return self.name.lower()

    @classmethod
    def from_str(cls, value: str) -> Severity:
        """
        Parse a severity token into the canonical enum.

        Parameters
        ----------
        value : str
            Serialized severity string.

        Returns
        -------
        Severity
            Matching severity enum member.

        Raises
        ------
        ValueError
            If `value` does not map to a supported severity token.
        """
        v = value.lower()
        if v == "info":
            return cls.INFO
        if v == "ok":
            return cls.OK
        if v in {"warn", "warning"}:
            return cls.WARN
        if v == "error":
            return cls.ERROR
        error_msg = f"Invalid severity: {value!r}"
        raise ValueError(error_msg)


class WarningInfo(TypedDict, total=False):
    """
    Structured warning payload attached to inventories or font entries.

    Parameters
    ----------
    None
    """

    severity: Severity
    code: str
    message: str
    extra: dict[str, Any]


class SampleTextInfo(TypedDict, total=False):
    """
    Embedded specimen text associated with a font.

    Parameters
    ----------
    None
    """

    lang: str
    text: str


class FontRef(TypedDict):
    """
    Shared lightweight font reference used across multiple subsystems.

    Parameters
    ----------
    None

    Notes
    -----
    The structure mixes required identity keys with optional enrichment
    fields used by specimen selection, warnings, and inventory-derived
    metadata helpers.
    """

    family: str
    style: str
    path: NotRequired[str | None]
    index: NotRequired[int | None]
    inference: NotRequired[InferenceInfo]
    warnings: NotRequired[list[WarningInfo]]
    sample_text: NotRequired[SampleTextInfo]


class CoverageV12(TypedDict, total=False):
    """
    Schema v1.2 coverage payload for a font entry.

    Parameters
    ----------
    None

    Notes
    -----
    This structure contains normalized coverage information derived from
    inventory processing, including script tags and Unicode block counts.
    """

    scripts: list[str]
    unicode_blocks: dict[str, int]


class InferenceV12(TypedDict, total=False):
    """
    Schema v1.2 inference payload for a font entry.

    Parameters
    ----------
    None

    Notes
    -----
    The structure records normalized inference results such as the
    active inference level, inferred scripts and languages, and derived
    Unicode block counts.
    """

    level: str
    scripts: list[str]
    languages: list[str]
    unicode_blocks: dict[str, int]


class CatalogFontEntryV12(TypedDict, total=False):
    """
    Minimal catalog-facing font descriptor based on schema v1.2 fields.

    Parameters
    ----------
    None

    Notes
    -----
    This typed dictionary represents the subset of inventory data needed
    by catalog generation, including identity, specimen text, and
    normalized coverage and inference sections.
    """

    path: str
    family: str
    specimen_text: str
    inference: InferenceV12
    coverage: CoverageV12


class DeprecatedLanguageInfo(TypedDict):
    """
    Record describing a deprecated language tag replacement.

    Parameters
    ----------
    None
    """

    raw: str
    from_: str
    to: str


class DroppedLanguageInfo(TypedDict, total=False):
    """
    Record describing a language tag removed during normalization.

    Parameters
    ----------
    None

    Notes
    -----
    The normalized field is optional because some dropped values do not
    map to a replacement tag.
    """

    raw: str
    reason: str
    normalized: str


class NormalizeLanguagesResult(TypedDict):
    """
    Aggregate result returned by language normalization helpers.

    Parameters
    ----------
    None

    Notes
    -----
    The structure separates accepted normalized tags from deprecated and
    dropped entries so callers can both consume canonical output and
    report normalization side effects.
    """

    normalized: list[str]
    deprecated: list[DeprecatedLanguageInfo]
    dropped: list[DroppedLanguageInfo]
