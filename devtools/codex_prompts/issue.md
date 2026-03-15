Work on a GitHub issue.

Steps:
1. Ask the user for the issue number.
2. Read in issues.json the issue description.
3. Reproduce the problem. If not reproductible -> stop.
4. Locate the code involved.
5. Identify the minimal fix.
6. Propose a plan and wait for confirmation.
7. Generate a patch implementing the fix.
8. If tests are missing, add them.
9. Generate a commit block for the fix indicating the closing of the issue.

Constraints:
- Minimal changes
- No refactoring unless required
- Preserve existing API behavior
