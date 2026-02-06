# fontshow/preflight/checks/base.py
from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from fontshow.preflight.model import CheckResult


class BaseCheck(ABC):
    """
    Abstract base class for all preflight checks.

    Concrete subclasses are automatically registered at import time
    and form the authoritative registry for built-in checks.
    """

    registry: ClassVar[list[type[BaseCheck]]] = []

    check_id: str
    #: Whether this check is meant to be executed by the runner
    executable: bool = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Register only concrete (non-abstract) checks
        if not inspect.isabstract(cls):
            BaseCheck.registry.append(cls)

    @abstractmethod
    def run(self) -> CheckResult:
        """Execute the check and return a CheckResult."""
        raise NotImplementedError
