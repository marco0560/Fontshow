"""
Pytest configuration and shared fixtures for Fontshow tests.

Responsibilities
----------------
- Provide global pytest fixtures used across the test suite.
- Configure import paths and runtime environment for tests.
- Offer shared helpers for invoking the Fontshow CLI in tests.

Design principles
-----------------
Test infrastructure must remain deterministic and isolated from the
developer environment. Fixtures here centralize setup logic so tests
remain concise and reproducible.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and provides
shared pytest configuration and fixtures for the Fontshow test suite.
"""

import importlib
import logging
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from fontshow.__main__ import main as fontshow_main
from tests.helpers import run_cli

TEST_RUNTIME_TEMP = (Path.home() / "Documents" / "FontshowPytestTemp").resolve()
TEST_RUNTIME_TEMP.mkdir(parents=True, exist_ok=True)
os.environ["TMPDIR"] = str(TEST_RUNTIME_TEMP)
os.environ["TMP"] = str(TEST_RUNTIME_TEMP)
os.environ["TEMP"] = str(TEST_RUNTIME_TEMP)
tempfile.tempdir = str(TEST_RUNTIME_TEMP)

# ---------------------------------------------------------------------------
# Path & import hygiene
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def add_project_root_to_syspath():
    """
    Ensure the project root is importable for the duration of the test session.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    root = (Path(__file__).parent / "..").resolve()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root)


@pytest.fixture(scope="session", autouse=True)
def ensure_fontshow_import_is_clean():
    """
    Clear cached `fontshow` modules after the session to avoid import leakage.

    Parameters
    ----------
    None

    Yields
    ------
    None
    """
    yield
    for name in list(sys.modules):
        if name.startswith("fontshow"):
            del sys.modules[name]


# ---------------------------------------------------------------------------
# Logging control
# ---------------------------------------------------------------------------


@pytest.fixture
def enable_fontshow_logging(monkeypatch):
    """
    Enable DEBUG-level Fontshow logging for a test.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to set the logging environment variable.

    Returns
    -------
    None
    """
    monkeypatch.setenv("FONTSHOW_LOG_LEVEL", "DEBUG")
    import fontshow.core.logging_utils

    importlib.reload(fontshow.core.logging_utils)


@pytest.fixture
def disable_fontshow_logging():
    """
    Temporarily disable Python logging during a test.

    Parameters
    ----------
    None

    Yields
    ------
    None
    """
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def silence_root_logger():
    """
    Remove root logger handlers temporarily to keep test output isolated.

    Parameters
    ----------
    None

    Yields
    ------
    None
    """
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    root.handlers.clear()
    yield
    root.handlers[:] = old_handlers


@pytest.fixture
def capture_fontshow_logs(caplog):
    """
    Capture records from the non-propagating ``fontshow`` logger.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        Fixture used to collect log records during the test.

    Yields
    ------
    pytest.LogCaptureFixture
        Active log-capture fixture configured for the ``fontshow`` logger.
    """
    logger = logging.getLogger("fontshow")

    # 🔴 mandatory
    old_propagate = logger.propagate
    logger.propagate = True

    with caplog.at_level(logging.DEBUG):
        yield caplog

    logger.propagate = old_propagate


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------


@pytest.fixture
def cli_runner():
    """
    Provide a small helper for invoking the Fontshow top-level CLI in tests.

    Parameters
    ----------
    None

    Returns
    -------
    collections.abc.Callable
        Callable that accepts an argv list and returns the normalized
        ``(exit_code, output)`` pair from `tests.helpers.run_cli`.
    """

    def _run(argv):
        """
        Execute the shared Fontshow CLI entrypoint with a provided argv vector.

        Parameters
        ----------
        argv : list[str]
            Argument vector passed to the top-level CLI entrypoint.

        Returns
        -------
        tuple[int, str]
            Pair ``(exit_code, output)`` returned by `tests.helpers.run_cli`.
        """
        return run_cli(fontshow_main, argv)

    return _run


# ---------------------------------------------------------------------------
# Helper: patch argparse dispatch
# ---------------------------------------------------------------------------


def patch_cli_func(monkeypatch, module, fake_func):
    """
    Patch a CLI module entrypoint after argparse parsing.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the module entrypoint.
    module : module
        Imported CLI module whose ``main`` function is patched.
    fake_func : collections.abc.Callable
        Replacement callable invoked by the CLI dispatcher.

    Returns
    -------
    None
    """
    monkeypatch.setattr(module, "main", fake_func)


# ---------------------------------------------------------------------------
# PRE-FLIGHT
# ---------------------------------------------------------------------------


@dataclass
class _FakeSeverity:
    """
    Minimal severity stand-in used by preflight CLI test doubles.

    Parameters
    ----------
    name : str
        Severity label exposed by the fake result object.
    """

    name: str


class _FakePreflightResult:
    """
    Minimal stand-in for a preflight result object used by CLI stubs.

    Parameters
    ----------
    ok : bool
        Whether the fake result should expose overall severity ``OK``
        or ``ERROR``.
    """

    def __init__(self, ok: bool):
        """
        Initialize a fake preflight result with no per-check entries.

        Parameters
        ----------
        ok : bool
            Whether the aggregate fake severity should be ``OK`` or ``ERROR``.

        Returns
        -------
        None
        """
        self.results = []
        self.overall_severity = _FakeSeverity("OK" if ok else "ERROR")


@pytest.fixture
def stub_preflight(monkeypatch, request):
    """
    Stub the preflight CLI callback with parametrized success or failure behavior.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the real preflight entrypoint.
    request : pytest.FixtureRequest
        Fixture request carrying the optional parametrized stub mode.

    Returns
    -------
    None
    """
    # Default behavior if fixture is not parametrized
    mode = getattr(request, "param", "ok")
    ok = mode == "ok"

    def fake_run(args):
        """
        Emulate the argparse callback used by the preflight subcommand.

        Parameters
        ----------
        args : object
            Parsed CLI arguments passed by argparse.

        Returns
        -------
        int
            Stubbed success or failure exit code.
        """
        if ok:
            print("Preflight passed.")
            return 0
        print("Preflight failed.")
        return 1

    import fontshow.preflight

    # Patch the actual function used by argparse
    monkeypatch.setattr(
        fontshow.preflight,
        "run",
        fake_run,
        raising=False,  # attribute may not exist yet
    )


# ---------------------------------------------------------------------------
# DUMP FONTS
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_dump_fonts(monkeypatch, request):
    """
    Stub the dump-fonts CLI entrypoint with parametrized behavior.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the dump-fonts entrypoint.
    request : pytest.FixtureRequest
        Fixture request carrying the parametrized stub mode.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        May be raised by the nested CLI stub in non-success modes.

    Notes
    -----
    The fixture provides a success path and a crashing path so CLI
    wrapper tests can verify exit-code normalization without running the
    real dump-fonts implementation.
    """
    mode = request.param

    def fake_run(_args):
        """
        Emulate the dump-fonts CLI callback with parametrized behavior.

        Parameters
        ----------
        _args : object
            Parsed CLI arguments, unused by the stub.

        Returns
        -------
        int
            Zero for the success mode.

        Raises
        ------
        RuntimeError
            Raised for non-success modes to emulate command failure.
        """
        if mode == "ok":
            return 0
        msg = "dump failed"
        raise RuntimeError(msg)

    from fontshow import dump_fonts

    patch_cli_func(monkeypatch, dump_fonts, fake_run)


# ---------------------------------------------------------------------------
# PARSE INVENTORY
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_parse_inventory(monkeypatch, request):
    """
    Stub the parse-inventory pipeline while preserving CLI wrapper behavior.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the injected parse function and runner.
    request : pytest.FixtureRequest
        Fixture request carrying the parametrized stub mode.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        May be raised by the nested parser stub in validation-failure mode.
    RuntimeError
        May be raised by the nested parser stub in crash mode.

    Notes
    -----
    The fixture keeps the real CLI runner in place and swaps only the
    parsing implementation so command wiring remains under test.
    Parametrized modes cover successful parsing, expected validation
    failure, and unexpected internal failure.
    """
    import copy

    import fontshow.cli.parse_inventory as mod

    mode = request.param

    def fake_parse_inventory(data, *_args, **_kwargs):
        """
        Emulate the parse step used by the parse-inventory CLI runner.

        Parameters
        ----------
        data : dict
            Inventory payload received by the injected parser.
        *_args : object
            Ignored positional arguments preserved for signature compatibility.
        **_kwargs : object
            Ignored keyword arguments preserved for signature compatibility.

        Returns
        -------
        dict
            Deep-copied inventory payload in the success mode.

        Raises
        ------
        ValueError
            Raised in the ``fail`` mode to emulate validation failure.
        RuntimeError
            Raised in the ``boom`` mode to emulate unexpected internal failure.
        """
        if mode == "fail":
            msg = "parse failed"
            raise ValueError(msg)

        if mode == "boom":
            msg = "internal error"
            raise RuntimeError(msg)

        # ok
        return copy.deepcopy(data)

    original_runner = mod.run_parse_font_inventory

    def patched_runner(args, **kwargs):
        """
        Invoke the real CLI runner with the fake parser injected.

        Parameters
        ----------
        args : object
            Parsed CLI arguments forwarded to the real runner.
        **kwargs : object
            Additional injected runner arguments.

        Returns
        -------
        int
            Exit code returned by the real CLI runner.
        """
        return original_runner(
            args,
            parse_inventory_fn=fake_parse_inventory,
            **kwargs,
        )

    monkeypatch.setattr(mod, "run_parse_font_inventory", patched_runner)


# ---------------------------------------------------------------------------
# CREATE CATALOG
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_create_catalog(monkeypatch, request):
    """
    Stub the create-catalog CLI entrypoint with parametrized behavior.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the create-catalog entrypoint.
    request : pytest.FixtureRequest
        Fixture request carrying the parametrized stub mode.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        May be raised by the nested CLI stub in crash mode.

    Notes
    -----
    The fixture exposes success, controlled failure, and crash modes so
    CLI tests can verify top-level dispatch semantics deterministically.
    """
    mode = request.param

    def fake_run(args):
        """
        Emulate the create-catalog CLI callback with parametrized outcomes.

        Parameters
        ----------
        args : object
            Parsed CLI arguments accepted for interface compatibility.

        Returns
        -------
        int
            Stubbed exit code for the configured mode.

        Raises
        ------
        RuntimeError
            Raised in the ``boom`` mode to emulate an unexpected internal crash.
        """
        if mode == "ok":
            return 0
        if mode == "fail":
            return 1
        if mode == "boom":
            raise RuntimeError(mode)
        return 2  # explicit fallback (non-None exit code)

    from fontshow import create_catalog

    monkeypatch.setattr(create_catalog, "main", fake_run)


# ---------------------------------------------------------------------------
# VALIDATE INVENTORY
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_validate_inventory(monkeypatch, request):
    """
    Stub the validate-inventory CLI entrypoint with parametrized behavior.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the validate-inventory entrypoint.
    request : pytest.FixtureRequest
        Fixture request carrying the parametrized stub mode.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        May be raised by the nested CLI stub in crash mode.
    """
    mode = request.param

    def fake_run(args):
        """
        Emulate the validate-inventory CLI callback.

        Parameters
        ----------
        args : object
            Parsed CLI arguments accepted for interface compatibility.

        Returns
        -------
        int
            Stubbed exit code for the configured mode.

        Raises
        ------
        RuntimeError
            Raised in the ``boom`` mode to emulate an unexpected internal crash.
        """
        if mode == "ok":
            return 0
        if mode == "fail":
            return 1
        if mode == "boom":
            raise RuntimeError(mode)
        return 2

    from fontshow import validate_inventory

    monkeypatch.setattr(validate_inventory, "main", fake_run)


# ---------------------------------------------------------------------------
# Clean verbosity state between tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_cli_state():
    """
    Reset shared CLI verbosity state between tests.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    from fontshow.core.cli_utils import set_cli_mode

    set_cli_mode(False, False)
