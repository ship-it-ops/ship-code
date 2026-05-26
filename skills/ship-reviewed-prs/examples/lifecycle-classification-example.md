# Lifecycle Classification Example

Worked example showing all six lifecycle states (RESOLVED, OUTDATED, WONT_FIX, ADDRESSED, STALE, OPEN) on a single long-lived PR, and how the skill's suppression behavior responds.

---

## The PR

**PR #2840: "Refactor billing service to support multi-currency"**

- Opened 6 weeks ago
- 47 commits
- 23 review threads total (5 commenters)
- Last commit 2 days ago
- CI: green

The PR is mid-refactor and has accumulated comment history that any new review must respect.

---

## The 23 review threads — classified

### Thread 1 — RESOLVED

- Author: Alice (maintainer), 5 weeks ago
- Path: `services/billing.ts:42`
- Body: "This casts the amount to int — won't this lose precision on cents?"
- Reply from PR author: "Fixed in 8a3f1c2, switched to bigint."
- State on GitHub: marked resolved by Alice
- GraphQL `isResolved`: **true**

**Classification: RESOLVED**

**Skill behavior:** Suppress any new finding fingerprinting to `(services/billing.ts, ~42, TYPE_PRECISION)`. Count in lifecycle line.

---

### Thread 2 — OUTDATED

- Author: Bob (maintainer), 4 weeks ago
- Path: `services/billing.ts:88` (line at the time)
- Body: "This function is missing error handling for the gateway timeout case."
- No reply
- State on GitHub: thread shown as "Outdated"
- GraphQL `isOutdated`: **true** (the function was rewritten in commit 12b4e6f and line 88 no longer exists)

**Classification: OUTDATED**

**Skill behavior:** Suppress any new finding fingerprinting to that path/line. Count in lifecycle line. If the new function (in the same area) has its own timeout problem, that fires as a fresh finding with a different fingerprint.

---

### Thread 3 — WONT_FIX (explicit marker)

- Author: Carol (maintainer), 3 weeks ago
- Path: `services/currency-converter.ts:14`
- Body: "Should this support cryptocurrency conversions?"
- Reply from PR author: "Out of scope for this PR — tracked in #2901."
- State on GitHub: open
- `isResolved`: false, `isOutdated`: false

**Classification: WONT_FIX**

The last comment from the PR author contains the marker `out of scope` and a tracking reference `#2901`.

**Skill behavior:** Suppress any new finding about cryptocurrency support in `currency-converter.ts`. Count in lifecycle line.

---

### Thread 4 — WONT_FIX (reaction marker)

- Author: Dave (collaborator), 2 weeks ago
- Path: `services/billing.ts:130`
- Body: "Consider renaming `convert` to `convertAmount` for clarity."
- Reply from PR author: "I'd rather keep the shorter name; the context makes it clear."
- Dave reacted with `:white_check_mark:` to the author's reply.
- `isResolved`: false (Dave forgot to click "Resolve thread")

**Classification: WONT_FIX**

The reaction from the original commenter (Dave) on the author's reply is the marker, even though the thread wasn't formally resolved.

**Skill behavior:** Suppress any new naming-related finding on that function. Note: this finding would have been a delegation to `ship-clean-code` anyway, so this is mostly for the suppression count.

---

### Thread 5 — ADDRESSED (heuristic)

- Author: Eve (member), 10 days ago
- Path: `services/payments.ts:55` (original_line)
- Body: "This needs a timeout — `fetch` without `signal` will hang."
- Reply from PR author: "Will fix."
- State on GitHub: open
- Subsequent commits: yes — commit `f1a2b3c` (8 days ago) touched `services/payments.ts` lines 50-58.

**Classification: ADDRESSED**

The post-comment commit touched the path within `original_line ± 5`. The skill doesn't *know* if the fix actually addresses the concern, but the spatial evidence is strong.

**Skill behavior:** Surface in the "Possibly addressed — needs reviewer confirmation" section. Do NOT re-raise the original concern. Mark the PR ineligible for APPROVE — degrade to COMMENT regardless of other findings.

In the output:
```
### Possibly addressed — needs reviewer confirmation
- Thread on services/payments.ts:55 (Eve, 10 days ago — "needs a timeout") was followed by commit f1a2b3c which touched lines 50-58. Eve should re-check and resolve the thread if the concern is addressed.
```

---

### Thread 6 — STALE

