# Expected Review Output — fixture-7-suggestions-only-approve

```
Posted by ship-reviewed-prs (bot). Reasoning available in this comment;
ask the author/oncall for human judgment on disputed findings.

---

## PR Review: #2200 — docs(contributing): add slash-command authoring guidance

### Decision: APPROVE

### Confidence
Reviewed CONTRIBUTING.md (+28 lines, 0 deletions) as a pure docs-only PR. SC ran a full pass for secret/URL leakage — clean. SE ran a technical-accuracy pass against the rest of the contributing guide. IN/DA/FE/TS did not activate. One P6 suggestion found. CI green. APPROVE with a Suggestions caveat — the finding is advisory and does not block the verdict per the updated decision matrix.

### Critical (must fix before merge)

- (none)

### Important (should fix)

- (none)

### Suggestions (improve when convenient)

- **[SE6-LINK-ROT-RISK] CONTRIBUTING.md:108**: The reference to `plugins/ship-reviewed-prs/commands/review-pr.md` is rendered as plain prose, not a markdown hyperlink. CI's relative-link checker (`scripts/check-skill-links.py`) only scans `skills/**/*.md`, so this path won't be validated if the file is renamed or moved. → Convert to a proper link: `[review-pr.md](plugins/ship-reviewed-prs/commands/review-pr.md)` — makes it navigable in rendered docs and gives a future link-check script something to test.

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

## CI mode submission

Exit code: `0` (APPROVE). The review is submitted via the pending-review protocol because there is one inline comment:

```
gh api -X POST .../pulls/2200/reviews                 → REVIEW_ID
gh api -X POST .../reviews/$REVIEW_ID/comments × 1    (one inline at CONTRIBUTING.md:108)
gh api -X POST .../reviews/$REVIEW_ID/events
  -f event=APPROVE -f body=<summary with disclosure prefix>
```

## What this fixture demonstrates

1. **Suggestions do not block APPROVE** — the updated matrix treats P6/P7 as advisory caveats inside the APPROVE body rather than verdict downgrades.
2. **"Suggestions (improve when convenient)" caveat is populated** when `suggestion_count > 0`, listing each finding with the same format as a COMMENT-decision suggestion.
3. **"Awaiting CI" caveat is absent** because CI is green; caveat sections are only emitted when their condition holds.
4. **APPROVE with inline findings uses the pending-review protocol** — not the simpler `gh pr review --approve --body` form (that's reserved for inline-less APPROVEs per reference.md §6).
5. **`--auto-approve` would NOT have been honored here** even on a green-path APPROVE, because suggestion findings exist; the local user would have been prompted to confirm submit.
6. **Exit code 0** in CI mode — downstream gating sees a clean pass; the suggestion is a body-only signal.
