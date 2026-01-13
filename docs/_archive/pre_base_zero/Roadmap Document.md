# Archived after base-zero planning (v0.28.7.post14)

# Fontshow Technical Roadmap

## Current status

- Version: 0.28.7.post9
- Focus: Stabilization, observability, and explicit contracts

## Guiding principles

- Observability before enrichment
- Explicit contracts over implicit behavior
- Platform differences are documented, not hidden
- Incremental, reviewable evolution

## Near-term (0.29.x – 0.31.x)

### Stabilization
- Dual-field language strategy
- Warning and logging contract finalization
- JSON readability improvements

### Testing & Validation
- Formal coverage strategy
- Platform-dependent test separation
- Gentoo-specific evidence

### CLI & Preflight UX
- Documented exit code policy
- Machine-readable outputs
- Public preflight APIs

## Mid-term (0.32.x – 0.33.x)

### Controlled Feature Evolution
- Charset-aware enrichment
- Explicit precedence rules
- Explainable inference

### Governance
- decisions.md external review
- Contributor onboarding improvements
- Public roadmap alignment

## Long-term (2.x)

### Architecture
- Pluggable font discovery backends
- Explicit environment support matrix

### Sustainability
- Stable public APIs
- Predictable schema evolution
- Reproducible testing across platforms

## Non-goals

- Silent behavioral changes
- Undocumented inference heuristics
- Platform-specific hacks without evidence

---

This roadmap is intentionally conservative and contract-driven.
