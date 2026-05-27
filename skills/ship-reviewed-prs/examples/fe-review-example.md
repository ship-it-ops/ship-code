# FE Review Example

End-to-end demonstration of the FE persona engaged on a React/TypeScript design-system PR. Shows FE1/FE2/FE3 firing as Critical, FE5 as Important, FE7 as a Suggestion, plus an SC3 catch on an accidentally-committed runtime lockfile.

This example is derived from a real-world miss the skill had on a graph-editor PR before the FE persona existed — the bugs are textbook FE shapes and are reproduced here as a regression anchor.

---

## Source PR (summarized)

**PR #47: "Add support for graph editing"** in the design-system monorepo.

**Body:**
> Adds a new `GraphEditorCanvas` (React Flow-based editor) to `@ship-it-ui/graph-editor`, an `InlineEdit` primitive in `@ship-it-ui/ui`, and extracts a shared `@ship-it-ui/graph-tokens` package from `@ship-it-ui/cytoscape`.

**Files (representative slice; full diff is +3753 / -346 over 56 files):**

- `packages/graph-editor/src/GraphEditorCanvas.tsx` (new, ~400 lines)
- `packages/graph-editor/src/MiniMap.tsx` (new, ~110 lines)
- `packages/ui/src/components/InlineEdit/InlineEdit.tsx` (new, ~250 lines)
- `packages/ui/src/components/InlineEdit/InlineEdit.test.tsx` (new, axe checks for display + edit modes only)
- `.changeset/add-graph-editor-canvas.md` (new)
- `.claude/scheduled_tasks.lock` (new, ephemeral runtime artifact)

**Existing review threads:** none.

**CI status:** all green.

---

## Review Output (what the skill produces)

```
## PR Review — #47 `Add support for graph editing`

**Verdict: Changes requested**

### Confidence
Reviewed 56 files (compressed: 8 representative TSX, 1 changeset, 1 lockfile, plus passing-context files). SC scanned the diff; flagged one SC3 on the committed lockfile. CI is green. Zero existing review threads. The verdict is `Changes requested` because the FE persona produced three *1-tier findings — an ARIA contract break and two state-management bugs that make undo/redo unusable in the controlled-elements pattern the docs themselves demonstrate.

Generated/vendored skipped: 1 (`pnpm-lock.yaml`).

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ✅ pass | no PR-shaped contract concerns beyond the FE-owned ones below |
| SC | ✅ active | committed runtime lock file (SC3) |
| IN | ✅ pass | IN-light — no infra files touched |
| DA | ⏭ skip | no schema/migration touched |
| FE | ✅ active | TSX-heavy diff, new aria-* attributes, global-CSS import in non-entry module |
| TS | ✅ pass | tests added alongside production code; ratio within TS1 threshold |

### Findings

| Severity   | Count |
|---|---|
| Must-fix   | 5 |
| Should-fix | 2 |
| Nits       | 1 |

**Must-fix anchors:**
- `FE1` packages/ui/src/components/InlineEdit/InlineEdit.tsx:234 — see inline comment
- `FE2` packages/graph-editor/src/GraphEditorCanvas.tsx:175 — see inline comment
- `FE2` packages/graph-editor/src/GraphEditorCanvas.tsx:231 — see inline comment
- `FE3` packages/graph-editor/src/GraphEditorCanvas.tsx:387 — see inline comment
- `FE3` packages/graph-editor/src/GraphEditorCanvas.tsx:397 — see inline comment

**Should-fix anchors:**
- `FE5` packages/graph-editor/src/GraphEditorCanvas.tsx:34 — see inline comment
- `SC3` .claude/scheduled_tasks.lock:1 — see inline comment

**Nit anchors:**
- `FE7` .changeset/add-graph-editor-canvas.md:7 — see inline comment (with `suggestion` fence)

(Each anchor maps to an inline comment with the full finding body and proposed fix — see "Inline comments to post" above.)

### Comment lifecycle

| State | Count |
|---|---|
| Resolved | 0 |
| Won't-fix | 0 |
| Outdated | 0 |
| Possibly addressed | 0 |
| Stale | 0 |
| Open | 0 |

Suppressed 0 findings.

### What's solid

- **Token extraction is clean**: `resolveColorReference` and friends moved intact from `@ship-it-ui/cytoscape` to the new `@ship-it-ui/graph-tokens` package with their full test suites; the cytoscape package re-exports the same surface verbatim, so existing consumers see zero behavior change. This is the textbook way to extract a shared dependency.
- **`useHistory` uses refs, not state**: pushing a command doesn't trigger a render. The `useMemo` wrapper on the return object keeps effect deps stable. `inverseOf(delete-node)` correctly restores incident edges via a `batch` command. The history primitive itself is solid; the issues above are about how it's wired up in `GraphEditorCanvas`, not the primitive.
- **Keyboard guard at the canvas root**: `INPUT`, `TEXTAREA`, and `contentEditable` targets short-circuit the keyboard handler before any canvas binding fires. An `<InlineEdit>` inside a custom node can type, commit, and cancel without accidentally triggering Delete or arrow-nudge on the host canvas. Correct guard placement.
- **`aria-errormessage` intent is right**: the wiring (`aria-invalid` + `aria-errormessage` + validation state) is the correct ARIA pattern; only the missing DOM target needs to be added.
- **Changesets are well-described elsewhere**: each of the other three changesets has a substantive body explaining what shipped and why. The FE7 finding above is on the one outlier.

### Submission preview (local mode only)
  gh api -X POST repos/ship-it-ops/ship-it-design/pulls/47/reviews (create pending review)
  gh api -X POST .../reviews/${REVIEW_ID}/comments × 8 (one per Must-fix anchor + Should-fix anchor + FE7 Nit; FE7 includes a `suggestion` fence since the fix is a single-file changeset-body rewrite)
  gh api -X POST .../reviews/${REVIEW_ID}/events -f event=REQUEST_CHANGES -f body="<this entire output as the summary, with the Submission preview block stripped>"

Proceed? Type "yes" to submit, "edit" to revise the body, "no" to abort.
```

---

## What this example demonstrates

1. **FE engages on a TSX-heavy PR** even though SE alone would have caught only the lock file (SC3) and missed the FE-shaped state/contract bugs. Without FE, the original review of this PR posted 3 findings; with FE, it posts 7 findings substantively comparable to a senior FE engineer's review.
2. **FE2 wins over SE2 in dedup**: the controlled-state desync at line 175 would otherwise fingerprint as a generic SE2-CONTRACT-DRIFT. FE2 framing ("undo unusable in the controlled-elements pattern the docs themselves demonstrate") is more actionable.
3. **Critical tier is reserved for *1 findings** (FE1, FE2, FE3). FE5 is *2 (Important). FE7 is *4 (Suggestions). The decision matrix doesn't negotiate — five *1 findings drive REQUEST_CHANGES on first sight.
4. **SC still catches the lockfile** — SC isn't replaced by FE; they cover different concerns. SC3 fires on the `.claude/scheduled_tasks.lock` because it matches the "committed runtime/lock-file artifact" sub-pattern of SECRET-LEAK.
5. **"What's solid" is substantive and frontend-flavored** — token extraction, history primitive correctness, keyboard guard placement, ARIA intent. These observations help the author trust the criticism: the reviewer engaged with the design, not just hunted for problems.
6. **Delegation is mentioned without firing TS1**: the axe-test gap is too specific to merit TS1 (TS1 is purely "no tests added"), but the FE persona's adjacent-test-file read surfaces it as a delegation pointer in prose.
