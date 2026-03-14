"""
Exercise validate-inventory runtime behavior.

Responsibilities
----------------
- Cover file, JSON, and schema-failure error paths.
- Verify semantic and inventory warnings are routed by severity.
- Keep tests deterministic by patching validation helpers directly.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from jsonschema.exceptions import ValidationError

from fontshow.cli import validate_inventory
from fontshow.core.types import Severity
from tests.helpers import minimal_inventory_v12


def test_run_reports_missing_inventory_file(monkeypatch, tmp_path):
    """
    Ensure missing files fail before any validation work runs.
    """
    errors: list[str] = []
    monkeypatch.setattr(validate_inventory, "log_err", errors.append)

    args = SimpleNamespace(
        path=str(tmp_path / "missing.json"), quiet=False, verbose=False
    )

    assert validate_inventory.run(args) == 1
    assert errors == [f"file not found: {tmp_path / 'missing.json'}"]


def test_run_reports_invalid_json(monkeypatch, tmp_path):
    """
    Ensure malformed JSON is converted into a CLI error and exit code 1.
    """
    path = tmp_path / "inventory.json"
    path.write_text("{", encoding="utf-8")

    errors: list[str] = []
    monkeypatch.setattr(validate_inventory, "log_err", errors.append)

    args = SimpleNamespace(path=str(path), quiet=False, verbose=False)

    assert validate_inventory.run(args) == 1
    assert len(errors) == 1
    assert errors[0].startswith("invalid JSON file:")


def test_run_reports_schema_validation_failure(monkeypatch, tmp_path):
    """
    Ensure schema validation failures are logged and returned as rc=1.
    """
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps({}), encoding="utf-8")

    monkeypatch.setattr(validate_inventory, "normalize_loaded_enums", lambda data: None)

    def _fail(_data):
        msg = "schema boom"
        raise ValidationError(msg)

    errors: list[str] = []
    monkeypatch.setattr(validate_inventory, "validate_inventory_schema", _fail)
    monkeypatch.setattr(validate_inventory, "log_err", errors.append)

    args = SimpleNamespace(path=str(path), quiet=False, verbose=False)

    assert validate_inventory.run(args) == 1
    assert errors == ["Schema validation failed", "schema boom"]


def test_run_logs_semantic_and_inventory_warnings(monkeypatch, tmp_path):
    """
    Ensure both semantic warnings and pre-existing inventory warnings are emitted.
    """
    data = minimal_inventory_v12()
    data["warnings"] = [
        {
            "code": "inventory_warning",
            "message": "top-level warning",
            "severity": "warn",
        }
    ]

    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    calls: list[tuple[Severity | None, str]] = []
    oks: list[str] = []

    def _normalize(loaded):
        loaded["warnings"][0]["severity"] = Severity.WARN

    monkeypatch.setattr(validate_inventory, "normalize_loaded_enums", _normalize)
    monkeypatch.setattr(
        validate_inventory, "validate_inventory_schema", lambda loaded: None
    )
    monkeypatch.setattr(
        validate_inventory,
        "validate_language_codes",
        lambda loaded: [
            {
                "code": "semantic_warning",
                "font": "Alpha",
                "message": "semantic issue",
                "severity": Severity.ERROR,
            }
        ],
    )
    monkeypatch.setattr(
        validate_inventory,
        "_log_by_severity",
        lambda severity, message: calls.append((severity, message)),
    )
    monkeypatch.setattr(validate_inventory, "log_ok", oks.append)

    args = SimpleNamespace(path=str(path), quiet=False, verbose=False)

    assert validate_inventory.run(args) == 0
    assert calls == [
        (Severity.ERROR, "semantic_warning (Alpha): semantic issue"),
        (Severity.WARN, "inventory_warning: top-level warning"),
    ]
    assert oks == ["Schema validation passed."]


def test_main_delegates_to_run(monkeypatch):
    """
    Ensure the public entrypoint is a thin wrapper around ``run``.
    """
    seen: list[object] = []
    args = SimpleNamespace(path="inventory.json", quiet=False, verbose=False)

    monkeypatch.setattr(
        validate_inventory, "run", lambda received: seen.append(received) or 7
    )

    assert validate_inventory.main(args) == 7
    assert seen == [args]
