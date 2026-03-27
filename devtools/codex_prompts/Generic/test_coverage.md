Analyze test coverage of the Fontshow repository.

Focus on:
- branches not executed
- exception paths not tested
- boundary conditions

For each uncovered area:

1. explain the missing scenario
2. propose a pytest test
3. generate the test code

Constraints:
- tests must be deterministic
- avoid filesystem dependencies when possible
- use tmp_path fixtures when filesystem is required
- do not modify production code unless strictly necessary
