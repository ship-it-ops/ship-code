# Synthetic PR Input for Fixture 5: Frontend Correctness PR

You are reviewing the following PR. Treat the input below as the result of the `gh` fetch phase. Do not actually run `gh` commands.

This fixture is the regression anchor for the FE persona. It is derived from a real PR the skill missed before FE was added — see `examples/fe-review-example.md` for the worked output. The 10 finding sites in the diff are each annotated with the FE finding they should trigger; the expected-output file's annotations cross-check coverage.

## PR metadata

```json
{
  "owner": "ship-it-ops",
  "repo": "ship-it-design",
  "number": 47,
  "title": "Add support for graph editing",
  "body": "## Summary\n\nAdds a new `GraphEditorCanvas` (React Flow-based) to `@ship-it-ui/graph-editor`, an `InlineEdit` primitive in `@ship-it-ui/ui`, and extracts a shared `@ship-it-ui/graph-tokens` package from `@ship-it-ui/cytoscape`.\n\n## Type of change\n\n- [x] New component / pattern / hook\n- [ ] Bug fix\n",
  "headRefName": "support-graph-editing",
  "baseRefName": "main",
  "author": "Mohamed-E",
  "isDraft": false,
  "labels": [],
  "files": [
    {"path": ".claude/scheduled_tasks.lock", "additions": 3, "deletions": 0},
    {"path": ".changeset/add-graph-editor-canvas.md", "additions": 7, "deletions": 0},
    {"path": ".changeset/add-graph-editor-behaviors.md", "additions": 5, "deletions": 0},
    {"path": ".changeset/add-inline-edit-primitive.md", "additions": 5, "deletions": 0},
    {"path": ".changeset/extract-graph-tokens-package.md", "additions": 5, "deletions": 0},
    {"path": "packages/ui/src/components/InlineEdit/InlineEdit.tsx", "additions": 250, "deletions": 0},
    {"path": "packages/ui/src/components/InlineEdit/InlineEdit.test.tsx", "additions": 120, "deletions": 0},
    {"path": "packages/ui/src/components/InlineEdit/index.ts", "additions": 4, "deletions": 0},
    {"path": "packages/ui/src/index.ts", "additions": 2, "deletions": 0},
    {"path": "packages/graph-editor/src/GraphEditorCanvas.tsx", "additions": 400, "deletions": 0},
    {"path": "packages/graph-editor/src/GraphEditorCanvas.test.tsx", "additions": 80, "deletions": 0},
    {"path": "packages/graph-editor/src/MiniMap.tsx", "additions": 110, "deletions": 0},
    {"path": "packages/graph-editor/src/history.ts", "additions": 150, "deletions": 0},
    {"path": "packages/graph-editor/src/keyboard.ts", "additions": 60, "deletions": 0},
    {"path": "packages/graph-editor/src/adapter.ts", "additions": 90, "deletions": 0},
    {"path": "packages/graph-editor/src/DefaultNode.tsx", "additions": 50, "deletions": 0},
    {"path": "packages/graph-editor/src/GraphNodeShell.tsx", "additions": 55, "deletions": 0},
    {"path": "packages/graph-editor/src/styles.css", "additions": 30, "deletions": 0},
    {"path": "packages/graph-editor/src/theme-bridge.ts", "additions": 40, "deletions": 0},
    {"path": "packages/graph-editor/package.json", "additions": 25, "deletions": 0},
    {"path": "packages/graph-tokens/src/theme-tokens.ts", "additions": 200, "deletions": 0},
    {"path": "packages/graph-tokens/src/theme-tokens.test.ts", "additions": 90, "deletions": 0},
    {"path": "packages/graph-tokens/src/index.ts", "additions": 8, "deletions": 0},
    {"path": "packages/graph-tokens/package.json", "additions": 20, "deletions": 0},
    {"path": "packages/cytoscape/src/theme-tokens.ts", "additions": 10, "deletions": 180},
    {"path": "apps/docs-site/app/(docs)/graph/editor/page.mdx", "additions": 80, "deletions": 0},
    {"path": "apps/docs-site/app/(docs)/components/inline-edit/page.mdx", "additions": 60, "deletions": 0},
    {"path": "apps/docs-site/content/navigation.ts", "additions": 6, "deletions": 0},
    {"path": "pnpm-lock.yaml", "additions": 1200, "deletions": 80}
  ],
  "statusCheckRollup": {"state": "SUCCESS"},
  "commits": [{"sha": "e4b3722", "committedDate": "2026-05-19T22:52:00Z"}]
}
```

