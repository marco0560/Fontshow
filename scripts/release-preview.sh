#!/usr/bin/env bash
set -euo pipefail

echo "[release-preview] Semantic release dry-run"

if ! command -v npx >/dev/null 2>&1; then
  echo "ERROR: npx not found"
  exit 1
fi

if ! npm list --depth=0 semantic-release >/dev/null 2>&1; then
  echo "ERROR: semantic-release not installed locally"
  echo "Hint: npm install --save-dev semantic-release"
  exit 1
fi

npx semantic-release \
  --dry-run \
  --config .releaserc.local.json

echo "[release-preview] Done"
