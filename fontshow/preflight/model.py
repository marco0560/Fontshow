"""
Preflight data model.

This module defines the core data structures used to represent the
results of preflight environment checks.

Responsibilities
----------------
- Define immutable representations of individual check results.
- Aggregate check results into a structured preflight report.
- Provide utilities for computing overall severity levels.

Design principles
-----------------
The data model is intentionally minimal and independent from CLI
presentation or check execution logic. It provides deterministic and
serializable representations of check outcomes.

Architectural role
------------------
This module belongs to the **preflight subsystem** and defines the
result structures produced by the preflight execution pipeline.
"""

from dataclasses import dataclass

from fontshow.core.types import Severity


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
