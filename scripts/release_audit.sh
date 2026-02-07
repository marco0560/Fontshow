#!/usr/bin/env bash
set -euo pipefail

echo "== Release Audit =="

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
echo "[2] Checking divergence..."

if git rev-parse --abbrev-ref @{u} >/dev/null 2>&1; then
  LOCAL=$(git rev-parse @)
  REMOTE=$(git rev-parse @{u})
  BASE=$(git merge-base @ @{u})

  if [ "$LOCAL" != "$REMOTE" ]; then
    if [ "$LOCAL" = "$BASE" ]; then
      echo "ERROR: branch behind remote"
      exit 1
    elif [ "$REMOTE" = "$BASE" ]; then
      echo "ERROR: branch ahead without push"
      exit 1
    else
      echo "ERROR: branch diverged"
      exit 1
    fi
  fi
else
  echo "WARN: no upstream configured — skipping divergence check"
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
