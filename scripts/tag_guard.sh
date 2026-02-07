#!/usr/bin/env bash
set -e

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
