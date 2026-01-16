#!/usr/bin/env bash
set -euo pipefail

DECISIONS_DIR="${DECISIONS_DIR:-docs/decisions}"

if [[ ! -d "$DECISIONS_DIR" ]]; then
  echo "ERROR: decisions directory not found: $DECISIONS_DIR" >&2
  exit 1
fi

# -------------------------------------------------------------------
# 1. Date
# -------------------------------------------------------------------
TODAY="$(date +%Y-%m-%d)"

# -------------------------------------------------------------------
# 2. Compute next decision number
# -------------------------------------------------------------------
LAST_NUM="$(
  ls "$DECISIONS_DIR"/*.md 2>/dev/null \
  | sed -E 's#.*/([0-9]+)-.*\.md#\1#' \
  | sort -n \
  | tail -n 1
)"

if [[ -z "${LAST_NUM:-}" ]]; then
  NEXT_NUM=1
else
  NEXT_NUM=$((LAST_NUM + 1))
fi

read -r -p "Decision number [$NEXT_NUM]: " NUM
NUM="${NUM:-$NEXT_NUM}"

# -------------------------------------------------------------------
# 3. One-line description → TITLE
# -------------------------------------------------------------------
read -r -p "One-line description: " DESCRIPTION

if [[ -z "$DESCRIPTION" ]]; then
  echo "ERROR: description cannot be empty" >&2
  exit 1
fi

# Normalize title:
# - lowercase
# - trim
# - collapse spaces
# - replace spaces with dashes
# - drop empty fragments
TITLE="$(
  echo "$DESCRIPTION" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E '
      s/^[[:space:]]+//;
      s/[[:space:]]+$//;
      s/[[:space:]]+/ /g;
      s/ /-/g
    '
)"

FILENAME="${NUM}-${TITLE}.md"
TARGET="$DECISIONS_DIR/$FILENAME"

# -------------------------------------------------------------------
# 4. Create decision file
# -------------------------------------------------------------------
if [[ -e "$TARGET" ]]; then
  echo "ERROR: file already exists: $TARGET" >&2
  exit 1
fi

cat >"$TARGET" <<EOF
# ${NUM} - ${DESCRIPTION}

## Status

**Status:** Accepted
**Date:** ${TODAY}


## Context
<Insert context>

## Decision
<Insert decision>

## Consequences
<Insert consequences>
EOF

echo "Decision created: $TARGET"

# -------------------------------------------------------------------
# 5. Update decisions index (fail hard + rollback)
# -------------------------------------------------------------------
INDEX_FILE="$DECISIONS_DIR/index.md"

if [[ ! -f "$INDEX_FILE" ]]; then
  echo "ERROR: index file not found: $INDEX_FILE" >&2
  echo "Rolling back decision file creation." >&2
  rm -f "$TARGET"
  exit 1
fi

echo "- [$NUM — $DESCRIPTION]($FILENAME)" >> "$INDEX_FILE"

echo
echo "Decision created:"
echo "  $TARGET"
echo "Index updated:"
echo "  $INDEX_FILE"
