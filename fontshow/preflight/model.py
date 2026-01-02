from dataclasses import dataclass
from enum import Enum, auto


class Severity(Enum):
    INFO = auto()
    OK = auto()
    WARN = auto()
    ERROR = auto()


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    severity: Severity
    message: str
    skipped: bool = False


@dataclass
class PreflightResult:
    results: list[CheckResult]

    @property
    def overall_severity(self) -> Severity:
        if any(r.severity is Severity.ERROR for r in self.results):
            return Severity.ERROR
        if any(r.severity is Severity.WARN for r in self.results):
            return Severity.WARN
        if any(r.severity is Severity.OK for r in self.results):
            return Severity.OK
        return Severity.OK
