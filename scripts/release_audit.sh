#!/usr/bin/env bash
set -e

echo "== Release Audit =="

echo "[1] Checking working tree clean..."
git diff --quiet || { echo "ERROR: dirty working tree"; exit 1; }

echo "[2] Checking divergence..."
git fetch --tags --force

echo "[2b] Running tag integrity guard..."
bash scripts/tag_guard.sh

echo "[2c] Running changelog guard..."
bash scripts/changelog_guard.sh

echo "[3] Checking divergence..."
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

echo "[4] Checking tag integrity..."
LATEST_TAG=$(git tag --sort=-creatordate | head -1)
if ! git merge-base --is-ancestor "$LATEST_TAG" HEAD; then
  echo "ERROR: latest tag not ancestor of HEAD"
  exit 1
fi

echo "[5] Checking semantic-release baseline..."
COMMITS=$(git rev-list "$LATEST_TAG"..HEAD --count)
echo "Commits since last release: $COMMITS"

echo "[6] Checking duplicate release tags..."
DUP=$(git log --oneline | grep -c "chore(release)")
echo "Release commits in history: $DUP"

echo "OK: release baseline valid"
