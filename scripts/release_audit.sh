#!/usr/bin/env bash
#
# Purpose
# -------
# Audit repository release readiness before a push or release operation.
#
# Responsibilities
# ----------------
# - Enforce release-history and tag ancestry invariants.
# - Verify repository cleanliness and release-policy preconditions.
# - Fail fast with deterministic diagnostics when release conditions are not
#   satisfied.
#
# Design principles
# -----------------
# This audit must be conservative and non-destructive. It performs only
# validation checks and exits on first failure so unsafe release workflows are
# blocked before mutating repository state.
#
set -euo pipefail

# allow semantic-release to bypass audit
if [ "${SKIP_RELEASE_AUDIT:-0}" = "1" ]; then
  exit 0
fi

echo "== Release Audit =="

########################################
# [0] History check
########################################
echo "[0] Checking history not rewritten after first release..."

  FIRST_TAG=$(git tag --sort=v:refname | grep -E '^v[0-9]+.[0-9]+.[0-9]+$' | head -1 || true)

if [ -n "$FIRST_TAG" ]; then
  if ! git merge-base --is-ancestor "$FIRST_TAG" HEAD; then
    echo "ERROR: history rewritten after first release (rebase detected)"
    exit 1
  fi
fi

########################################
# [1] Working tree must be clean
########################################
echo "[1] Checking working tree clean..."
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: dirty working tree"
  exit 1
fi

########################################
# [2] Branch must not be diverged
# (NO fetch here — pre-push safe)
########################################
echo "[3] Checking divergence..."
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
BASE=$(git merge-base @ @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "OK: branch aligned"
elif [ "$LOCAL" = "$BASE" ]; then
  echo "ERROR: branch behind remote"
  exit 1
elif [ "$REMOTE" = "$BASE" ]; then
  echo "OK: branch ahead (push expected)"
else
  echo "ERROR: branch diverged"
  exit 1
fi

########################################
# Skip release checks outside main
########################################
BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [[ "$BRANCH" != "main" ]]; then
  echo "Release audit skipped on branch $BRANCH"
  exit 0
fi

########################################
# [3] Tag integrity (semantic-release safe)
# Only consider tags reachable from HEAD
########################################
echo "[3] Checking tag integrity..."

LATEST_TAG=$(
  git tag --merged HEAD \
  | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' \
  | sort -V \
  | tail -1
)

if [ -z "${LATEST_TAG:-}" ]; then
  echo "WARN: no semantic version tag reachable from HEAD"
else
  if git merge-base --is-ancestor "$LATEST_TAG" HEAD; then
    echo "OK: last tag consistent ($LATEST_TAG)"
  else
    echo "ERROR: tag $LATEST_TAG is not ancestor of HEAD"
    exit 1
  fi
fi

########################################
# [4] Changelog guard
########################################
echo "[4] Running changelog guard..."
bash scripts/changelog_guard.sh

########################################
# [5] Semantic-release baseline
########################################
echo "[5] Checking semantic-release baseline..."

if [ -n "${LATEST_TAG:-}" ]; then
  COMMITS=$(git rev-list "$LATEST_TAG"..HEAD --count)
else
  COMMITS=$(git rev-list HEAD --count)
fi

echo "Commits since last release: $COMMITS"

########################################
# [6] Duplicate release commit detection
# (non-blocking informational)
########################################
echo "[6] Checking duplicate release commits..."

DUP=$(git log --oneline --grep '^chore(release):' | wc -l | tr -d ' ')
echo "Release commits in history: $DUP"

########################################
# Done
########################################
echo "OK: release baseline valid"
