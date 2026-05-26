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
## PR Review: #47 — Add support for graph editing

### Decision: 🛑 REQUEST_CHANGES

### Confidence
Reviewed 56 files (compressed: 8 representative TSX, 1 changeset, 1 lockfile, plus passing-context files). Conditional FE persona activated (TSX-heavy diff with new aria-* attributes and a new `import './styles.css'` in a non-entry module). Conditional DA persona did not activate (no schema files). IN deep mode did not activate (no infra files). SC scanned the diff; flagged one SC3 on the committed lockfile. CI is green. Zero existing review threads. The decision is REQUEST_CHANGES because the FE persona produced three *1-tier findings — an ARIA contract break and two state-management bugs that make undo/redo unusable in the controlled-elements pattern the docs themselves demonstrate.

Generated/vendored skipped: 1 (`pnpm-lock.yaml`).

### 🛑 Critical (must fix before merge)

- **[FE1-A11Y-CONTRACT-BROKEN] packages/ui/src/components/InlineEdit/InlineEdit.tsx:234**: `aria-errormessage` references `${id}-error`, but no element with that id is rendered in the component tree. The string returned by `validate()` lives only in `error` state — sighted users see the red border, AT users get a dangling ARIA reference. → Render the error adjacent to the input: `{error && <p id={`${id}-error`} role="alert" className="text-err mt-1 text-[11px]">{error}</p>}` and wrap the `<input>` + `<p>` in a fragment.

- **[FE2-CONTROLLED-STATE-DESYNC] packages/graph-editor/src/GraphEditorCanvas.tsx:175**: A `useEffect([elements])` resyncs internal React Flow state from the `elements` prop and calls `history.reset()` on every change. In the controlled-elements pattern the docs examples demonstrate (consumer updates `elements` in response to `onNodeMove`/`onConnect`/deletes), this clears undo/redo after every edit — history is effectively unusable. → Either make `elements` uncontrolled (`initialElements` + explicit `resetKey`) or stop resetting history on routine prop updates.

- **[FE2-CONTROLLED-STATE-DESYNC] packages/graph-editor/src/GraphEditorCanvas.tsx:231**: `handleConnect` generates the new edge id internally (`e-${Date.now()}`) but the outward `onConnect` callback only emits `{source, target}` to the consumer. A controlled consumer reconstructs the edge with a different id; internal history/selection/edge-delete events then diverge from the persisted graph. → Include the generated id in the callback: `onConnect?.({ source, target, id: newEdge.id })`, or accept a `createEdgeId` factory prop so the consumer chooses.

- **[FE3-COMMAND-HISTORY-INCOMPLETE] packages/graph-editor/src/GraphEditorCanvas.tsx:387**: Arrow-key nudges flow through `useGraphEditorKeyboard` and apply via `baseOnNodesChange`, bypassing the `applyCommand` dispatch that drag/click handlers use. `⌘Z` will undo drags but not nudges, and the keyboard path silently corrupts history when interleaved with mouse actions. → Route both through `applyCommand({ kind: 'move-node', from, to })`.

- **[FE3-COMMAND-HISTORY-INCOMPLETE] packages/graph-editor/src/GraphEditorCanvas.tsx:397**: When Delete is pressed with both nodes and edges selected, `deleteSelectedNodes()` records a `delete-node` command (whose inverse restores incident edges) AND `deleteSelectedEdges()` records a separate `delete-edge` for each selected edge. If a selected edge is incident to a selected node, undo re-adds it twice — duplicate edges in the graph. → Before pushing `delete-edge` commands, subtract edges already covered by a `delete-node` in this batch.

### ⚠️ Important (should fix)

- **[FE5-SSR-GLOBAL-CSS] packages/graph-editor/src/GraphEditorCanvas.tsx:34**: Global CSS imported (`import './styles.css'`) inside a non-entry component module. Next.js App Router only permits global CSS imports from `layout.tsx`/`_app.tsx`; consumers on App Router will hit a build error. The package already exports `@ship-it-ui/graph-editor/styles.css` for consumer-side import. → Drop the internal import; document that consumers must import the stylesheet once from their entry module.

- **[SC3-SECRET-LEAK] .claude/scheduled_tasks.lock:1**: Ephemeral runtime lock file accidentally committed. The file is created and deleted at runtime by a scheduled-task runner; it embeds a PID and timestamp so it will differ on every machine. → Add `.claude/*.lock` to `.gitignore` and remove this file from the PR.

