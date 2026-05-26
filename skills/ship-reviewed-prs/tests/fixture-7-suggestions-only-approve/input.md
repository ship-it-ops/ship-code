# Synthetic PR Input for Fixture 7: Suggestions-Only APPROVE

You are reviewing a small docs PR that contains exactly one cosmetic concern — a path reference written as inline prose rather than a markdown hyperlink. Under the relaxed decision matrix, suggestion-only findings produce APPROVE with a "Suggestions" caveat, not COMMENT.

## PR metadata

```json
{
  "owner": "acme",
  "repo": "platform",
  "number": 2200,
  "title": "docs(contributing): add slash-command authoring guidance",
  "body": "Documents the layout required when a plugin needs an explicit slash command in addition to a skill. Closes a documentation gap that surfaced when a downstream CI integration ran for ~5 minutes producing no review.",
  "headRefName": "docs/slash-command-guidance",
  "baseRefName": "main",
  "author": "renee",
  "isDraft": false,
  "labels": ["docs"],
  "files": [
    {"path": "CONTRIBUTING.md", "additions": 28, "deletions": 0}
  ],
  "statusCheckRollup": {"state": "SUCCESS"},
  "commits": [
    {"sha": "aaa111", "committedDate": "2026-05-25T22:30:00Z"}
  ]
}
```

## Diff (gh pr diff — relevant region)

```diff
diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
@@ -100,6 +100,28 @@ Plugin version MUST match between `plugins/<name>/.claude-plugin/plugin.json` an

+### Slash Commands (optional)
+
+If you want users to invoke a skill explicitly with `/<name>`, you also need
+a slash command file under `plugins/<name>/commands/<name>.md`. Skills
+marked `disable-model-invocation: true` are only reachable that way.
+
+For skills that require mode detection or subagent orchestration, the
+minimal one-line body is not enough — an LLM handed only that sparse body
+may attempt to inline-implement the skill instead of loading it. See
+plugins/ship-reviewed-prs/commands/review-pr.md for a complete template
+that passes arguments through verbatim and invokes the skill via the
+Skill tool.
+
 ## Validation
```

## Review threads (gh api graphql)

```json
{
  "reviewThreads": []
}
```

## CI checks

All green. No checks pending or failing.

## Invocation flags

The user invoked the skill in CI mode (`CI=true`). No `--auto-approve`, no `--strict`.

---

Run the multi-persona PR review. Expected outcome:

- The reference to `plugins/ship-reviewed-prs/commands/review-pr.md` is rendered as plain prose, not a markdown link. The CI relative-link checker only scans `skills/**/*.md`, so this path will not be validated if the file is renamed or moved. → P6 (Suggestion) — `SE6-LINK-ROT-RISK`.
- No Critical or Important findings. No "Possibly addressed" items. CI green.
- Per the decision matrix, the verdict is **APPROVE** with a "Suggestions (improve when convenient)" caveat listing the single P6.
- The "Awaiting CI" caveat is **absent** (CI green, no pending checks).
- In CI mode, the bot disclosure prefix appears before the review body, and the review is submitted as an `APPROVE` event via the gh pending-review protocol (because there is one inline comment — the suggestion).
