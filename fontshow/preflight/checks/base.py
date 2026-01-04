# fontshow/preflight/checks/base.py

from abc import ABC, abstractmethod

from fontshow.preflight.model import CheckResult


class BaseCheck(ABC):
    """
    Abstract base class for all preflight checks.

    Contract:
    - subclasses MUST define a non-empty `check_id` string
    - subclasses MUST implement `run()` returning a CheckResult
    """

    check_id: str

    @abstractmethod
    def run(self) -> CheckResult:
        raise NotImplementedError
