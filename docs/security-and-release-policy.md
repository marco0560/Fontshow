# Security and Release Policy

## Commit Signing Policy

All contributors are required to sign their commits using SSH or GPG keys.

This project uses **SSH-based commit signing** as the preferred mechanism.

### Developer Responsibilities

- Developers MUST enable commit signing in their local Git configuration.
- Commits created locally are expected to be signed.
- Local hooks (`pre-commit`, `commit-msg`) enforce commit hygiene and conventions.

> Note: Local enforcement is intentional and required.

## Enforcement Model

This project uses GitHub Repository Rulesets as the **authoritative enforcement
mechanism** for security and release integrity.

The following principles apply:

- All human-authored commits **must be cryptographically signed**
  (SSH signing, verified by GitHub).
- GitHub is the **single source of truth** for enforcement.
- Local hooks and CI checks are **supportive but not authoritative**.

### CI end Automation Exception

Due to current GitHub limitations, GitHub Actions workflows (including
`semantic-release`) **cannot produce commits with verified cryptographic
signatures**.

As a consequence:

- Repository Rulesets explicitly allow a **documented bypass for CI automation**
- This exception applies **only** to trusted automation
- The rationale and failed alternatives are documented in `decisions.md`

See:

- `decisions.md` — for historical context and rejected alternatives
- `CONTRIBUTING.md` — for contributor-facing rules

## Automated Releases

Releases are performed automatically via GitHub Actions using `semantic-release`.

The release process may create unsigned commits (e.g. changelog updates, version bumps), which are trusted as CI-generated artifacts.

## Relationship with GitHub Rulesets

This policy is implemented using GitHub Repository Rulesets.
Local hooks and CI checks are supportive but not authoritative.

## Rationale

GitHub Actions currently cannot produce cryptographically signed commits that satisfy repository rulesets.

This policy represents the best balance between:

- Security
- Automation
- Developer experience

The policy will be revisited if GitHub introduces first-class support for CI-signed commits.
