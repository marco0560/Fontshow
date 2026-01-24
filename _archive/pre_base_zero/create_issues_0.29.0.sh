#!/usr/bin/env bash
# Archived after base-zero planning (v0.28.7.post14)

set -euo pipefail

REPO="marco0560/Fontshow"
MILESTONE="0.29.0"

gh issue create \
  --repo "$REPO" \
  --title "Finalize dual-field language strategy (raw vs normalized)" \
  --label "c5.x,stabilization,schema,languages" \
  --milestone "$MILESTONE" \
  --body "$(cat <<'EOF'
## Scope
- Complete separation between raw Fontconfig language tags and normalized ISO 639 languages
- Preserve raw data verbatim
- Normalize ISO 639 codes in a dedicated field
- Update schema, validation rules, and documentation

## Acceptance Criteria
- Gentoo pipeline runs without excessive validation noise
- Raw language tags preserved
- Schema remains compliant

## Notes
Completes the C5.3 design already documented in decisions.md.
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "Charset vs fontTools coverage consistency diagnostics (logging-only)" \
  --label "c5.x,stabilization,logging,charset" \
  --milestone "$MILESTONE" \
  --body "$(cat <<'EOF'
## Scope
- Diagnostic-only comparison between charset-derived and fontTools-derived coverage
- Structured logging only
- No inventory mutation

## Acceptance Criteria
- Diagnostics emitted only when both sources are present
- Suppressible via log level
- No schema or semantic changes

## Notes
Corresponds to C5.2 and is intentionally observability-only.
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "Close documented gaps between logging specification and implementation" \
  --label "c5.x,techdebt,logging,docs" \
  --milestone "$MILESTONE" \
  --body "$(cat <<'EOF'
## Scope
- Audit logging matrices in decisions.md
- Track implemented vs missing vs deferred messages
- Align code and documentation incrementally

## Acceptance Criteria
- Every documented message is implemented or explicitly deferred
- No undocumented discrepancies remain

## Notes
Process-oriented technical debt issue.
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "Improve JSON readability for charset-derived numeric arrays" \
  --label "c5.x,stabilization,ux" \
  --milestone "$MILESTONE" \
  --body "$(cat <<'EOF'
## Scope
- Compact formatting for short numeric arrays
- Localized to formatting/serialization layer
- No semantic changes

## Acceptance Criteria
- Improved readability
- Schema remains valid

## Notes
Purely cosmetic improvement.
EOF
)"
