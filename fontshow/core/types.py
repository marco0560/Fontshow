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


# ------------------------------------------------------------------
# Script Rendering Policy (Phase 6)
# ------------------------------------------------------------------


@dataclass(frozen=True)
class ScriptRenderPolicy:
    """
    Rendering policy describing how a script should be typeset.

    Parameters
    ----------
    language : str
        Polyglossia language identifier, or ``""`` when no explicit
        language should be selected.
    fontspec_opts : str
        Raw ``fontspec`` options applied when rendering text for the
        script.
    rtl : bool
        Whether the script must be rendered right-to-left.
    requires_polyglossia : bool
        Whether rendering requires the ``TestNonLatin`` / Polyglossia
        path instead of the default Latin-oriented template flow.

    Notes
    -----
    This dataclass is a normalized policy object shared between script
    analysis and LaTeX rendering code. It carries rendering decisions
    only and does not perform any inference itself.
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
    severity : Severity
        Severity level associated with the warning.
    code : str
        Machine-readable warning identifier.
    message : str
        Human-readable warning message.
    extra : dict[str, Any]
        Optional structured payload with warning-specific metadata.
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
    lang : str
        Language tag associated with the embedded sample text.
    text : str
        Sample text payload extracted for the font.
    """

    lang: str
    text: str


class FontRef(TypedDict):
    """
    Shared lightweight font reference used across multiple subsystems.

    Parameters
    ----------
    family : str
        Canonical family name.
    style : str
        Style or subfamily label.
    path : str | None, optional
        Source font path when available.
    index : int | None, optional
        Face index for collection-based fonts.
    inference : InferenceInfo, optional
        Minimal inference payload associated with the font.
    warnings : list[WarningInfo], optional
        Structured warnings attached to the font.
    sample_text : SampleTextInfo, optional
        Embedded sample text payload.

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
    scripts : list[str]
        Normalized script tags associated with the font.
    unicode_blocks : dict[str, int]
        Covered Unicode block counts keyed by block name.

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
    level : str
        Inference aggressiveness level used to derive the payload.
    scripts : list[str]
        Inferred script tags.
    languages : list[str]
        Inferred language tags.
    unicode_blocks : dict[str, int]
        Unicode block counts retained for inference diagnostics.

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
    path : str
        Source font path.
    family : str
        Canonical family name.
    specimen_text : str
        Text chosen for catalog specimen rendering.
    inference : InferenceV12
        Inference payload used by catalog helpers.
    coverage : CoverageV12
        Coverage payload used by catalog helpers.

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
    raw : str
        Original raw language value.
    from_ : str
        Deprecated normalized language tag.
    to : str
        Replacement canonical language tag.
    """

    raw: str
    from_: str
    to: str


class DroppedLanguageInfo(TypedDict, total=False):
    """
    Record describing a language tag removed during normalization.

    Parameters
    ----------
    raw : str
        Original raw language value.
    reason : str
        Drop reason identifier.
    normalized : str
        Replacement normalized value when one exists.

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
    normalized : list[str]
        Accepted normalized language tags.
    deprecated : list[DeprecatedLanguageInfo]
        Deprecated-tag remaps encountered during normalization.
    dropped : list[DroppedLanguageInfo]
        Dropped inputs with structured reasons.

    Notes
    -----
    The structure separates accepted normalized tags from deprecated and
    dropped entries so callers can both consume canonical output and
    report normalization side effects.
    """

    normalized: list[str]
    deprecated: list[DeprecatedLanguageInfo]
    dropped: list[DroppedLanguageInfo]
