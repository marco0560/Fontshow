#!/usr/bin/env bash
set -euo pipefail

echo "== Fontshow Gentoo CLI test =="

FONTSHOW=fontshow
WORKDIR="$(mktemp -d)"
OUT_JSON="$WORKDIR/inventory.json"
OUT_JSON2="$WORKDIR/inventory_enriched.json"

cleanup() {
  rm -rf "$WORKDIR"
}
trap cleanup EXIT

run() {
  echo
  echo ">> $*"
  "$@"
  rc=$?
  echo "exit code=$rc"
  return $rc
}

# ------------------------------------------------------------
echo "1) Help and version"
run $FONTSHOW -h
run $FONTSHOW -V

# ------------------------------------------------------------
echo "2) Preflight"
run $FONTSHOW preflight

# ------------------------------------------------------------
echo "3) Dump fonts"
run $FONTSHOW dump-fonts -o "$OUT_JSON"

test -s "$OUT_JSON" || {
  echo "ERROR: inventory.json not created"
  exit 1
}

# ------------------------------------------------------------
echo "4) Parse inventory"
run $FONTSHOW parse-inventory "$OUT_JSON" -o "$OUT_JSON2"

test -s "$OUT_JSON2" || {
  echo "ERROR: enriched inventory not created"
  exit 1
}

# ------------------------------------------------------------
echo "5) Validate inventory"
run fontshow-validate "$OUT_JSON2"

# ------------------------------------------------------------
echo
echo "All Fontshow Gentoo tests PASSED"
