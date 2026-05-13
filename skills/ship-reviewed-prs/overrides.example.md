# PR Review Overrides — Example

Copy this file to `overrides.md` (next to `SKILL.md`) or to `.claude/ship-reviewed-prs-overrides.md` in your project root, then edit. Anything documented here supersedes the defaults in `SKILL.md`, `reference.md`, and `reference-lifecycle.md`.

> The skill loader reads override files in this order, with later files winning:
> 1. `SKILL.md` defaults
> 2. `overrides.md` (next to `SKILL.md`, team-wide)
> 3. `.claude/ship-reviewed-prs-overrides.md` in the project root (project-specific)

Format is loose `key: value` or `key: [list]`. The skill reads override files as plain text and pattern-matches keys; no YAML parser required.

---

## Comment lifecycle tuning

```
stale_threshold_days: 21
fingerprint_line_window: 7
maintainer_associations: [OWNER, MEMBER, COLLABORATOR]
```

### Won't-fix markers

Default set is in `reference-lifecycle.md` §6. Add team-specific phrases here:

```
wont_fix_markers:
  - "punt"
  - "next sprint"
  - "agreed with @alice"
  - "not blocking"
  - "deferred to v2"
```

### Won't-fix reactions

```
wont_fix_reactions: [white_check_mark, thumbsup, eyes]
```

---

## Persona configuration

### Disable a persona entirely

For repos that have no DB and no schema concerns:

```
disable: [DA]
```

For repos that have no IaC and no operational concerns (rare — usually IN-light is still valuable):

```
disable: [IN-deep]
```

### Custom conditional triggers

Add to the file-pattern lists that activate DA or IN-deep:

```
da_trigger_paths:
  - "src/db/"
  - "data/contracts/"
  - "shared/events/"

in_deep_trigger_paths:
  - "deploy/"
  - "infra-terraform/"
  - "platform-cdk/"
```

### Severity adjustments

Escalate or demote specific finding IDs for your context:

```
escalate: [SC5]      # treat SC5 as a *1 finding (REQUEST_CHANGES) — we are paranoid about supply chain
demote: [SE7]        # SE7 (docstring mismatch) is suggestions-only for us; treat as P6
```

---

## CI behavior

### Cap CI submission decision

The most useful CI override. Caps the action the skill will submit; the exit code still reflects original severity.

```
ci_max_decision: COMMENT
```

Other valid values: `REQUEST_CHANGES`, `APPROVE`. Default is no cap (full matrix honored).

### Bot identity prefix

Customize the disclosure line prepended to CI-submitted reviews:

```
ci_bot_identity_prefix: |
  Posted by ship-reviewed-prs (automated review).
  For nuanced judgment on disputed findings, ask oncall in #eng-oncall
  or the author directly. This bot's findings are advisory unless
  marked Critical.
```

### Strict mode for CI

By default, COMMENT exits `2` (non-blocking). With `ci_strict_mode: true`, COMMENT exits `1` too — same as `--strict` flag.

```
ci_strict_mode: false
```

---

## Skipping patterns

### Additional generated-file patterns

```
generated_paths:
  - "*.generated.ts"
  - "*_pb2.py"
  - "openapi-types.ts"
  - "src/types/api-generated.d.ts"
```

### Additional vendored-file patterns

```
vendor_paths:
  - "third_party/"
  - "external/"
  - "src/vendor/"
```

### Path-only fingerprinting threshold (long-lived PRs)

```
path_only_threshold: 20    # default: 30
long_lived_comment_threshold: 30    # default: 50
long_lived_commit_threshold: 15     # default: 30
```

---

## TS persona thresholds

```
ts1_min_added_lines: 50    # default: 30 — TS1 only fires above this threshold
```

For repos where small additions don't warrant tests (e.g., one-liner config glue), raise this.

---

## Custom domain rules

Team-specific concerns that don't fit the default rubric. These are appended to the relevant persona's prompt.

```
custom_rules:
  - persona: SC
    rule: "Any new endpoint under /api/internal/ must have @InternalOnly annotation. Flag missing as SC1."
  - persona: SE
    rule: "Any PR touching src/billing/ must reference a JIRA ticket in the description. Flag missing as SE3 (rollout risk)."
  - persona: DA
    rule: "Migrations touching the events table require sign-off from @data-team in the PR. Flag missing as DA1."
```

---

## Repository conventions

```
public_api_paths:
  - "src/sdk/"
  - "packages/api/src/"
  - "src/lib/public/"
```

These paths are treated as public API surface — SE persona is stricter about breaking changes here.

```
allow_force_push: false
```

If `true`, the skill treats force-pushes as expected and is more lenient on ADDRESSED detection. If `false`, force-pushes trigger a "history changed — review state may be stale" warning.

---

## Disabled rules (granular)

```
disable_finding_ids:
  - SE7    # we don't care about docstring mismatches
  - IN5    # CI changes are reviewed elsewhere
```

The skill still computes these but never emits them. Useful when an entire finding category is handled by another tool (e.g., a dedicated GitHub Action does CI-pipeline auditing).
