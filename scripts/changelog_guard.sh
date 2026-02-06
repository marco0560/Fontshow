#!/usr/bin/env bash
set -euo pipefail

echo "== Changelog Guard =="

FILE="CHANGELOG.md"

[ -f "$FILE" ] || { echo "ERROR: CHANGELOG.md missing"; exit 1; }

echo "[1] Checking duplicate version blocks..."

DUP=$(grep -E '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' "$FILE" \
      | sed -E 's/^## \[([0-9]+\.[0-9]+\.[0-9]+)\].*/\1/' \
      | sort | uniq -d)

if [ -n "$DUP" ]; then
    echo "ERROR: duplicate CHANGELOG versions detected:"
    echo "$DUP"
    exit 1
fi

echo "[2] Checking newest version matches latest tag..."

LATEST_TAG=$(git tag --sort=-creatordate | head -1 | sed 's/^v//')
TOP_CHANGELOG=$(grep -m1 -E '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' "$FILE" \
                | sed -E 's/^## \[([0-9]+\.[0-9]+\.[0-9]+)\].*/\1/')

if [ "$LATEST_TAG" != "$TOP_CHANGELOG" ]; then
    echo "ERROR: top CHANGELOG version ($TOP_CHANGELOG) != latest tag ($LATEST_TAG)"
    exit 1
fi

echo "[3] Checking ordering (descending)..."

PREV=""
grep -E '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' "$FILE" \
| sed -E 's/^## \[([0-9]+\.[0-9]+\.[0-9]+)\].*/\1/' \
| while read -r v; do
    if [ -n "$PREV" ]; then
        if [ "$(printf "%s\n%s\n" "$PREV" "$v" | sort -V | tail -1)" != "$PREV" ]; then
            echo "ERROR: CHANGELOG not in descending order at $PREV -> $v"
            exit 1
        fi
    fi
    PREV="$v"
done

echo "OK: CHANGELOG consistent"
