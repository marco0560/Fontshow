# Contributing to Fontshow

Thank you for your interest in contributing to Fontshow.

This project enforces **signed commits**.

Commit signing is mandatory.
The authoritative policy is defined in:
`docs/security-and-release-policy.md`

## Requirements

Before submitting a contribution, you must:

1. Use Git with SSH transport
2. Configure SSH-based commit signing
3. Register your signing key on GitHub

## Development workflow

Fontshow uses a **pre-commit–driven workflow** to keep generated artifacts
and documentation consistent and to avoid noisy or accidental changes.

Local semantic-release dry-runs require a temporary GitHub token
(GH_TOKEN) due to mandatory GitHub plugin verification, even in dry-run mode.

### Development tooling

Fontshow provides a small set of development helpers implemented as Python
scripts under the `scripts/` directory.

For convenience, commonly used helpers are exposed via Git aliases
(e.g. `git clean-artifacts`, `git test-coverage`, `git release-preview`).

See `scripts.md` for details.

Performance benchmarking is documented separately because it is an
on-demand local workflow and is not part of CI:

- `performance.md`

For repository-wide docstring audits, use:

```bash
repoindex audit-docstrings
```

If you want to inspect only a subset of findings, filter the output text with
`rg`, for example:

```bash
repoindex audit-docstrings | rg 'git_alias_entries|build_bootstrap_commands'
```

### Semantic-release and git hooks

Fontshow uses `semantic-release` to automate versioning and changelog
generation. However, its usage differs between local development and CI.

#### Local development

- direct `git push` to `main` is blocked by the pre-push hook
- use `git rel` for guarded pushes to `main`
- direct `git push` remains allowed on non-`main` branches
- The pre-push hook may optionally run a `semantic-release --dry-run`
  **only if** a `GH_TOKEN` environment variable is present
- If `GH_TOKEN` is not set, the semantic-release preview is skipped
  without blocking the push

This design ensures that:

- guarded release pushes to `main` remain deterministic
- branch pushes work in all environments (Linux, WSL, Windows)
- no local credentials are required by default
- release planning remains an explicit, opt-in action

For local release previews, contributors can run:

```bash
python scripts/release_preview.py
```

or use a convenience alias that injects a temporary `GH_TOKEN`.

#### Continuous Integration (CI)

In CI environments:

- `semantic-release` runs with full credentials
- authentication is mandatory
- failures are blocking

CI remains the single authoritative gate for releases.

### Pre-commit hooks

Before each commit, the following checks and generators may run automatically:

- Code formatters and linters
- Validation checks
- Documentation generators (when applicable)

One generated artifact deserves special attention:

- `docs/cheatsheet.md`

### Cheatsheet generation

The cheatsheet is generated from source metadata using:

```bash
python scripts/generate_cheatsheet.py
```

This script is executed automatically by a **pre-commit hook**.

#### Expected behavior

- If the generated content is **identical** to the current `docs/cheatsheet.md`,
  the file **must not be modified**
- If the content **differs**, the hook will update `docs/cheatsheet.md`
  and the change must be included in the commit

This ensures that commits never contain accidental or stale cheatsheet updates.

#### Manual execution

You may run the generator manually at any time:

```bash
python scripts/generate_cheatsheet.py
```

If this command produces changes, they are considered intentional and
should be committed explicitly.

### Rationale

Generated documentation is treated as a **derived artifact**:

- It must always be reproducible
- It must never drift from source definitions
- It must not introduce "dirty" commits when no semantic changes occurred

The pre-commit hook enforces these guarantees automatically.

## Commit Signing (Required)

All commits authored by contributors **must be cryptographically signed**
using SSH signing.

Unsigned commits will be rejected by GitHub.

> ⚠️ This repository enforces commit signing at server level.
> Local hooks are provided for convenience only.

### Reference Policy

The authoritative security and release policy is defined in:

- `docs/security-and-release-policy.md`

Key rotation procedures are documented in:

- `docs/key-rotation.md`

### Commit Signing

Commits must be signed using SSH:

```bash
git config --global gpg.format ssh
git config --global commit.gpgsign true
git config --global user.signingkey ~/.ssh/<SIGNING_KEY>.pub
```

Commits that are not signed will be rejected.

## Commit Message Format

This project follows a conventional commit format:

```txt
<type>(<scope>): <summary>
```

Examples:

```txt
feat(core): add inventory validation
fix(catalog): escape LaTeX special characters
docs(docs): update security policy
```

### Git commit message template

This repository uses a commit message template stored in `.gitmessage`.

To ensure consistent behavior across platforms (Linux, Windows, macOS)
and tools (CLI, VS Code), the template is configured at **repository level**
using:

```bash
git config commit.template .gitmessage
```

The recommended bootstrap command applies this automatically:

```bash
python3 scripts/bootstrap_dev_environment.py
```

Notes:

- `.gitignore` does not affect already tracked files.
- VS Code relies on Git configuration for commit templates.
- Do NOT set a user-specific global commit template for this repo.

If the template does not appear in your editor, verify with:

```bash
git config --get commit.template
```

## Verification

You can verify your last commit with:

```bash
git log --show-signature -1
```

It must show a valid signature.

## Notes

- Signing keys must be added to GitHub as *Signing keys*
- Authentication keys alone are not sufficient
- CI may reject unsigned commits
