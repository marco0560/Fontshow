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

        LATN → latn
    """
    return ScriptTag(str(script).lower())


def tag_to_iso(tag: ScriptTag | str) -> ScriptISO:
    """
    Convert lowercase tag to ISO15924 uppercase identifier.

        latn → LATN
    """
    return ScriptISO(str(tag).upper())


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
    confidence: Confidence
    evidence: list[str]


class InferenceInfo(TypedDict, total=False):
    languages: list[str]
    script: str | None
    confidence: float | None


class ExecutionContext(Enum):
    """
    Execution environment classification.

    JSON representation follows ADR-0019:
    - lowercase stable string tokens
    """

    NATIVE = auto()
    WSL = auto()
    CONTAINER = auto()
    OTHER = auto()

    def to_json(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, value: str) -> ExecutionContext:
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
    INFO = auto()
    OK = auto()
    WARN = auto()
    ERROR = auto()

    def to_json(self) -> str:
        if self is Severity.WARN:
            return "warning"
        if self is Severity.INFO:
            return "info"
        if self is Severity.ERROR:
            return "error"
        return self.name.lower()

    @classmethod
    def from_str(cls, value: str) -> Severity:
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
    severity: Severity
    code: str
    message: str
    extra: dict[str, Any]


class SampleTextInfo(TypedDict, total=False):
    lang: str
    text: str


class FontRef(TypedDict):
    family: str
    style: str
    path: NotRequired[str | None]
    index: NotRequired[int | None]
    inference: NotRequired[InferenceInfo]
    warnings: NotRequired[list[WarningInfo]]
    sample_text: NotRequired[SampleTextInfo]


class CoverageV12(TypedDict, total=False):
    scripts: list[str]
    unicode_blocks: dict[str, int]


class InferenceV12(TypedDict, total=False):
    level: str
    scripts: list[str]
    languages: list[str]
    unicode_blocks: dict[str, int]


class CatalogFontEntryV12(TypedDict, total=False):
    path: str
    family: str
    specimen_text: str
    inference: InferenceV12
    coverage: CoverageV12


class DeprecatedLanguageInfo(TypedDict):
    raw: str
    from_: str
    to: str


class DroppedLanguageInfo(TypedDict, total=False):
    raw: str
    reason: str
    normalized: str


class NormalizeLanguagesResult(TypedDict):
    normalized: list[str]
    deprecated: list[DeprecatedLanguageInfo]
    dropped: list[DroppedLanguageInfo]
