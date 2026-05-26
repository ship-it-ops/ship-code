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

## PR Review: #2200 — docs(contributing): add slash-command authoring guidance

### Decision: ✅ APPROVE

### Confidence
Reviewed CONTRIBUTING.md (+28 lines, 0 deletions) as a pure docs-only PR. SC ran a full pass for secret/URL leakage — clean. SE ran a technical-accuracy pass against the rest of the contributing guide. IN/DA/FE/TS did not activate. One P6 suggestion found. CI green. APPROVE with a Suggestions caveat — the finding is advisory and does not block the verdict per the updated decision matrix.

### Critical (must fix before merge)

- (none)

### Important (should fix)

- (none)

### Suggestions (improve when convenient)

- **[SE6-LINK-ROT-RISK]** CONTRIBUTING.md:108 — *see inline comment* (suggestion attached)

### Delegations

- (none)

### Comment lifecycle

- 0 resolved | 0 outdated | 0 won't-fix | 0 possibly addressed | 0 stale | 0 open
- Suppressed: 0 findings already discussed in earlier review.

### What's Good

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

1. **Suggestions do not block APPROVE** — the updated matrix treats P6/P7 as advisory caveats inside the APPROVE body rather than verdict downgrades.
2. **Suggestion-tier findings post inline when they're mechanical** — SE6 here is a single-line textual edit (plain prose → markdown link) so it qualifies for both the inline comment and the `suggestion` fence. Suggestion-tier findings that require an adjacent edit (a new import, a multi-step refactor) stay in the summary body's Suggestions section instead.
3. **"Awaiting CI" caveat is absent** because CI is green; caveat sections are only emitted when their condition holds.
4. **APPROVE with inline findings uses the pending-review protocol** — not the simpler `gh pr review --approve --body` form (that's reserved for zero-inline APPROVEs per reference.md §6).
5. **`--auto-approve` would NOT have been honored here** even on a green-path APPROVE, because suggestion findings exist; the local user would have been prompted to confirm submit.
6. **Exit code 0** in CI mode — downstream gating sees a clean pass; the suggestion is a body-only signal.
