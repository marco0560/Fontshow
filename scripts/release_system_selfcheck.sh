#!/usr/bin/env bash
set -e

echo "== Release System Self-Check =="

FAIL=0

check() {
  if "$@"; then
    echo "OK: $*"
  else
    echo "FAIL: $*"
    FAIL=1
  fi
}

echo "[1] Checking hooks path..."
HOOKS=$(git config core.hooksPath)
[ "$HOOKS" = ".githooks" ] || { echo "FAIL: hooksPath not .githooks"; FAIL=1; }

echo "[2] Checking required scripts..."
for f in \
  scripts/release_audit.sh \
  scripts/tag_guard.sh \
  scripts/changelog_guard.sh
do
  [ -f "$f" ] || { echo "FAIL: missing $f"; FAIL=1; }
done

echo "[3] Checking pre-push hook exists..."
[ -f .githooks/pre-push ] || { echo "FAIL: missing pre-push"; FAIL=1; }

echo "[4] Checking release alias..."
git config alias.rel >/dev/null || { echo "FAIL: alias.rel missing"; FAIL=1; }

echo "[5] Checking history not rewritten..."
FIRST_TAG=$(git tag --sort=v:refname | head -1)
if [ -n "$FIRST_TAG" ]; then
  git merge-base --is-ancestor "$FIRST_TAG" HEAD || {
    echo "FAIL: history rewritten after first release"
    FAIL=1
  }
fi

echo "[6] Checking latest tag reachable..."
LATEST_TAG=$(git tag --merged HEAD --sort=-v:refname | head -1)
if [ -n "$LATEST_TAG" ]; then
  git merge-base --is-ancestor "$LATEST_TAG" HEAD || {
    echo "FAIL: latest tag not ancestor of HEAD"
    FAIL=1
  }
fi

echo "[7] Checking semantic-release baseline..."
npx semantic-release --dry-run >/dev/null 2>&1 || {
  echo "WARN: semantic-release dry-run failed"
}

if [ "$FAIL" -eq 0 ]; then
  echo "OK: release system consistent"
else
  echo "FAIL: release system inconsistent"
  exit 1
fi
