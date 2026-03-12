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
    """
    Immutable result produced by a single preflight check.

    Parameters
    ----------
    check_id : str
        Stable identifier of the check that produced the result.
    severity : Severity
        Final severity assigned to the check outcome.
    message : str
        User-facing summary describing the outcome.
    skipped : bool, optional
        Whether the check was skipped instead of executed.

    Notes
    -----
    Each instance captures the check identifier, final severity,
    user-facing message, and whether the check was skipped.

    Instances are frozen so check results remain stable once produced by
    the runner.
    """

    check_id: str
    severity: Severity
    message: str
    skipped: bool = False


@dataclass
class PreflightResult:
    """
    Aggregate result returned by the preflight runner.

    Parameters
    ----------
    results : list[CheckResult]
        Ordered list of individual check results produced by the
        runner.

    Notes
    -----
    The result stores the ordered list of individual `CheckResult`
    objects and derives an overall severity via `overall_severity`.

    The container itself is mutable so tests or orchestration layers can
    construct result sets incrementally if needed.
    """

    results: list[CheckResult]

    @property
    def overall_severity(self) -> Severity:
        """
        Compute the highest-severity outcome across all check results.

        Parameters
        ----------
        None

        Returns
        -------
        Severity
            `ERROR` if any check failed, otherwise `WARN` if any warning
            is present, otherwise `OK`.

        Notes
        -----
        An empty result set currently resolves to `Severity.OK`.
        """
        if any(r.severity is Severity.ERROR for r in self.results):
            return Severity.ERROR
        if any(r.severity is Severity.WARN for r in self.results):
            return Severity.WARN
        if any(r.severity is Severity.OK for r in self.results):
            return Severity.OK
        return Severity.OK