## Diff (gh pr diff — compressed to the lines that matter for each finding)

```diff
diff --git a/.claude/scheduled_tasks.lock b/.claude/scheduled_tasks.lock
new file mode 100644
@@ -0,0 +1,3 @@
+{
+  "pid": 47234,
+  "started_at": "2026-05-19T22:51:30Z"
+}

diff --git a/.changeset/add-graph-editor-canvas.md b/.changeset/add-graph-editor-canvas.md
new file mode 100644
@@ -0,0 +1,7 @@
+---
+"@ship-it-ui/graph-editor": minor
+---
+
+Initial `GraphEditorCanvas` surface. Renders nodes/edges and emits `onNodeMove`/`onConnect`/`onSelect`.
+
+Keyboard handling, undo/redo, mini-map, and the +Add palette land in the next iteration.

diff --git a/.changeset/add-graph-editor-behaviors.md b/.changeset/add-graph-editor-behaviors.md
new file mode 100644
@@ -0,0 +1,5 @@
+---
+"@ship-it-ui/graph-editor": minor
+---
+
+Graph editor behaviors: keyboard shortcuts (arrow-nudge, delete), undo/redo via command-history stack, mini-map adapter, +Add palette.

diff --git a/packages/ui/src/components/InlineEdit/InlineEdit.tsx b/packages/ui/src/components/InlineEdit/InlineEdit.tsx
new file mode 100644
@@ -0,0 +1,250 @@
+import { useState, useRef, useEffect } from 'react';
+import { cn } from '@ship-it-ui/cn';
+import { inputStyles } from './styles';
+
+export type Activation = 'click' | 'focus';
+
+export interface InlineEditProps {
+  value: string;
+  onValueChange: (next: string) => void;
+  activate?: Activation;
+  validate?: (value: string) => string | null;
+  size?: 'sm' | 'md';
+  id?: string;
+  inputClassName?: string;
+}
+
+export function InlineEdit({
+  value,
+  onValueChange,
+  activate = 'click',
+  validate,
+  size = 'md',
+  ...rest
+}: InlineEditProps) {
+  const [editing, setEditing] = useState(false);
+  const [draft, setDraft] = useState(value);
+  const [error, setError] = useState<string | null>(null);
+
+  function startEdit() {
+    setDraft(value);
+    setError(null);
+    setEditing(true);
+  }
+
+  function handleClick() {
+    if (activate === 'click') startEdit();
+  }
+  // ↑ FINDING #1 (line ~86): `activate='focus'` is in the union but has no branch.
+
+  function commit() {
+    const err = validate?.(draft) ?? null;
+    if (err) { setError(err); return; }
+    setEditing(false);
+    onValueChange(draft);
+  }
+
+  if (!editing) {
+    return (
+      <button
+        type="button"
+        role="button"
+        aria-label={`Edit ${value}`}
+        onClick={handleClick}
+        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') startEdit(); }}
+      >
+        {value}
+      </button>
+    );
+  }
+
+  return (
+    <input
+      value={draft}
+      onChange={(e) => setDraft(e.target.value)}
+      onBlur={commit}
+      onKeyDown={(e) => {
+        if (e.key === 'Enter') commit();
+        if (e.key === 'Escape') setEditing(false);
+      }}
+      aria-invalid={error ? true : undefined}
+      aria-errormessage={error ? `${rest.id ?? 'inline-edit'}-error` : undefined}
+      className={cn(inputStyles({ size, tone: error ? 'err' : 'default' }), rest.inputClassName)}
+    />
+    // ↑ FINDING #2 (line ~223): the <input> has no aria-label; the display element's
+    //   `aria-label={`Edit ${value}`}` does not carry over to the input that just replaced it.
+    // ↑ FINDING #3 (line ~234): aria-errormessage references `${id}-error` but no element
+    //   with that id is rendered anywhere; error text only lives in `error` state.
+  );
+}

diff --git a/packages/graph-editor/src/GraphEditorCanvas.tsx b/packages/graph-editor/src/GraphEditorCanvas.tsx
new file mode 100644
@@ -0,0 +1,400 @@
+'use client';
+
+import { useEffect, useMemo, useState } from 'react';
+import { ReactFlow, useNodesState, useEdgesState, applyNodeChanges } from '@xyflow/react';
+import { useHistory } from './history';
+import { useGraphEditorKeyboard } from './keyboard';
+import { adapter } from './adapter';
+import { useThemeBridge } from './theme-bridge';
+import { GraphMinimap } from './MiniMap';
+import { DefaultNode } from './DefaultNode';
+import type { GraphElements, GraphNode, GraphEdge, MoveCommand, AddNodeCommand, DeleteNodeCommand, AddEdgeCommand, DeleteEdgeCommand } from './types';
+
+import './styles.css';
+// ↑ FINDING #4 (line ~34): global CSS import inside a non-entry module breaks
+//   Next.js App Router. The package already exports
+//   `@ship-it-ui/graph-editor/styles.css` for consumer-side import.
+
+export interface GraphEditorCanvasProps {
+  elements: GraphElements;
+  onNodeMove?: (id: string, position: { x: number; y: number }) => void;
+  onConnect?: (params: { source: string; target: string }) => void;
+  onNodeAdd?: (position: { x: number; y: number }) => void;
+  onDeleteNode?: (id: string) => void;
+  onDeleteEdge?: (id: string) => void;
+  toolbarSlot?: React.ReactNode;
+}
+
+export function GraphEditorCanvas({
+  elements,
+  onNodeMove,
+  onConnect,
+  onNodeAdd,
+  onDeleteNode,
+  onDeleteEdge,
+  toolbarSlot,
+}: GraphEditorCanvasProps) {
+  const [nodes, setNodes] = useNodesState(adapter.nodesToReactFlow(elements));
+  const [edges, setEdges] = useEdgesState(adapter.edgesToReactFlow(elements));
+  const history = useHistory();
+
+  useEffect(() => {
+    setNodes(adapter.nodesToReactFlow(elements));
+    setEdges(adapter.edgesToReactFlow(elements));
+    history.reset();
+  }, [elements]);
+  // ↑ FINDING #5 (line ~175): re-sync internal state from `elements` AND reset
+  //   history every change. Consumers using the controlled-elements pattern the
+  //   docs examples show will see undo cleared after every edit.
+
+  function applyCommand(cmd: MoveCommand | AddNodeCommand | DeleteNodeCommand | AddEdgeCommand | DeleteEdgeCommand) {
+    history.push(cmd);
+    switch (cmd.kind) {
+      case 'add-node':
+        setNodes((ns) => [...ns, cmd.node]);
+        onNodeAdd?.(cmd.node.position);
+        break;
+      // ↑ FINDING #6 (line ~331): internal command stores full {id, data, position}
+      //   but onNodeAdd only emits position. On undo-of-delete, consumer can't
+      //   restore the same node from position alone.
+      case 'delete-node':
+        setNodes((ns) => ns.filter((n) => n.id !== cmd.id));
+        setEdges((es) => es.filter((e) => e.source !== cmd.id && e.target !== cmd.id));
+        onDeleteNode?.(cmd.id);
+        break;
+      case 'add-edge':
+        setEdges((es) => [...es, cmd.edge]);
+        break;
+      case 'delete-edge':
+        setEdges((es) => es.filter((e) => e.id !== cmd.edge.id));
+        onDeleteEdge?.(cmd.edge.id);
+        break;
+      case 'move-node':
+        setNodes((ns) => ns.map((n) => (n.id === cmd.id ? { ...n, position: cmd.to } : n)));
+        onNodeMove?.(cmd.id, cmd.to);
+        break;
+    }
+  }
+
+  function handleConnect(params: { source: string; target: string }) {
+    const newEdge: GraphEdge = { id: `e-${Date.now()}`, ...params };
+    applyCommand({ kind: 'add-edge', edge: newEdge });
+    onConnect?.({ source: params.source, target: params.target });
+    // ↑ FINDING #7 (line ~231): outward callback emits only {source, target} but
+    //   the internal handler generates an id via Date.now(). Consumer creates an
+    //   edge with a different id; internal state diverges from persisted graph.
+  }
+
+  function deleteSelectedNodes() {
+    const selected = nodes.filter((n) => n.selected);
+    selected.forEach((node) => {
+      const incidentEdges = edges.filter((e) => e.source === node.id || e.target === node.id);
+      applyCommand({ kind: 'delete-node', id: node.id, incidentEdges });
+    });
+  }
+
+  function deleteSelectedEdges() {
+    const selected = edges.filter((e) => e.selected);
+    selected.forEach((edge) => {
+      applyCommand({ kind: 'delete-edge', edge });
+    });
+  }
+
+  function handleDelete() {
+    deleteSelectedNodes();
+    deleteSelectedEdges();
+    // ↑ FINDING #8 (line ~397): delete-node already cascades incident edges via
+    //   its inverse, AND delete-edge is pushed separately for selected edges.
+    //   Undo re-adds incident edges twice.
+  }
+
+  function baseOnNodesChange(changes: any[]) {
+    setNodes((ns) => applyNodeChanges(changes, ns));
+  }
+
+  useGraphEditorKeyboard({
+    onArrow: (direction) => {
+      const selectedIds = nodes.filter((n) => n.selected).map((n) => n.id);
+      const change = makePositionChange(selectedIds, direction);
+      baseOnNodesChange(change);
+      // ↑ FINDING #9 (line ~387): arrow-key nudges call baseOnNodesChange directly,
+      //   bypassing applyCommand. ⌘Z won't undo keyboard nudges.
+    },
+    onDelete: handleDelete,
+  });
+
+  useThemeBridge();
+
+  return (
+    <ReactFlow
+      nodes={nodes}
+      edges={edges}
+      onNodesChange={baseOnNodesChange}
+      onConnect={handleConnect}
+      nodeTypes={{ default: DefaultNode }}
+    >
+      {toolbarSlot}
+      <GraphMinimap viewportRect={...} />
+    </ReactFlow>
+  );
+}

diff --git a/packages/graph-editor/src/MiniMap.tsx b/packages/graph-editor/src/MiniMap.tsx
new file mode 100644
@@ -0,0 +1,110 @@
+...
+function computeViewportRect(viewport: Viewport, bbox: Bbox) {
+  const tl = projectToBbox(viewport.tl, bbox);
+  const br = projectToBbox(viewport.br, bbox);
+  return {
+    x: Math.max(0, Math.min(1, tl.x)),
+    y: Math.max(0, Math.min(1, tl.y)),
+    width: br.x - tl.x,
+    height: br.y - tl.y,
+    // ↑ FINDING #10 (line ~92): width/height not clamped — when the viewport
+    //   is panned past the graph bbox, these can exceed 1. GraphMinimap expects
+    //   normalized 0..1 fractions; rendering artifacts result.
+  };
+}
+...
```

## Review threads (gh api graphql)

```json
{
  "reviewThreads": []
}
```

## CI checks (gh pr checks)

All green.

---

Run the multi-persona PR review and produce the structured output. The expected output annotates each finding with its mapped Copilot-finding number so coverage can be scored directly: 10 of 10 finding sites caught is the target. (The two "obvious" findings — #3 aria-errormessage and the lock file — were caught by the pre-FE skill; the other 8 are new with FE.)