### Suggestions (improve when convenient)

- **[FE7-CHANGESET-DRIFT] .changeset/add-graph-editor-canvas.md:7**: Changeset body says keyboard handling, undo/redo, mini-map, and the +Add palette "land in the next iteration", but those behaviors are implemented in this PR (`keyboard.ts`, `history.ts`, `MiniMap.tsx`, `applyCommand({ kind: 'add-node' })`). Release notes will be misleading. → Either remove this changeset (a sibling changeset already covers the behaviors) or rewrite the body to describe what actually ships.

### Delegations

- (none — tests were added alongside production code, TS1 does not fire. But note: the `InlineEdit.test.tsx` axe checks cover display and edit modes only — not the validation-error render path. Run `/ship-tested-code` for test-coverage depth.)

### Comment lifecycle
- 0 resolved | 0 outdated | 0 won't-fix | 0 possibly addressed | 0 stale | 0 open
- Suppressed: 0 findings.

### Stale comments needing reply
- (none)

### What's Good

- **Token extraction is clean**: `resolveColorReference` and friends moved intact from `@ship-it-ui/cytoscape` to the new `@ship-it-ui/graph-tokens` package with their full test suites; the cytoscape package re-exports the same surface verbatim, so existing consumers see zero behavior change. This is the textbook way to extract a shared dependency.
- **`useHistory` uses refs, not state**: pushing a command doesn't trigger a render. The `useMemo` wrapper on the return object keeps effect deps stable. `inverseOf(delete-node)` correctly restores incident edges via a `batch` command. The history primitive itself is solid; the issues above are about how it's wired up in `GraphEditorCanvas`, not the primitive.
- **Keyboard guard at the canvas root**: `INPUT`, `TEXTAREA`, and `contentEditable` targets short-circuit the keyboard handler before any canvas binding fires. An `<InlineEdit>` inside a custom node can type, commit, and cancel without accidentally triggering Delete or arrow-nudge on the host canvas. Correct guard placement.
- **`aria-errormessage` intent is right**: the wiring (`aria-invalid` + `aria-errormessage` + validation state) is the correct ARIA pattern; only the missing DOM target needs to be added.
- **Changesets are well-described elsewhere**: each of the other three changesets has a substantive body explaining what shipped and why. The FE7 finding above is on the one outlier.

### Submission preview (local mode only)
  gh api -X POST repos/ship-it-ops/ship-it-design/pulls/47/reviews (create pending review)
  gh api -X POST .../reviews/${REVIEW_ID}/comments × 6 (one per Critical + the Important SC3 + Important FE5)
  gh api -X POST .../reviews/${REVIEW_ID}/events -f event=REQUEST_CHANGES -f body="<this entire output as the summary, with the Submission preview block stripped>"

Proceed? Type "yes" to submit, "edit" to revise the body, "no" to abort.
```

---

## What this example demonstrates

1. **FE engages on a TSX-heavy PR** even though SE alone would have caught only the lock file (SC3) and missed the FE-shaped state/contract bugs. Without FE, the original review of this PR posted 3 findings; with FE, it posts 7 findings substantively comparable to a senior FE engineer's review.
2. **FE2 wins over SE2 in dedup**: the controlled-state desync at line 175 would otherwise fingerprint as a generic SE2-CONTRACT-DRIFT. FE2 framing ("undo unusable in the controlled-elements pattern the docs themselves demonstrate") is more actionable.
3. **Critical tier is reserved for *1 findings** (FE1, FE2, FE3). FE5 is *2 (Important). FE7 is *4 (Suggestions). The decision matrix doesn't negotiate — five *1 findings drive REQUEST_CHANGES on first sight.
4. **SC still catches the lockfile** — SC isn't replaced by FE; they cover different concerns. SC3 fires on the `.claude/scheduled_tasks.lock` because it matches the "committed runtime/lock-file artifact" sub-pattern of SECRET-LEAK.
5. **"What's Good" is substantive and frontend-flavored** — token extraction, history primitive correctness, keyboard guard placement, ARIA intent. These observations help the author trust the criticism: the reviewer engaged with the design, not just hunted for problems.
6. **Delegation is mentioned without firing TS1**: the axe-test gap is too specific to merit TS1 (TS1 is purely "no tests added"), but the FE persona's adjacent-test-file read surfaces it as a delegation pointer in prose.
