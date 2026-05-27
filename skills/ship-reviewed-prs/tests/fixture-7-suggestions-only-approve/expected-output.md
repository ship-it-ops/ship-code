# Expected Review Output — fixture-7-suggestions-only-approve

The skill should APPROVE this docs-only PR with one P6 suggestion. Because the suggestion is a single, contiguous textual edit (convert a plain-prose path into a markdown hyperlink on the same line), it qualifies for both an inline comment and a `suggestion` fence. The summary body's "Suggestions" section becomes a pointer to that inline comment.

---

## Inline comments to post

### Inline comment 1 — SE6-LINK-ROT-RISK

```
path:        CONTRIBUTING.md
line:        108
suggestion:  yes
```

````markdown
**[SE6-LINK-ROT-RISK]** The reference to `plugins/ship-reviewed-prs/commands/review-pr.md`
is rendered as plain prose, not a markdown hyperlink. CI's relative-link checker
(`scripts/check-skill-links.py`) only scans `skills/**/*.md`, so this path won't be
validated if the file is renamed or moved.

```suggestion
See `plugins/ship-reviewed-prs/commands/review-pr.md` for the matching command.
```

(Adjust the surrounding prose if your line doesn't end in a period — the fence
replaces the entire line. Convert to a proper link to make it navigable in
rendered docs and give a future link-check script something to test.)
````

---

## Summary body (posted as the review body)

```
Posted by ship-reviewed-prs (bot). Reasoning available in this comment;
ask the author/oncall for human judgment on disputed findings.

---

## PR Review — #2200 `docs(contributing): add slash-command authoring guidance`

**Verdict: LGTM (with caveats)**

### Confidence
Reviewed CONTRIBUTING.md (+28 lines, 0 deletions) as a pure docs-only PR. SC ran a full pass for secret/URL leakage — clean. SE ran a technical-accuracy pass against the rest of the contributing guide. One P6 suggestion found. CI green. The verdict is `LGTM (with caveats)` because the lone finding is a Nit (advisory) and does not block the formal APPROVE per the updated decision matrix.

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ✅ active | docs technical-accuracy pass surfaced a link-rot Nit |
| SC | ✅ pass | no leaked secrets / URLs / env-var names |
| IN | ⏭ skip | docs-only PR |
| DA | ⏭ skip | docs-only PR |
| FE | ⏭ skip | docs-only PR |
| TS | ⏭ skip | docs-only PR |

### Findings

| Severity | Count | Inline anchors |
|---|---|---|
| Must-fix | 0 | — |
| Should-fix | 0 | — |
| Nits | 1 | `SE6 CONTRIBUTING.md:108` |

### Delegations

- (none)

### Comment lifecycle

| State | Count |
|---|---|
| Resolved | 0 |
| Won't-fix | 0 |
| Outdated | 0 |
| Possibly addressed | 0 |
| Stale | 0 |
| Open | 0 |

Suppressed 0 findings already discussed in earlier review.

### What's solid

- The PR description names the downstream incident that motivated this section, which gives the docs immediate operational grounding for future plugin authors.
- The `disable-model-invocation: true` → `commands/` mandatory connection is a non-obvious invariant; capturing it here is exactly the kind of thing that prevents future repeats of the original bug.
- Single-file, additive, low-risk change with a clear blast radius.
```

---

## CI mode submission

Exit code: `0` (APPROVE). The review is submitted via the pending-review protocol because there is one inline comment:

```
gh api -X POST .../pulls/2200/reviews                 → REVIEW_ID
gh api -X POST .../reviews/$REVIEW_ID/comments × 1    (one inline at CONTRIBUTING.md:108, with suggestion fence)
gh api -X POST .../reviews/$REVIEW_ID/events
  -f event=APPROVE -f body=<summary with disclosure prefix>
```

## What this fixture demonstrates

1. **Nits do not block LGTM** — the updated matrix treats P6/P7 (Nits) as advisory and demotes the friendly verdict to `LGTM (with caveats)` rather than degrading the formal decision to COMMENT.
2. **Nit-tier findings still get inline anchors when they're mechanical** — SE6 here is a single-line textual edit (plain prose → markdown link) so it qualifies for both the inline comment and the `suggestion` fence. Nit-tier findings that require an adjacent edit (a new import, a multi-step refactor) live in the Findings table count but not in the anchors column.
3. **"Awaiting CI" caveat is absent** because CI is green; caveat sections are only emitted when their condition holds.
4. **LGTM (with caveats) + inline findings uses the pending-review protocol** — not the simpler `gh pr review --approve --body` form (that's reserved for zero-inline APPROVEs per reference.md §6).
5. **`--auto-approve` would NOT have been honored here** even on a green-path APPROVE, because Nit findings exist; the local user would have been prompted to confirm submit.
6. **Exit code 0** in CI mode — downstream gating sees a clean pass; the Nit is a body-only signal.