- Author: Frank (collaborator), 18 days ago
- Path: `services/auth.ts:30`
- Body: "Should we add logging here for failed auth attempts?"
- No reply, no commits to `services/auth.ts` since.
- `isResolved`: false, `isOutdated`: false
- Last activity 18 days ago, exceeds 14-day stale threshold.

**Classification: STALE**

**Skill behavior:** Surface in the "Stale comments needing reply" section. Don't block the decision matrix; don't suppress; remind the author to engage.

In the output:
```
### Stale comments needing reply
- services/auth.ts:30 (Frank, 18 days ago — "logging for failed auth attempts?")
```

---

### Threads 7–22 — OPEN

Sixteen recent threads with active back-and-forth in the last 14 days. Each is its own concern. Most have an OPEN state.

**Skill behavior:** Each thread fingerprint is compared against new candidate findings. If a new finding matches, the new finding is dropped and the open thread is noted as "still active". If a new finding doesn't match any open thread, it's emitted fresh.

Result: of the 16 OPEN threads, the skill matches 12 to candidate findings (suppressed as "already raised — see thread"), and 4 are flagged as still needing author response.

---

### Thread 23 — OPEN, but matches a critical new finding

- Author: Grace (member), 3 days ago
- Path: `api/admin/billing.ts:88`
- Body: "Is this endpoint behind auth? I don't see it."
- No reply.
- `isResolved`: false, `isOutdated`: false
- New finding from SC persona: SC1-AUTH-MISSING at the same path/line.

**Classification: OPEN**

**Skill behavior:** Match found. Suppress the new SC1 finding from the output (don't re-raise). Add to "still active threads needing author response" with the original framing.

```
### Open threads (still need author response)
- api/admin/billing.ts:88 (Grace, 3 days ago — "Is this endpoint behind auth?") — matches SC1-AUTH-MISSING from new scan. The original framing is correct; awaiting author action.
```

The SC1 finding still counts toward the decision matrix because it's the same blocking concern, just framed by Grace originally rather than by the skill. **Decision: REQUEST_CHANGES** (or whatever the SC1 logic dictates).

---

## Summary lifecycle line in the output

```
### Comment lifecycle
- 1 resolved | 1 outdated | 2 won't-fix | 1 possibly addressed (please confirm) | 1 stale | 17 open (12 match new candidate findings — suppressed as duplicates; 4 need author response; 1 raises SC1-AUTH-MISSING which is the actual blocker)
- Suppressed: 14 findings already discussed in earlier review.
```

The 14 suppressed = 1 (Thread 1 match) + 1 (Thread 4 match) + 12 (Threads 7-22 matches) = 14. The threads that don't match candidate findings (3, 5, 6, 23) and the OUTDATED thread don't contribute to suppression counts (they're noted in their own sections).

---

## The decision

- `critical_count`: 1 (SC1, from the surface that matches Thread 23 — still counts because it's an active concern)
- `important_count`: 4 (from the open threads still needing response)
- `possibly_addressed_count`: 1 (Thread 5)
- `ci_state`: green

Matrix: any unsuppressed *1 finding → REQUEST_CHANGES.

```
### Decision: 🛑 REQUEST_CHANGES

### Confidence
Reviewed a long-lived PR with 23 existing threads and 47 commits. Aggressive lifecycle suppression applied — 14 candidate findings were dropped as duplicates of existing threads. The one critical finding (SC1-AUTH-MISSING on api/admin/billing.ts) matches Thread 23 from Grace; the same concern is the actual blocker. Confirming addressed items (Thread 5) and engaging with stale Thread 6 would clear the path; the SC1 fix is the critical action.
```

---

## What this example demonstrates

1. **All six lifecycle states** present in one PR, classified deterministically before any finding generation.
2. **Suppression is aggressive** on long-lived PRs — 14 dropped findings is normal, not pathological.
3. **Critical findings are not suppressed by thread-matching** — Thread 23 matches SC1 but the finding still counts toward the decision (it's a real, active blocker; matching just means the framing is reused).
4. **ADDRESSED downgrades to COMMENT** if there are no other critical findings — the skill never auto-approves over an unconfirmed "possibly fixed" item.
5. **STALE doesn't block the decision** but is surfaced for the author.
6. **Lifecycle line is concise but informative** — the reviewer can scan it in 5 seconds and understand the state of the PR's review history.
