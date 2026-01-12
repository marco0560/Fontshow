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
