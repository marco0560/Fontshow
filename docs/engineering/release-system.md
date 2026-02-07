# Release System — Operational Documentation

## Purpose

This document describes the **Fontshow release safety system**, including:

* release workflow
* safety guards
* Git hooks
* semantic-release integration
* recovery procedures
* operational rules

This is the **source of truth** for release behavior.

---

## 1. Release Philosophy

The release system is designed to be:

* **Deterministic**
* **History-safe**
* **Tag-consistent**
* **semantic-release compatible**
* **Protected against human mistakes**
* **Protected against technical inconsistencies**

Key invariant:

> After the first release tag exists, history MUST NOT be rewritten.

---

## 2. Authorized Commands

### Normal development

```bash
git commit
```

### Safe release (ONLY allowed publish command)

```bash
git rel
```

Alias definition:

```bash
git config alias.rel '!SKIP_RELEASE_AUDIT=1 ALLOW_MAIN_PUSH=1 bash scripts/release_audit.sh && SKIP_RELEASE_AUDIT=1 ALLOW_MAIN_PUSH=1 git push'
```

### Forbidden (blocked by hooks)

```bash
git push
git safe-push
```

---

## 3. Release Workflow

When `git rel` is executed:

1. `release_audit.sh` runs
2. Verifies repository integrity
3. Push occurs
4. CI runs semantic-release
5. CI creates:

   * version tag
   * GitHub release
   * CHANGELOG update (if configured)
6. Developer runs:

```bash
git pull --ff-only
```

to realign local repo with CI release commit.

---

## 4. Safety Guards

### 4.1 release_audit.sh

Verifies:

* Working tree clean
* No rewritten history after first release
* Branch divergence
* Tag integrity (latest tag reachable from HEAD)
* CHANGELOG consistency
* semantic-release baseline
* Duplicate release detection

Failure = push blocked.

---

### 4.2 tag_guard.sh

Ensures:

* Latest semantic tag is ancestor of HEAD
* Prevents detached / rewritten release chains

---

### 4.3 changelog_guard.sh

Checks:

* No duplicated versions
* Top version matches latest tag
* Descending order
* Structural validity

---

### 4.4 Git pre-push hook

Blocks:

* Direct push to `main`
* Unsafe repository state
* Failing tests
* Failing lint
* Broken release baseline

Allows only:

```bash
git rel
```

via:

```bash
ALLOW_MAIN_PUSH=1
```

---

## 5. No-Rewrite Rule

Once **any tag exists**:

* ❌ No rebase on `main`
* ❌ No history rewrite
* ❌ No tag movement (except repair)
* ❌ No squash merge of published commits

Reason:

semantic-release relies on immutable history.

---

## 6. Tag Ownership

Tags are created by:

* CI / semantic-release (normal case)

Manual tag creation allowed **only for repair**.

---

## 7. Recovery Procedures

### 7.1 Broken tag not ancestor of HEAD

```bash
git tag -d vX.Y.Z
git tag vX.Y.Z HEAD
git push origin vX.Y.Z --force
git fetch --tags --force
```

---

### 7.2 Duplicate CHANGELOG block

Keep block matching real tag history.

Remove rebase artifacts.

---

### 7.3 semantic-release baseline drift

Recreate missing tag on correct commit.

---

### 7.4 Hook deadlock (emergency)

Temporary bypass:

```bash
git push --no-verify
```

Use **only for repair**, never normal workflow.

---

## 8. Stash Policy

Stash is safe for:

* local uncommitted work
* temporary pull protection

Not safe for:

* released state tracking
* versioning
* semantic-release history

Useful commands:

```bash
git stash push -m "msg"
git stash list
git stash apply
git stash drop
```

---

## 9. Determinism Guarantees

The system guarantees:

* No duplicate releases
* No orphan tags
* No tag drift
* No silent divergence
* No accidental push to main
* Reproducible release chain

---

## 10. Minimal Operational Checklist

Before release:

* Tests pass
* Ruff clean
* Working tree clean

Release:

```bash
git rel
git pull --ff-only
```

Done.

---

