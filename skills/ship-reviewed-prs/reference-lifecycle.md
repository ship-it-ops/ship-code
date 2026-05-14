# Comment Lifecycle Reference

The single most important behavior in this skill is **not re-raising findings that have already been discussed**. This file documents the six-state classification, fingerprinting, and override knobs in detail.

---

## 1. Six-State Classification

Every review thread on the PR falls into exactly one state. Compute deterministically before any LLM judgment.

### RESOLVED

- **Definition**: GraphQL `reviewThread.isResolved == true`. The reviewer (or author with permissions) explicitly marked the thread resolved on GitHub.
- **Behavior**: Suppress matching findings. Mention by count in the lifecycle line.
- **Why**: A resolved thread is a closed loop. Re-raising is a clear regression in behavior.

### OUTDATED

- **Definition**: GraphQL `reviewThread.isOutdated == true`. The line the comment was attached to no longer exists in the current diff.
- **Behavior**: Suppress matching findings. Mention by count.
- **Why**: The original comment may or may not have been "fixed", but the surface it referred to is gone. The new finding either (a) doesn't apply because the code changed, or (b) is a new finding at a different location and should be raised independently.

### WONT_FIX

- **Definition**: An open thread (not resolved, not outdated) where the **last** comment from the PR author OR a maintainer matches a won't-fix marker.

  **Default marker set** (case-insensitive substring match — these are literal substrings, NOT regex; the algorithm is `marker.lower() in comment_body.lower()`):
  - `won't fix`, `wontfix`, `won't address`
  - `out of scope`, `out-of-scope`, `out of scope for this pr`, `not in this pr`
  - `tracked in #`, `tracking in #`, `see #`, `filed as #` (the trailing `#` is enough — `tracked in #5001` substring-matches `tracked in #`)
  - `agreed to skip`, `discussed offline`, `discussed on slack`, `discussed sync`
  - `follow-up pr`, `follow-up ticket`, `follow-up issue`, `next pr`, `separate pr` (NOTE: bare `follow-up` is intentionally excluded — a comment like "pushed a follow-up commit" should NOT classify as won't-fix because the author is claiming the concern was addressed, not deferred. The marker must reference a *separate work item*.)
  - `as discussed`, `per discussion`
  - **Reaction marker**: a `:white_check_mark:` or `:thumbsup:` (👍) reaction from the *original commenter* on the author's response

  "Maintainer" is determined via GraphQL `authorAssociation` of `OWNER`, `MEMBER`, or `COLLABORATOR`. Tunable via `overrides.md` (`maintainer_associations`).

- **Behavior**: Suppress matching findings. Mention by count.
- **Why**: The team has explicitly decided not to address this. Re-raising it is rude and shows the skill isn't reading.

### ADDRESSED

- **Definition**: An open thread (not resolved, not WONT_FIX) where the author has pushed a commit after the comment's `createdAt` that touches the comment's `path` near `original_line ± 5`.

  **Lookup**:
  1. List commits on the PR via `gh pr view <n> --json commits`.
  2. For each commit after the comment's `createdAt`, run `gh api repos/.../commits/{sha}` to get the per-file patch.
  3. For files matching the comment's `path`, check if any patch hunk overlaps `original_line ± 5`.

- **Behavior**: Surface as a special bucket "Possibly addressed — needs reviewer confirmation". Do NOT re-derive the original concern. Do NOT count as suppression (the human still needs to verify and either resolve or push back).
- **Why**: Better than re-raising a comment that's likely been fixed, but lighter than fully suppressing — the heuristic is fuzzy and the original reviewer should confirm.
- **Decision-matrix impact**: Any `ADDRESSED` count > 0 prevents APPROVE — the skill degrades to COMMENT with the explanation "Confirm addressed items to escalate."

### STALE

- **Definition**: An open thread (not resolved, not WONT_FIX, not ADDRESSED) where the last activity (comment, push, reaction) is older than 14 days AND the author has not responded since the comment was made.
- **Behavior**: Surface in a separate "Stale comments needing reply" section. Don't suppress — these need human attention. Don't block the decision matrix on stale alone (it's the reviewer's call).
- **Why**: Old comments without author response usually mean the comment was forgotten. Surfacing them helps the author re-engage without re-raising the finding fresh.
- **Tunable**: `stale_threshold_days` in `overrides.md` (default 14).

### OPEN

- **Definition**: Everything else. Open thread, not resolved, not WONT_FIX, not ADDRESSED, not STALE.
- **Behavior**: Blocking. Counts toward `open_thread_count` in the decision matrix.
- **Why**: An active, recent, unresolved thread is by definition still in discussion. The skill should not approve over an open thread.

---

## 2. Classification Algorithm (Pseudocode)

```
for thread in pr.review_threads:
    if thread.isResolved:
        state = RESOLVED
    elif thread.isOutdated and not line_in_current_diff(thread.path, thread.line):
        state = OUTDATED
    elif matches_wont_fix_marker(thread):
        state = WONT_FIX
    elif addressed_by_later_commit(thread):
        state = ADDRESSED
    elif (now - thread.last_activity).days > stale_threshold and not author_replied_since(thread):
        state = STALE
    else:
        state = OPEN

    thread.lifecycle_state = state
```

`matches_wont_fix_marker`:
```
original_commenter = thread.comments[0].author
last_relevant_comment = last comment whose author is the PR author OR a maintainer

# Critical: never let the original commenter mark their own concern as won't-fix.
# This guard must run BEFORE the body-marker check, otherwise a maintainer who
# opened the thread and then commented "follow-up" or "out of scope" in the same
# thread (a common pattern when the same person is reviewing several adjacent
# concerns and decides one is out of scope) would auto-suppress their own
# valid finding.
if last_relevant_comment.author == original_commenter:
    return False

if any marker in last_relevant_comment.body (case-insensitive substring):
    return True
if has_reaction(original_commenter, [white_check_mark, thumbsup], on=last_relevant_comment):
    return True
return False
```

`addressed_by_later_commit`:
```
for commit in pr.commits:
    if commit.committed_date <= thread.created_at:
        continue
    patch = fetch_commit_patch(commit.sha)
    for file_patch in patch.files:
        if file_patch.path != thread.path:
            continue
        for hunk in file_patch.hunks:
            if overlaps(hunk.line_range, thread.original_line, window=5):
                return True
return False
```

---

## 3. Finding Suppression — Fingerprinting

Once threads are classified, suppress new findings that match existing closed threads.

### Fingerprint

```
fingerprint(finding) = (
    finding.path,
    floor(finding.line / 5),
    finding.root_cause_token,
)
```

`root_cause_token` is a canonical short identifier for the *category* of finding. Examples:
- `MISSING_AUTH`
- `SQL_INJECTION`
- `XSS`
- `HARDCODED_SECRET`
- `NO_TIMEOUT`
- `BLOCKING_MIGRATION`
- `BACKFILL_MISSING`
- `NO_INDEX`
- `LOG_LEAK`
- `BREAKING_CHANGE`
- `MISSING_TEST`
- `MISSING_REGRESSION_TEST`

The token list is closed — the prompt enforces it. Personas pick from this list rather than inventing tokens at runtime, so dedup is deterministic.

### Suppression check

Suppression applies to RESOLVED / OUTDATED / WONT_FIX (drop silently, count
toward `suppressed_findings`) AND to OPEN (drop from new-finding list, surface
the existing thread under "Open threads (still need author response)", and still
let the underlying concern count toward the decision matrix because it remains
unresolved).

```
suppressed_count = 0
matched_open_threads = []   # OPEN threads that match a new candidate finding
for finding in candidate_findings:
    fp = fingerprint(finding)
    for thread in pr.review_threads:
        thread_fp = thread_fingerprint(thread)
        if not matches(fp, thread_fp):
            continue
        if thread.lifecycle_state in (RESOLVED, OUTDATED, WONT_FIX):
            # Closed-loop suppression: the team has decided. Drop silently.
            suppressed_count += 1
            drop(finding)
            break
        if thread.lifecycle_state == OPEN:
            # Active suppression: don't re-raise, but the concern is still real.
            # The decision matrix sees the finding's priority via the OPEN thread.
            matched_open_threads.append((thread, finding.priority_id))
            drop(finding)
            break
        # ADDRESSED and STALE threads do NOT suppress new findings; the rendered
        # output handles them in their own sections (Possibly addressed / Stale).
```

`thread_fingerprint` extracts the path, line, and a categorized root-cause token from the thread's comments. Since old threads weren't generated by this skill, the categorization is fuzzier — use keyword matching on the comment body.

The matched OPEN threads are rendered in the "Open threads (still need author response)" output section with their original framing — never re-stated in our voice — and the priority IDs we matched against are listed so the decision matrix can still gate on `*1`/`*2` severities (see `reference.md` §5).

### Why path+line±5+category, not exact match?

- Lines drift as the diff evolves. A comment on line 42 may now be on line 47.
- A finding that's about the same category in the same neighborhood IS the same finding for review purposes.
- Going broader than ±5 starts dropping legitimate independent findings.

The ±5 window is tunable via `overrides.md` (`fingerprint_line_window`).

---

## 4. Long-Lived PR Handling

For PRs with ≥ 50 comments OR ≥ 30 commits, suppression becomes load-bearing.

### Adjustments

- **Path-only fingerprinting fallback**: when there are > 30 threads on a file, drop the `line` component of the fingerprint for that file. The diff has shifted too much to trust line-based matching.
- **Lead with the lifecycle line**: move the lifecycle summary above the Confidence section in the output. The reviewer needs to see "12 resolved, 5 won't-fix" before any new finding.
- **Aggressive suppression**: prefer false-negative over false-positive in dedup. If unsure whether a candidate finding matches an existing thread, suppress and add to the suppressed count. The reviewer can ask for a re-review with `--verbose` if they think a finding was wrongly dropped.

---

## 5. Edge Cases

### Bot-authored comments

If a thread's only commenter is a bot (e.g., Dependabot, CodeQL, `ship-reviewed-prs` from a prior CI run), don't apply maintainer logic to it. A bot can't grant won't-fix.

### Suggested changes that were committed

GitHub's "commit suggestion" feature creates a commit from a review comment. Detect via commit message `Apply suggestion from <user>`. Mark the source thread as ADDRESSED automatically.

### Re-opened threads

A re-opened thread looks identical to any other OPEN thread in the snapshot
the skill fetches (the documented GraphQL query exposes only the *current*
`isResolved` value, not the timeline of resolves/un-resolves). The skill
therefore does **not** treat re-opened threads specially — it cannot
distinguish them from threads that have always been open.

If you re-open a thread because earlier markers no longer apply, leave a fresh
comment restating the concern. The skill's classification operates on the
latest comment from the PR author or a maintainer, so a new comment without a
won't-fix marker forces the thread back into OPEN/STALE handling and the
suppression algorithm respects the updated state. Implementations that need
proper re-open detection must fetch `reviewThread.timelineItems` and reduce
events to a resolution history; this is left as a future enhancement.

### Forced-pushed branches

A force-push can rewrite history; commit lookup for ADDRESSED becomes unreliable for commits before the force-push. Fall back to: if any of the post-comment commits has the same `committedDate` as the head, assume ADDRESSED detection is degraded and surface uncertainty in the output.

### Pull request from a fork

GraphQL access is the same. Inline comment posting via `gh api` works as long as the token has write access to the base repo. CI bot tokens generally do; default `GITHUB_TOKEN` in GitHub Actions does for PRs from same-repo branches, may not for fork PRs (depends on workflow `pull_request_target` vs `pull_request`). Document in `examples/ci-github-actions.yml`.

---

## 6. Override Knobs

All of the following are configurable via `overrides.md`. Defaults shown:

```yaml
stale_threshold_days: 14
fingerprint_line_window: 5
maintainer_associations: [OWNER, MEMBER, COLLABORATOR]

wont_fix_markers:
  - "won't fix"
  - "wontfix"
  - "won't address"
  - "out of scope"
  - "out-of-scope"
  - "not in this pr"
  - "tracked in #"
  - "tracking in #"
  - "see #"
  - "filed as #"
  - "agreed to skip"
  - "discussed offline"
  - "next pr"
  - "follow-up pr"
  - "follow-up ticket"
  - "follow-up issue"
  - "separate pr"
  - "as discussed"
  - "per discussion"
  # Note: bare "follow-up" intentionally NOT in the default set — too broad,
  # would catch innocent author replies like "pushed a follow-up commit".
  # Teams that want it can add it explicitly.

wont_fix_reactions: [white_check_mark, thumbsup]

# When > N threads exist on a single file, drop line-based fingerprinting:
path_only_threshold: 30

# When > N comments OR commits, treat as long-lived:
long_lived_comment_threshold: 50
long_lived_commit_threshold: 30
```

Format is `key: value` or `key: [list]`. The skill reads `overrides.md` as plain text and pattern-matches these keys; no YAML parser required.

---

## 7. Worked Examples

See `examples/lifecycle-classification-example.md` for a worked end-to-end demonstration of all six states on a single PR.
