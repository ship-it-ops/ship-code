# Expected Review Output — fixture-5-frontend-pr

The skill should produce a report substantially matching the structure below. The Critical FE1/FE2/FE3 findings and the REQUEST_CHANGES decision are non-negotiable; wording details can vary.

Each finding is annotated with `# Copilot finding #N` to cross-check coverage against the original 10 missed findings. Target: 10/10 catch rate after FE persona is fully wired up. Pre-FE baseline: 2/10 (only #3 aria-errormessage and the lock file were caught).

> **Format note (v1.2+):** Under the inline-first protocol every Critical and Important finding below should be posted as an inline review comment on the cited `file:line`. The summary body bullets are reduced to `[FINDING-ID] file:line — see inline comment`. A handful qualify for a `suggestion` fence — notably **FE5-SSR-GLOBAL-CSS** (delete the offending `import './styles.css'` line; one-line deletion qualifies) and the **InlineEdit FE4-NO-OP-PROP-VALUE** if the chosen resolution is "remove `'focus'` from the union" (single-line type edit). The FE1/FE2/FE3 findings on `GraphEditorCanvas.tsx` require multi-line refactors and stay as prose. The full finding text below is what should appear in the inline-comment bodies.

---

```
## PR Review — #47 `Add support for graph editing`

**Verdict: Changes requested**

### Confidence
Reviewed 29 files (compressed diff of 56 changed files; pnpm-lock.yaml skipped as generated). SC scanned all files; flagged one SC3 on `.claude/scheduled_tasks.lock`. CI is green. Zero existing review threads. The verdict is `Changes requested` because FE produced five *1-tier findings on the GraphEditorCanvas state-management surface plus an ARIA contract break in InlineEdit.

Generated/vendored skipped: 1 (pnpm-lock.yaml).

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ✅ pass | FE owns the TSX-shaped concerns; no PR-shaped contract drift |
| SC | ✅ active | committed runtime lock file (SC3) |
| IN | ✅ pass | IN-light — no infra files touched |
| DA | ⏭ skip | no schema/migration touched |
| FE | ✅ active | TSX-heavy diff, new aria-* attributes, global-CSS import in non-entry module |
| TS | ✅ pass | tests added alongside production code; ratio within TS1 threshold |

### Findings

| Severity   | Count |
|---|---|
| Must-fix   | 7 |
| Should-fix | 4 |
| Nits       | 1 |

**Must-fix anchors:**
- `FE1` packages/ui/src/components/InlineEdit/InlineEdit.tsx:234 — see inline comment
- `FE1` packages/ui/src/components/InlineEdit/InlineEdit.tsx:223 — see inline comment
- `FE2` packages/graph-editor/src/GraphEditorCanvas.tsx:175 — see inline comment
- `FE2` packages/graph-editor/src/GraphEditorCanvas.tsx:231 — see inline comment
- `FE2` packages/graph-editor/src/GraphEditorCanvas.tsx:331 — see inline comment
- `FE3` packages/graph-editor/src/GraphEditorCanvas.tsx:387 — see inline comment
- `FE3` packages/graph-editor/src/GraphEditorCanvas.tsx:397 — see inline comment

**Should-fix anchors:**
- `FE4` packages/ui/src/components/InlineEdit/InlineEdit.tsx:86 — see inline comment
- `FE5` packages/graph-editor/src/GraphEditorCanvas.tsx:34 — see inline comment
- `FE6` packages/graph-editor/src/MiniMap.tsx:92 — see inline comment
- `SC3` .claude/scheduled_tasks.lock:1 — see inline comment

**Nit anchors:**
- `FE7` .changeset/add-graph-editor-canvas.md:7 — see inline comment (with `suggestion` fence)

The 12 anchors above are posted as inline comments — see the "Inline comments to post" section at the top of this file for the full finding bodies. Headline summaries (mapped 1:1 to the inline comments, with the `# Copilot finding #N` markers used to score coverage against the original missed PR):

- **[FE1-A11Y-CONTRACT-BROKEN] InlineEdit.tsx:234** — `aria-errormessage` references a `${id}-error` element that is not rendered; AT users get a dangling reference. (#3)
- **[FE1-A11Y-CONTRACT-BROKEN] InlineEdit.tsx:223** — display-mode `aria-label` is not carried over when swapping to edit-mode `<input>`. (#2)
- **[FE2-CONTROLLED-STATE-DESYNC] GraphEditorCanvas.tsx:175** — `useEffect([elements])` calls `history.reset()` on every prop change; controlled consumers lose undo. (#5)
- **[FE2-CONTROLLED-STATE-DESYNC] GraphEditorCanvas.tsx:231** — `onConnect` emits `{source,target}` without the internally-generated edge id; persisted-vs-internal id diverges. (#7)
- **[FE2-CONTROLLED-STATE-DESYNC] GraphEditorCanvas.tsx:331** — `onNodeAdd` callback drops `{id,data}`; undo-after-delete cannot restore. (#6)
- **[FE3-COMMAND-HISTORY-INCOMPLETE] GraphEditorCanvas.tsx:387** — arrow-key nudges bypass `applyCommand`; `⌘Z` undoes drags but not nudges. (#8)
- **[FE3-COMMAND-HISTORY-INCOMPLETE] GraphEditorCanvas.tsx:397** — Delete pushes both `delete-node` and `delete-edge` for incident edges; undo re-adds duplicates. (#9)
- **[FE4-NO-OP-PROP-VALUE] InlineEdit.tsx:86** — `activate: 'click' | 'focus'` but only `'click'` is implemented. (#1)
- **[FE5-SSR-GLOBAL-CSS] GraphEditorCanvas.tsx:34** — `import './styles.css'` in a non-entry module breaks Next.js App Router consumers. (#4)
- **[FE6-RANGE-CLAMP-MISSING] MiniMap.tsx:92** — viewport width/height not clamped to [0,1]; rect overshoots minimap frame. (#10)
- **[SC3-SECRET-LEAK] .claude/scheduled_tasks.lock:1** — ephemeral runtime lockfile committed.
- **[FE7-CHANGESET-DRIFT] add-graph-editor-canvas.md:7** — changeset says behaviors land "next iteration" but they ship in this PR. (#11)

### Delegations

- (none — tests were added alongside production code so TS1 does not fire. Note: `InlineEdit.test.tsx` covers display + edit modes only; the validation-error render path is uncovered. Run `/ship-tested-code` for test-coverage depth.)

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

- **Token extraction is clean**: `resolveColorReference` and friends moved intact from `@ship-it-ui/cytoscape` to the new `@ship-it-ui/graph-tokens` package with their full test suites. The cytoscape package re-exports the same surface verbatim; existing consumers see zero behavior change. This is the textbook way to extract a shared dependency.
- **`useHistory` is implemented with refs, not state**: pushing a command doesn't trigger a render. `inverseOf(delete-node)` correctly restores incident edges via a `batch` command. The history primitive is solid; the issues above are about wiring, not the primitive.
- **Keyboard guard at the canvas root**: `INPUT`, `TEXTAREA`, and `contentEditable` targets short-circuit the keyboard handler before any canvas binding fires. An `<InlineEdit>` inside a custom node can type without triggering Delete or arrow-nudge on the host canvas.
- **`aria-errormessage` intent is right**: the ARIA pattern wiring is correct; only the missing DOM target needs to be added.

### Submission preview (local mode only)
  gh api -X POST repos/ship-it-ops/ship-it-design/pulls/47/reviews (create pending review)
  gh api -X POST .../reviews/${REVIEW_ID}/comments × 11 (one per Must-fix + one per Should-fix + the FE7 Nit anchor)
  gh api -X POST .../reviews/${REVIEW_ID}/events -f event=REQUEST_CHANGES -f body=<summary>

Proceed? Type "yes" to submit, "edit" to revise, "no" to abort.
```

## What this fixture demonstrates

1. **Regression coverage** — 10 of 10 finding sites from the original missed PR are now caught by the FE persona plus the existing SC3 lockfile catch. Pre-FE baseline was 2/10 (the aria-errormessage and the lockfile). The fixture is the durable acceptance test for the FE additions.
2. **FE > SE on TSX dedup** — three FE2 findings on `GraphEditorCanvas.tsx:175/231/331` would have been generic SE2-CONTRACT-DRIFT findings without the FE persona. FE2 framing ("undo unusable in the controlled-elements pattern the docs themselves show") is far more actionable.
3. **Severity discipline** — FE1/FE2/FE3 are *1 (Must-fix), FE4/FE5/FE6 are *2 (Should-fix), FE7 is *4 (Nit). Even though FE5 (SSR/global-CSS) and FE6 (range clamp) are real production bugs, they sit in Should-fix because they don't necessarily block functional behavior the way a state-desync does. Tier consistency matters more than per-finding intuition.
4. **SC and FE coexist** — SC3 still catches the committed lockfile; FE doesn't replace SC, it adds the missing domain.
5. **"What's solid" is substantive and frontend-flavored** — token extraction, history primitive correctness, keyboard guard placement, ARIA intent. Names what the author got right, not just what they got wrong.
