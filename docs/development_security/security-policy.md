# Security and Commit Policy

## Scope
This document defines the security model enforced by this repository.

## Principles
- Local tooling is advisory
- The server is authoritative
- History must be immutable

## Commit Signing
- All commits to protected branches must be signed
- SSH-based signing is required
- Unsigned commits are rejected by the server

## Branch Protection
- `main` is a protected branch
- Force-push is forbidden
- History rewriting is not allowed

## Local Hooks
- Local hooks are helpers only
- They may be bypassed
- They do not grant permission to push invalid commits

## Continuous Integration
- CI is the final authority
- CI checks are mandatory
- CI may reject commits regardless of local state

## Contributors
- Contributors must configure commit signing
- Key rotation is the contributor’s responsibility
- See `key-rotation.md`
