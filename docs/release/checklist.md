# Release Checklist

This document defines the **mandatory validation steps** required before
publishing a new Fontshow release.

It is intended to:

- enforce consistency across releases
- prevent regressions
- make the release process auditable and repeatable

This checklist is **process-level documentation**.
It does not define behavior and does not replace automated testing.

---

## 1. Preconditions

### 1.1 Repository state

- [ ] Working tree is clean (`git status`)
- [ ] Correct branch is checked out (usually `main`)
- [ ] No uncommitted or staged changes
- [ ] Version number updated where applicable
- [ ] No temporary debug code present

---

### 1.2 Versioning

- [ ] Version follows project versioning scheme
- [ ] Version bump matches scope of changes
- [ ] No accidental version drift across files

---

## 2. Verification (Technical)

### 2.1 Tests

- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] No skipped tests masking failures
- [ ] Test output reviewed for warnings

---

### 2.2 CLI verification

- [ ] All CLI commands execute without error
- [ ] Exit codes match documented behavior
- [ ] `--help` output is correct and readable
- [ ] No unexpected stdout/stderr output

---

### 2.3 Build & packaging

- [ ] Package builds successfully
- [ ] Entry points resolve correctly
- [ ] No missing or extra files in package
- [ ] Installation works in a clean environment

---

## 3. Validation (Semantic & Structural)

### 3.1 Output validation

- [ ] JSON output conforms to documented schema
- [ ] Required fields are always present
- [ ] No unexpected null or empty values

---

### 3.2 Compatibility

- [ ] No breaking changes introduced unintentionally
- [ ] CLI behavior unchanged unless explicitly documented
- [ ] Backward compatibility verified (where applicable)

---

### 3.3 Logging & diagnostics

- [ ] No unexpected warnings at default log level
- [ ] Structured logging remains valid
- [ ] Debug output does not leak into normal runs

---

## 4. Release Gate

A release **MUST NOT proceed** if any of the following is true:

- Any test is failing
- CLI behavior differs from documentation
- Output schema validation fails
- Known regressions are undocumented
- Required checks above are incomplete

---

## 5. Optional (Recommended)

- [ ] Manual test on at least one real system
- [ ] Review of recent commits for unintended changes
- [ ] Validation against previous release output
- [ ] Changelog reviewed for clarity

---

## 6. Notes

- This checklist is intentionally manual.
- Automation may be added later, but does not replace human validation.
- The checklist applies to **all releases**, including patch releases.
