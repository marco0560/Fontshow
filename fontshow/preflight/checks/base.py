"""
Preflight check base classes.

This module defines the abstract base class used by all preflight
environment checks.

Responsibilities
----------------
- Provide the base interface implemented by all checks.
- Automatically register concrete check classes.
- Define the contract for executing checks and returning results.

Design principles
-----------------
Preflight checks are implemented as independent classes that return
structured results. Automatic registration ensures that checks can be
discovered without requiring manual configuration.

Architectural role
------------------
This module belongs to the **preflight subsystem** and defines the
foundation used by all preflight environment checks.
"""

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
