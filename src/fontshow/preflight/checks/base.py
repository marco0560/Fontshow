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

    Responsibilities
    ----------------
    - Define the execution contract implemented by concrete checks.
    - Provide automatic registration for non-abstract subclasses.
    - Establish shared metadata such as ``check_id`` and
      ``executable``.

    Notes
    -----
    Concrete subclasses are automatically registered at import time and
    form the authoritative registry for built-in checks.
    """

    registry: ClassVar[list[type[BaseCheck]]] = []

    check_id: str
    #: Whether this check is meant to be executed by the runner
    executable: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        """
        Register concrete subclasses automatically when they are defined.

        Parameters
        ----------
        **kwargs : object
            Keyword arguments forwarded to the superclass hook.

        Returns
        -------
        None

        Notes
        -----
        Abstract subclasses are not registered. Only concrete check
        classes are appended to `BaseCheck.registry`.
        """
        super().__init_subclass__(**kwargs)

        # Register only concrete (non-abstract) checks
        if not inspect.isabstract(cls):
            BaseCheck.registry.append(cls)

    @abstractmethod
    def run(self) -> CheckResult:
        """
        Execute the check and return a structured result.

        Parameters
        ----------
        None

        Returns
        -------
        CheckResult
            Result object describing the outcome of the check.

        Raises
        ------
        NotImplementedError
            Raised by the abstract base implementation. Concrete
            subclasses must override this method and may document
            additional exceptions.
        """
        raise NotImplementedError
