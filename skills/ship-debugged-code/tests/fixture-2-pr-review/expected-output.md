# Expected Review Output — fixture-2-pr-review

---

## Debug Review: PR "Fix crash in dashboard"

### Critical (must fix before merge)

- **[D1-REPRO] PR description**: No reproduction case captured. "Some users" with no user ID, no Sentry link, no stack trace, no failing request. → Add to the PR body: the exact error message, the user/session ID that hit it, and a curl or test snippet that reproduces the crash on `main`. Without this, we cannot verify the fix actually addresses the failure.

- **[D2-SYMPTOM] renderDashboard()**: The fix treats `widgets` being falsy at the call site, but the bug is that *something passed undefined where an array was expected*. The producer is unknown. → Trace upstream: which caller is passing undefined? Likely candidates: `useWidgets()` returning before data loads, an API response without the `widgets` field, an error in the loader silently producing undefined. Fix at the source: ensure the caller passes `[]` not `undefined`, or refine the type signature so undefined is impossible.

- **[D4-TEST] PR**: No regression test added. → Add a test that fails without this change. Suggested: `renders empty state when widgets is undefined` (if we accept undefined as input), or — preferred — a test on the caller that proves the loader never returns undefined.

### Important (should fix)

- **[D3-LAYER] renderDashboard:1**: This component now accepts both `Widget[]` and `undefined`, weakening the type contract. → Strengthen the type: `widgets: Widget[]` (required, never undefined). Push the empty-vs-undefined distinction to the loader, which returns `[]` on no data and throws on error.

- **[D5-HYPOTHESIS] PR description**: No hypothesis about why `widgets` was undefined. "Some users" is not a hypothesis. → State the assumed cause: "I believe new users who haven't configured any widgets get `null` from the API instead of `[]`." Then verify against the actual data.

### Suggestions (improve when convenient)

- **[D7-DOC] Commit message "fix dashboard"**: Future engineers searching for "TypeError dashboard widgets" will not find this commit. → Rewrite: `Fix TypeError when widgets is undefined for new users. Cause: <root cause>. Fix at <layer>. Regression test: <file:line>.`

### What's Good

- The fix is minimal and reviewable as a single concept — easy to revert if the proper producer-side fix lands later.
- Falling back to `<EmptyState />` is reasonable UX once the data-flow issue is properly addressed; the visual outcome for users with no widgets makes sense.
