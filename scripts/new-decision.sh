#!/usr/bin/env bash
set -euo pipefail

DECISIONS_DIR="docs/decisions"
INDEX_FILE="$DECISIONS_DIR/index.md"

read -rp "Decision number (e.g. 0004): " NUM
read -rp "Decision short title: " TITLE
read -rp "One-line description: " DESC

FILENAME="${NUM}-${TITLE// /-}.md"
FILEPATH="$DECISIONS_DIR/$FILENAME"

if [[ -e "$FILEPATH" ]]; then
  echo "ERROR: decision file already exists"
  exit 1
fi

cat > "$FILEPATH" <<EOF
# Decision $NUM — $TITLE

## Status

**Status:** Proposed
**Date:** <Insert date>

## Context

$DESC

## Decision

## Consequences
EOF

# Append to index.md
echo "- [$NUM — $TITLE]($FILENAME)" >> "$INDEX_FILE"

echo "Decision created:"
echo "  $FILEPATH"
echo "Index updated:"
echo "  $INDEX_FILE"
