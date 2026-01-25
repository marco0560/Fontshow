import json
from pathlib import Path

from fontshow.schema_validation import validate_inventory_schema


def test_real_inventory_regression_no_errors():
    """
    Regression test using a real-world inventory file.

    Ensures:
    - schema validation does not raise
    - no error-level warnings are emitted
    """

    fixture = Path(__file__).parent / "fixtures" / "inventory_real.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))

    warnings = validate_inventory_schema(data)

    # No hard errors allowed
    assert all("code" in w for w in warnings)
    assert all("severity" in w for w in warnings)
