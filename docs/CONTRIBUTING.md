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

## Commit Signing

Commits must be signed using SSH:

```
git config --global gpg.format ssh
git config --global commit.gpgsign true
git config --global user.signingkey ~/.ssh/<SIGNING_KEY>.pub
```

Commits that are not signed will be rejected.

## Commit Message Format

This project follows a conventional commit format:

```
<type>(<scope>): <summary>
```

Examples:

```
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
