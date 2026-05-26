# Expected Review Output — fixture-5-frontend-pr

The skill should produce a report substantially matching the structure below. The Critical FE1/FE2/FE3 findings and the REQUEST_CHANGES decision are non-negotiable; wording details can vary.

Each finding is annotated with `# Copilot finding #N` to cross-check coverage against the original 10 missed findings. Target: 10/10 catch rate after FE persona is fully wired up. Pre-FE baseline: 2/10 (only #3 aria-errormessage and the lock file were caught).

---

```
## PR Review: #47 — Add support for graph editing

### Decision: 🛑 REQUEST_CHANGES

### Confidence
Reviewed 29 files (compressed diff of 56 changed files; pnpm-lock.yaml skipped as generated). Conditional FE persona activated (TSX-heavy diff with new aria-* attributes, new `import './styles.css'` in non-entry module, .changeset/*.md files). Conditional DA persona did not activate. IN deep mode did not activate. SC scanned all files; flagged one SC3 on `.claude/scheduled_tasks.lock`. CI is green. Zero existing review threads. The decision is REQUEST_CHANGES because FE produced five *1-tier findings on the GraphEditorCanvas state-management surface plus an ARIA contract break in InlineEdit.

Generated/vendored skipped: 1 (pnpm-lock.yaml).

### 🛑 Critical (must fix before merge)

- **[FE1-A11Y-CONTRACT-BROKEN] packages/ui/src/components/InlineEdit/InlineEdit.tsx:234**: `aria-errormessage` references `${rest.id ?? 'inline-edit'}-error`, but no element with that id is rendered anywhere in the component. The error string from `validate()` lives only in `error` state — sighted users see the red border, AT users get a dangling ARIA reference. → Render the error adjacent to the input: `{error && <p id={`${rest.id ?? 'inline-edit'}-error`} role="alert" className="text-err mt-1 text-[11px]">{error}</p>}` inside a fragment with the `<input>`. # Copilot finding #3

- **[FE1-A11Y-CONTRACT-BROKEN] packages/ui/src/components/InlineEdit/InlineEdit.tsx:223**: When the component swaps from display mode (`<button aria-label="Edit ${value}">`) to edit mode (`<input>`), the display element's accessible name does not carry over. Screen readers announce nothing meaningful for the input that just appeared. → Apply the same computed label to the input: `<input aria-label={`Editing ${value}`} ...>`. # Copilot finding #2

- **[FE2-CONTROLLED-STATE-DESYNC] packages/graph-editor/src/GraphEditorCanvas.tsx:175**: `useEffect([elements])` re-syncs internal state from the `elements` prop and calls `history.reset()` on every change. Consumers using the controlled-elements pattern the docs examples demonstrate (`elements` updated in response to `onNodeMove`/`onConnect`/deletes) will see history cleared after every edit — undo/redo is unusable. → Either make `elements` uncontrolled (`initialElements` + explicit `resetKey` prop) or stop resetting history on routine prop updates. # Copilot finding #5

- **[FE2-CONTROLLED-STATE-DESYNC] packages/graph-editor/src/GraphEditorCanvas.tsx:231**: `handleConnect` generates the new edge id (`e-${Date.now()}`) internally but `onConnect` emits only `{source, target}` to the consumer. A controlled consumer will create an edge with a different id; internal history/selection/edge-delete events then diverge from the consumer's persisted graph. → Include the generated id in the callback: `onConnect?.({ source, target, id: newEdge.id })`, or accept a `createEdgeId` factory prop. # Copilot finding #7

- **[FE2-CONTROLLED-STATE-DESYNC] packages/graph-editor/src/GraphEditorCanvas.tsx:331**: `applyCommand('add-node')` calls `onNodeAdd` with only a position, but the internal command stores the full `{id, data, position}`. On undoing a `delete-node`, the consumer cannot restore the same node via `onNodeAdd(position)` alone, so external persistence will desync from the internal graph. → Change the callback contract to include the full node: `onNodeAdd?.(cmd.node)`. # Copilot finding #6

- **[FE3-COMMAND-HISTORY-INCOMPLETE] packages/graph-editor/src/GraphEditorCanvas.tsx:387**: Arrow-key nudges flow through `useGraphEditorKeyboard` and apply via `baseOnNodesChange`, bypassing the `applyCommand` dispatch that drag/click handlers use. `⌘Z` will undo drags but not nudges, and the keyboard path silently corrupts history when interleaved with mouse actions. → Route both through `applyCommand({ kind: 'move-node', from, to })`. # Copilot finding #8

- **[FE3-COMMAND-HISTORY-INCOMPLETE] packages/graph-editor/src/GraphEditorCanvas.tsx:397**: When Delete is pressed with both nodes and edges selected, `deleteSelectedNodes()` records a `delete-node` command whose inverse already restores incident edges, AND `deleteSelectedEdges()` records a separate `delete-edge` for each selected edge. If a selected edge is incident to a selected node, undo re-adds it twice — duplicate edges. → Before pushing `delete-edge` commands, subtract edges already covered by a `delete-node` in this batch. # Copilot finding #9

### ⚠️ Important (should fix)

- **[FE4-NO-OP-PROP-VALUE] packages/ui/src/components/InlineEdit/InlineEdit.tsx:86**: `activate` is typed `'click' | 'focus'` but no implementation branch on `activate === 'focus'` exists; only the `'click'` path triggers `startEdit()`. The prop value is type-system-valid and silently does nothing at runtime. → Either implement focus activation (start edit on `onFocus` when `activate === 'focus'`), or remove `'focus'` from the `Activation` union. # Copilot finding #1

- **[FE5-SSR-GLOBAL-CSS] packages/graph-editor/src/GraphEditorCanvas.tsx:34**: Global CSS imported (`import './styles.css'`) inside a non-entry module. Next.js App Router only permits global CSS imports from `layout.tsx`/`_app.tsx`; consumers on App Router will hit a build error. The package already exports `@ship-it-ui/graph-editor/styles.css` for consumer-side import. → Drop the internal import; document that consumers must import the stylesheet once from their entry module. # Copilot finding #4

- **[FE6-RANGE-CLAMP-MISSING] packages/graph-editor/src/MiniMap.tsx:92**: `viewportRect.width = br.x - tl.x` and `height = br.y - tl.y` are not clamped to [0,1]. When the viewport is panned past the graph bbox, these can exceed 1. `GraphMinimap` expects normalized 0..1 fractions, so the rendered rect extends past the minimap frame. → Clamp width/height using the already-clamped top-left: `width: Math.max(0, Math.min(1, br.x)) - Math.max(0, Math.min(1, tl.x))`, same for height. # Copilot finding #10

- **[SC3-SECRET-LEAK] .claude/scheduled_tasks.lock:1**: Ephemeral runtime lock file accidentally committed. The file is created and deleted at runtime by a scheduled-task runner; it embeds a PID and timestamp so it will conflict on every machine. → Add `.claude/*.lock` to `.gitignore` and drop this file from the PR.

### Suggestions (improve when convenient)

- **[FE7-CHANGESET-DRIFT] .changeset/add-graph-editor-canvas.md:7**: Changeset body says keyboard handling, undo/redo, mini-map, and the +Add palette "land in the next iteration", but those behaviors are implemented in this PR (`keyboard.ts`, `history.ts`, `MiniMap.tsx`, the `applyCommand({ kind: 'add-node' })` path). The sibling changeset `add-graph-editor-behaviors.md` already covers the behaviors, so this one duplicates the version bump and ships misleading release notes. → Either remove this changeset or rewrite the body to describe only what's actually new in the canvas surface. # Copilot finding #11 (changeset accuracy)

### Delegations

- (none — tests were added alongside production code so TS1 does not fire. Note: `InlineEdit.test.tsx` covers display + edit modes only; the validation-error render path is uncovered. Run `/ship-tested-code` for test-coverage depth.)

### Comment lifecycle
- 0 resolved | 0 outdated | 0 won't-fix | 0 possibly addressed | 0 stale | 0 open
- Suppressed: 0 findings.

### Stale comments needing reply
- (none)

### What's Good

- **Token extraction is clean**: `resolveColorReference` and friends moved intact from `@ship-it-ui/cytoscape` to the new `@ship-it-ui/graph-tokens` package with their full test suites. The cytoscape package re-exports the same surface verbatim; existing consumers see zero behavior change. This is the textbook way to extract a shared dependency.
- **`useHistory` is implemented with refs, not state**: pushing a command doesn't trigger a render. `inverseOf(delete-node)` correctly restores incident edges via a `batch` command. The history primitive is solid; the issues above are about wiring, not the primitive.
- **Keyboard guard at the canvas root**: `INPUT`, `TEXTAREA`, and `contentEditable` targets short-circuit the keyboard handler before any canvas binding fires. An `<InlineEdit>` inside a custom node can type without triggering Delete or arrow-nudge on the host canvas.
- **`aria-errormessage` intent is right**: the ARIA pattern wiring is correct; only the missing DOM target needs to be added.

### Submission preview (local mode only)
  gh api -X POST repos/ship-it-ops/ship-it-design/pulls/47/reviews (create pending review)
  gh api -X POST .../reviews/${REVIEW_ID}/comments × 10 (one per Critical + one per Important)
  gh api -X POST .../reviews/${REVIEW_ID}/events -f event=REQUEST_CHANGES -f body=<summary>

Proceed? Type "yes" to submit, "edit" to revise, "no" to abort.
```

## What this fixture demonstrates

1. **Regression coverage** — 10 of 10 finding sites from the original missed PR are now caught by the FE persona plus the existing SC3 lockfile catch. Pre-FE baseline was 2/10 (the aria-errormessage and the lockfile). The fixture is the durable acceptance test for the FE additions.
2. **FE > SE on TSX dedup** — three FE2 findings on `GraphEditorCanvas.tsx:175/231/331` would have been generic SE2-CONTRACT-DRIFT findings without the FE persona. FE2 framing ("undo unusable in the controlled-elements pattern the docs themselves show") is far more actionable.
3. **Tier discipline** — FE1/FE2/FE3 are *1 (Critical), FE4/FE5/FE6 are *2 (Important), FE7 is *4 (Suggestions). Even though FE5 (SSR/global-CSS) and FE6 (range clamp) are real production bugs, they sit in Important because they don't necessarily block functional behavior the way a state-desync does. Tier consistency matters more than per-finding intuition.
4. **SC and FE coexist** — SC3 still catches the committed lockfile; FE doesn't replace SC, it adds the missing domain.
5. **"What's Good" is substantive and frontend-flavored** — token extraction, history primitive correctness, keyboard guard placement, ARIA intent. Names what the author got right, not just what they got wrong.
