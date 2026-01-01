# SSH Key Rotation Policy

This project uses **SSH-based commit signing**.

> This document is part of the Fontshow security policy.
> See `security-and-release-policy.md` for the full enforcement model.

To maintain a high security level, contributors and maintainers
must follow the key rotation policy described below.

---

## Key Rotation and Trust Model

This project distinguishes between **human-authored commits** and **CI-generated commits**.

### Human Commits

- All human contributors must use personal SSH keys for commit signing
- Keys must be rotated according to this document
- Compromised keys must be revoked immediately

### CI and Automation

Automated processes (e.g. GitHub Actions) do not use cryptographic commit signing.

CI-generated commits are trusted based on:
- Restricted write access to protected branches
- Mandatory CI checks
- Auditable workflows

This separation is intentional and documented.

See also:
- [Development environment and commit policy](dev-environment.md#commit-signing-and-release-model)

---

## Key Separation

Two distinct SSH keys are required:

- **Authentication key**
  - Used for Git transport (push / pull)
  - May have a passphrase
- **Signing key**
  - Used exclusively for commit signing
  - Must be registered on GitHub as *Signing key*
  - Recommended: no passphrase

---

## Rotation Policy

Signing keys should be rotated when:

- a machine is decommissioned
- a key is suspected to be compromised
- after a major OS or account migration
- periodically (recommended: every 12–24 months)

---

## Rotation Procedure

1. Generate a new signing key
2. Add it to GitHub as a *Signing key*
3. Update local Git configuration
4. Verify new commits are signed correctly
5. Remove the old signing key from GitHub

Old commits remain valid but may appear as *Unverified*
after key removal. This does not affect repository integrity.

---

## Security Notes

- Private keys must never be committed
- `allowed_signers` files are local-only
- Contributors are responsible for their own key management
