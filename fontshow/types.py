from typing import Any, Literal, NotRequired, TypedDict

Confidence = Literal["high", "medium"]


class LanguageInferenceInfo(TypedDict):
    confidence: "Confidence"
    evidence: list[str]


class InferenceInfo(TypedDict, total=False):
    languages: list[str]
    script: str | None
    confidence: float | None


class WarningInfo(TypedDict, total=False):
    severity: str
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
