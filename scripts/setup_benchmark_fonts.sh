#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/setup_benchmark_fonts.sh [light|heavy]

Generate on-demand benchmark font fixtures under tests/fixtures/fonts_dir.

Profiles:
  light    Download the pinned OFL-safe fixture subset.
  heavy    Download the light subset and add replicated stress fixtures.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

PROFILE="${1:-light}"
if [[ "${PROFILE}" != "light" && "${PROFILE}" != "heavy" ]]; then
  usage >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FONT_DIR="${REPO_ROOT}/tests/fixtures/fonts_dir"
HEAVY_DIR="${FONT_DIR}/.heavy"

mkdir -p "${FONT_DIR}"

sha256_file() {
  python - "$1" <<'PY'
import hashlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
digest = hashlib.sha256(path.read_bytes()).hexdigest()
print(digest)
PY
}

download_file() {
  local output="$1"
  local url="$2"
  local expected_sha="$3"
  local target="${FONT_DIR}/${output}"
  local tmp="${target}.tmp"

  if [[ -f "${target}" ]]; then
    actual_sha="$(sha256_file "${target}")"
    if [[ "${actual_sha}" == "${expected_sha}" ]]; then
      printf 'ok: %s already present\n' "${output}"
      return 0
    fi
    printf 'warning: checksum mismatch for %s; re-downloading\n' "${output}" >&2
    rm -f "${target}"
  fi

  python - "${url}" "${tmp}" <<'PY'
import sys
from pathlib import Path
from urllib.request import urlopen

url = sys.argv[1]
target = Path(sys.argv[2])
with urlopen(url, timeout=60) as response:
    target.write_bytes(response.read())
PY

  actual_sha="$(sha256_file "${tmp}")"
  if [[ "${actual_sha}" != "${expected_sha}" ]]; then
    rm -f "${tmp}"
    printf 'error: checksum mismatch for %s\n' "${output}" >&2
    printf 'expected: %s\nactual:   %s\n' "${expected_sha}" "${actual_sha}" >&2
    exit 1
  fi

  mv "${tmp}" "${target}"
  printf 'downloaded: %s\n' "${output}"
}

download_file \
  "Roboto.ttf" \
  "https://raw.githubusercontent.com/google/fonts/47831f08ec6d6d7ad6b465f23dc9f9a890a2a04b/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf" \
  "d7598e12c5dbef095ff8272cfc55da0250bd07fbdecbac8a530b9b277872a134"
download_file \
  "Roboto-Italic.ttf" \
  "https://raw.githubusercontent.com/google/fonts/47831f08ec6d6d7ad6b465f23dc9f9a890a2a04b/ofl/roboto/Roboto-Italic%5Bwdth%2Cwght%5D.ttf" \
  "9725a847af6b460ffca162ae66d20dad48b01876137947180b42d7dcd7887182"
download_file \
  "OpenSans.ttf" \
  "https://raw.githubusercontent.com/google/fonts/47831f08ec6d6d7ad6b465f23dc9f9a890a2a04b/ofl/opensans/OpenSans%5Bwdth%2Cwght%5D.ttf" \
  "36643644f318a812aab2d2ed3bb98f8cf0872527f835fe9398d95fe6b9adb878"
download_file \
  "NotoSans.ttf" \
  "https://raw.githubusercontent.com/google/fonts/47831f08ec6d6d7ad6b465f23dc9f9a890a2a04b/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf" \
  "bfb7bb691513f12e734dc346c03a03f784912432d7e3fa8e56efcf906fe86b3d"
download_file \
  "NotoSerif.ttf" \
  "https://raw.githubusercontent.com/google/fonts/47831f08ec6d6d7ad6b465f23dc9f9a890a2a04b/ofl/notoserif/NotoSerif%5Bwdth%2Cwght%5D.ttf" \
  "4d8e6761424656867019081a1a01336f3cb086982682698714054fc33f782713"
download_file \
  "Lato-Regular.ttf" \
  "https://raw.githubusercontent.com/google/fonts/47831f08ec6d6d7ad6b465f23dc9f9a890a2a04b/ofl/lato/Lato-Regular.ttf" \
  "d636e4683231f931eda222d588e944d082bfd3bdba02f928bee461c0f185b251"
download_file \
  "SourceCodePro.ttf" \
  "https://raw.githubusercontent.com/google/fonts/47831f08ec6d6d7ad6b465f23dc9f9a890a2a04b/ofl/sourcecodepro/SourceCodePro%5Bwght%5D.ttf" \
  "b400fc584e10aff25d0e775ce181b4fc1c5ea1b5dc37b81aeb2084375b945790"
download_file \
  "Inconsolata.ttf" \
  "https://raw.githubusercontent.com/google/fonts/47831f08ec6d6d7ad6b465f23dc9f9a890a2a04b/ofl/inconsolata/Inconsolata%5Bwdth%2Cwght%5D.ttf" \
  "23ded25b447074d00659392bf9b1123d89df55cb07b0ad9bfef3366d199b5fcb"

rm -rf "${HEAVY_DIR}"

if [[ "${PROFILE}" == "heavy" ]]; then
  mkdir -p "${HEAVY_DIR}"
  for copy_index in $(seq -w 1 8); do
    copy_dir="${HEAVY_DIR}/copy-${copy_index}"
    mkdir -p "${copy_dir}"
    for font_path in "${FONT_DIR}"/*.ttf; do
      cp "${font_path}" "${copy_dir}/${copy_index}-$(basename "${font_path}")"
    done
  done
fi

printf 'benchmark font fixture ready: %s (%s)\n' "${FONT_DIR}" "${PROFILE}"
