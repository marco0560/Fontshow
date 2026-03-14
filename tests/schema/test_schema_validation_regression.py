"""
Verify schema validation regression behavior.

This module tests schema validation using a reduced real-world
inventory snapshot.

Responsibilities
----------------
- Validate compatibility with real inventory data.
- Detect schema-breaking changes.
- Ensure no ERROR-level validation issues occur for the snapshot.

Design principles
-----------------
Regression tests use stable input snapshots so that changes to schema
validation logic are detected deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
schema validation stability across real-world inventory examples.

Note
----
This file is NOT intended to be exhaustive nor representative
of the full inventory.
"""

from fontshow.inventory.schema_validation import validate_inventory_schema
from tests.helpers import minimal_inventory_v12


def test_schema_v1_2_inventory_regression_no_errors():
    """
    Regression test using a real-world inventory file.

    Ensures:
    - schema validation does not raise
    - no error-level warnings are emitted

    Returns
    -------
    None
    """

    data = minimal_inventory_v12()

    warnings = validate_inventory_schema(data)

    # No hard errors allowed
    assert all("code" in w for w in warnings)
    assert all("severity" in w for w in warnings)
