from enum import Enum, auto
from typing import Any, Literal, NotRequired, TypedDict

Confidence = Literal["high", "medium"]


class LanguageInferenceInfo(TypedDict):
    confidence: "Confidence"
    evidence: list[str]


class InferenceInfo(TypedDict, total=False):
    languages: list[str]
    script: str | None
    confidence: float | None


class Severity(Enum):
    INFO = auto()
    OK = auto()
    WARN = auto()
    ERROR = auto()

    def to_json(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, value: str) -> "Severity":
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
