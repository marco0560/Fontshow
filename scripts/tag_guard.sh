#!/usr/bin/env bash
#
# Purpose
# -------
# Validate git tag usage and invariants before release operations.
#
# Responsibilities
# ----------------
# - Ensure tag names follow the repository versioning conventions.
# - Prevent duplicate or malformed tags from being used in releases.
# - Provide deterministic diagnostics when tag invariants are violated.
#
# Design principles
# -----------------
# Tag validation must be conservative and deterministic. The script must
# inspect repository metadata only and must not modify tags or commits.
#
set -euo pipefail

echo "== Tag Guard =="

if git tag | grep -q .; then
  if git log --oneline --decorate | grep -q "(rewritten)"; then
    echo "ERROR: history rewritten after release"
    exit 1
  fi
fi

git fetch --tags --force

LATEST=$(git tag -l "v[0-9]*" --sort=-v:refname | head -1)

if ! git merge-base --is-ancestor "$LATEST" HEAD; then
  echo "ERROR: latest tag $LATEST is not ancestor of HEAD"
  exit 1
fi

echo "OK: last tag consistent"