## 11. Future Maintenance

If modifying:

* hooks
* audit scripts
* tag logic
* release alias

Run full validation:

```bash
./scripts/release_audit.sh
npx semantic-release --dry-run
git rel
```

---

## 12. System Status

If this document matches repository behavior:

The release system is **STABLE**.

---

## 13. Release Flow — Logical Diagram

```text
Developer
   │
   │ git commit
   ▼
Local repository (clean state required)
   │
   │ git rel
   ▼
release_audit.sh
   │
   ├─ Check history not rewritten
   ├─ Check working tree clean
   ├─ Check divergence
   ├─ Check tag integrity
   ├─ Check CHANGELOG consistency
   └─ Check semantic-release baseline
   │
   ▼
Pre-push hook
   │
   ├─ Block direct push to main (unless ALLOW_MAIN_PUSH=1)
   ├─ Run release_audit (secondary safety)
   ├─ Run lint
   ├─ Run tests
   └─ Optional semantic-release dry-run
   │
   ▼
git push (authorized)
   │
   ▼
CI / GitHub Actions
   │
   ├─ semantic-release analyzes commits
   ├─ Determines next version
   ├─ Creates tag
   ├─ Updates CHANGELOG
   └─ Publishes GitHub Release
   │
   ▼
Developer
   │
   │ git pull --ff-only
   ▼
Local repo aligned with released state
```

---

## 14. Official Local Git Aliases

These aliases are **NOT versioned** and must be defined locally:

## Safe release (ONLY publish command)

```bash
git config alias.rel '!SKIP_RELEASE_AUDIT=1 ALLOW_MAIN_PUSH=1 bash scripts/release_audit.sh && SKIP_RELEASE_AUDIT=1 ALLOW_MAIN_PUSH=1 git push'
```

### Release audit (manual check)

```bash
git config alias.release-audit '!bash scripts/release_audit.sh'
```

### Safe fast-forward sync before work

```bash
git config alias.sync '!git fetch --tags --prune && git pull --ff-only'
```

### Emergency bypass (use only for repair)

```bash
git config alias.push-unsafe '!git push --no-verify'
```

---

## 15. Troubleshooting Decision Tree

### Push blocked

```text
Push blocked?
 ├─ Dirty working tree → commit or stash
 ├─ Branch diverged → git sync
 ├─ Tag not ancestor → repair tag
 ├─ CHANGELOG mismatch → fix ordering/version
 ├─ Tests failing → fix code
 ├─ Ruff failing → fix lint
 └─ Hook deadlock → use push-unsafe (repair only)
```

---

### semantic-release produced wrong version

```text
Wrong version?
 ├─ Missing tag → recreate tag on correct commit
 ├─ History rewritten → restore correct chain
 ├─ Duplicate CHANGELOG → remove rebase artifact
 └─ Wrong commit type → fix conventional commit usage
```

---

### "tag not ancestor of HEAD"

```bash
git tag -d vX.Y.Z
git tag vX.Y.Z <correct_commit>
git push origin vX.Y.Z --force
git fetch --tags --force
```

---

### Cannot push due to hook deadlock

Temporary:

```bash
git push --no-verify
```

Then repair:

* audit scripts
* tag consistency
* CHANGELOG
* release alias

---

## 16. Auto-Check: Documentation vs Real System

### Purpose of this check

Verify that:

* Hooks installed and correct
* Scripts present
* Alias configured
* Release invariant respected
* semantic-release chain valid

---

## Script — `release_system_selfcheck.sh`

Lives in `scripts/`. Use it to check the release system. It is not callad automatically

---

### Usage

Manual verification:

```bash
bash scripts/release_system_selfcheck.sh
```

Optional alias:

```bash
git config alias.release-check '!bash scripts/release_system_selfcheck.sh'
```

---

## 17. System Completeness Criteria

The release system is **fully stable** if:

* `git rel` works consistently
* `release_audit.sh` passes
* `release_system_selfcheck.sh` passes
* semantic-release dry-run produces no errors
* Tags form a continuous chain
* CHANGELOG matches tag history

---

## End of Extended Document
