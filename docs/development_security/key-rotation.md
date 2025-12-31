# SSH Key Rotation Policy

This project uses **SSH-based commit signing**.

To maintain a high security level, contributors and maintainers
must follow the key rotation policy described below.

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
