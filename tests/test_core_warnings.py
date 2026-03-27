"""
Verify structured warning attachment behavior.

Responsibilities
----------------
- Ensure warning payloads are appended consistently.
- Cover the empty-``extra`` boundary where no extra payload should be stored.
"""

from fontshow.core.types import Severity
from fontshow.core.warnings import add_structured_warning


def test_add_structured_warning_creates_warning_list_without_empty_extra():
    """
    Ensure an empty ``extra`` mapping does not produce an ``extra`` field.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    container: dict[str, object] = {}

    add_structured_warning(
        container,
        code="boundary",
        message="empty extra payload",
        severity=Severity.WARN,
        extra={},
    )

    assert container == {
        "warnings": [
            {
                "code": "boundary",
                "message": "empty extra payload",
                "severity": Severity.WARN,
            }
        ]
    }


def test_add_structured_warning_appends_to_existing_warning_list():
    """
    Ensure subsequent warnings are appended rather than overwriting state.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    existing = {
        "warnings": [
            {
                "code": "first",
                "message": "already present",
                "severity": Severity.INFO,
            }
        ]
    }

    add_structured_warning(
        existing,
        code="second",
        message="new warning",
        severity=Severity.ERROR,
        extra={"source": "test"},
    )

    assert existing["warnings"] == [
        {
            "code": "first",
            "message": "already present",
            "severity": Severity.INFO,
        },
        {
            "code": "second",
            "message": "new warning",
            "severity": Severity.ERROR,
            "extra": {"source": "test"},
        },
    ]
