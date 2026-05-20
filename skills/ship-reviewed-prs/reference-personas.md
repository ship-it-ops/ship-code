# Persona Rubrics

Per-persona detail: concerns, triggers, anti-overlap rules, finding examples, common false-positive patterns. Load on-demand when running a specific persona pass.

---

## SE — Senior Engineer

**Always on.** The synthesis lead. Owns concerns that span files and don't fit any other persona.

### Concerns

- API and contract design: public function signatures, exported types, HTTP endpoints, gRPC/protobuf changes, GraphQL schema, SDK surface.
- Backward compatibility: removed exports, renamed fields, changed semantics, signature changes that break callers.
- Rollout safety: feature flags, gradual deploys, deprecation pathways, kill switches, fallback behavior.
- Module-level Single Responsibility: a class or module that grew to handle three concerns.
- Public surface noise: types/symbols exported but not used outside the module.
- Docstring/doc accuracy: type hints contradicting docstrings, doc examples that no longer compile.

### Anti-overlap

SE does **not** emit findings about:
- Naming, function length, magic numbers, dead code, error swallowing, deeply nested code — those are `ship-clean-code`'s P3-P7. Replace with a delegation bullet.
- Test design — `ship-tested-code`.
- Single-file SRP at the function level — `ship-clean-code` P5.

SE owns the **PR-shaped** concerns: changes that span files, public contracts, rollout strategy.

### Finding IDs

| ID | Label | When to fire |
|----|-------|--------------|
| SE1 | BREAKING-CHANGE | A public symbol is removed or its signature changed in a way that breaks downstream callers without a deprecation period. Includes removed HTTP routes, removed fields from responses, changed enum values. |
| SE2 | CONTRACT-DRIFT | A public type or interface evolved in a way that compiles but changes meaning. E.g., field made optional, default value changed, validation loosened. Catches "looks compatible, isn't." |
| SE3 | ROLLOUT-RISK | New feature ships behind no flag in a high-blast-radius area, OR an existing feature flag is being deleted, OR a flag default flips without a coordinated plan. |
| SE4 | LAYERING | A module gained a dependency direction that violates the project's documented architecture (e.g., domain importing infra, server importing client). |
| SE5 | DEPRECATION-MISSING | A symbol is being removed in this PR; the prior release did not mark it deprecated. Two-release minimum is the default; configurable via overrides. |
| SE6 | PUBLIC-SURFACE-NOISE | A new symbol is added to the public API (exported from a package, included in an SDK barrel) but used only internally. Reduces API surface bloat. |
| SE7 | DOCSTRING-MISMATCH | Docstring, type hint, or doc-example disagrees with the implementation. Inconsistency is worse than no docs. |

### Examples

**SE1 firing:**
```diff
-export function createUser(name: string, email: string): User
+export function createUser(name: string, email: string, tier: Tier): User
```
> **[SE1-BREAKING-CHANGE] src/sdk/users.ts:14**: `createUser` adds a required `tier` parameter. Existing callers compiled against the prior signature will fail to type-check. → Make `tier` optional with a sensible default, or add an overload, or mark the prior signature deprecated and ship the new one as `createUserV2`.

**SE2 firing:**
```diff
 export interface UserResponse {
   id: string;
   email: string;
-  tier: "free" | "pro" | "enterprise";
+  tier?: "free" | "pro" | "enterprise";
 }
```
> **[SE2-CONTRACT-DRIFT] src/types/user.ts:8**: `UserResponse.tier` became optional. Callers that destructure `{ tier }` will get `undefined` where they previously got a string; behavior changes silently. → Either keep required (handle legacy upstream), or rename to signal the change (`tier?: Tier | undefined`) plus a release note.

### Common false-positives

- A type's optional/required change inside a *private* module: not a contract change. SE2 only fires on exported types.
- Adding an argument *with a default*: usually safe; only flag if the default changes semantics for old callers.

---

## SC — Senior Security Engineer

**Always on.** Highest-priority persona. Overrides `ship-clean-code` P2-SEC on overlap.

### Concerns

- AuthN/AuthZ: missing auth on new endpoints, broken access control (BOLA/IDOR), authz checked at wrong layer.
- Injection: SQL, NoSQL, command, template (SSTI), XSS, header injection, CRLF, log injection.
- Secrets: hardcoded credentials, API keys, tokens; secrets pushed to git history; secrets logged.
- Crypto: weak algorithms (MD5, SHA1 for security), ECB mode, fixed IVs, custom crypto, hardcoded salts.
- Supply chain: new dependencies, lockfile changes, postinstall scripts, dependencies with known CVEs.
- PII / data sensitivity: PII fields newly logged, PII in URLs, PII in error responses, PII without retention policy.
- Log leakage: tokens / passwords / cookies / authorization headers in log output.
- Server-Side Request Forgery (SSRF): user-controllable URL fetched by server.
- Unsafe deserialization: pickle, Java `ObjectInputStream`, YAML.load with default loader.
- CORS, CSRF, JWT validation: misconfigured CORS allowlist, missing CSRF token on state-changing requests, JWT signature not verified or alg=none accepted.

### Anti-overlap

SC scans every file regardless of bucket. On a shared finding with `ship-clean-code` P2-SEC, SC wins (it gets the prefix tag, not P2-SEC).

### Delegation to `ship-secure-code`

SC has two depth modes:

- **Direct-emit** (single-line, high-precision patterns): hardcoded secret literal matching a known prefix (`sk_live_`, `AKIA`, `ghp_`, etc.); `dangerouslySetInnerHTML={{__html: userInput}}` where `userInput` is a clearly-tracked HTTP field; new HTTP route handler with no auth middleware between path and handler; `eval(userInput)` / `Function(userInput)`; `child_process.exec` with template literal; `jwt.decode(token, verify=False)`. These fire inline as SC1/SC2/SC3 findings without delegation.
- **Delegate** (anything requiring data-flow trace, multi-file context, framework-specific knowledge, or one of the SEC4-SEC12 categories): emit a single `Run /ship-secure-code on <file>` bullet under Delegations. Example triggers: `db.query` with interpolated value where the value's source isn't visible in the same file; `prisma.findUnique({where: {id}})` where tenant scope may or may not be needed (depends on schema); ReDoS-shape regex; SSRF-shape `fetch(userUrl)`; deserialization sink; CORS misconfig (needs cross-file allowlist context).

The delegation bullet does NOT count toward the decision matrix — same rule as other delegations. But if the SC direct-emit pass produces *1 findings, those still drive REQUEST_CHANGES.

This mirrors the TS → `ship-tested-code` pattern at `SKILL.md:71-76` — orchestrator does shallow detection, the depth target owns the rubric.

### Finding IDs

| ID | Label | When to fire |
|----|-------|--------------|
| SC1 | AUTH-MISSING | New endpoint/route/handler has no auth check, or auth check is at wrong layer. Includes missing role/permission checks (IDOR/BOLA risk). |
| SC2 | INJECTION | SQL/command/template injection pattern detected. Includes string-concatenated queries, `eval()` with user input, template rendering with unescaped user input. |
| SC3 | SECRET-LEAK | Credentials, API keys, tokens hardcoded or pushed to logs. Includes `.env` files committed, secrets in CI YAML, secrets in code comments. |
| SC4 | CRYPTO-MISUSE | Weak crypto algorithms, custom crypto rolled, fixed IVs, hardcoded salts, missing signature verification on JWTs. |
| SC5 | DEPENDENCY-RISK | New dependency added with: known CVE, postinstall script, very new (< 3 months) with low maintenance signal, unverifiable publisher. Includes lockfile changes that pull in new transitive deps. |
| SC6 | PII-HANDLING | PII (email, phone, SSN, name) appears in: log output, error responses, URL query strings, third-party analytics calls. |
| SC7 | LOG-LEAKAGE | Authorization headers, cookies, full request bodies, session tokens logged. |

### Examples

**SC1 firing:**
```diff
+// New route
+router.post("/admin/users", async (req, res) => {
+  const user = await db.users.create(req.body);
+  res.json(user);
+});
```
> **[SC1-AUTH-MISSING] src/api/admin.ts:42**: New `POST /admin/users` has no auth middleware. Any unauthenticated request can create admin users. → Add `requireAdmin` middleware (see `src/middleware/auth.ts:78` for the pattern). Verify with `curl -X POST localhost:3000/admin/users` returns 401.

**SC2 firing:**
```diff
+const query = `SELECT * FROM users WHERE email = '${email}'`;
+const rows = await db.execute(query);
```
> **[SC2-INJECTION] src/services/users.ts:18**: SQL injection via string interpolation. A malicious `email` value (`' OR '1'='1`) executes arbitrary SQL. → Use parameterized query: `db.execute("SELECT * FROM users WHERE email = $1", [email])`. The project's `db.execute` already supports parameters.

**SC5 firing:**
```diff
+  "left-pad": "1.0.0",
+  "untrusted-postinstall-pkg": "0.0.1"
```
> **[SC5-DEPENDENCY-RISK] package.json:34**: New dependency `untrusted-postinstall-pkg@0.0.1`: published 2 weeks ago, no GitHub repo linked, contains a `postinstall` script. Supply-chain risk. → Verify the package origin; pin to a reviewed version; consider vendoring; or remove the dependency.

### Common false-positives

- A test fixture that contains a fake credential (e.g., `password: "test1234"` in a unit test). If path is in the `test` bucket and the variable name suggests test usage, skip.
- A "secret" that's a documented placeholder (e.g., `YOUR_API_KEY_HERE` in docs). If the file is `*.md` and the value is all-caps, skip.
- Crypto that's reading the right thing but a linter would still flag (e.g., MD5 used for file checksum, not security). Check the surrounding semantic.

---

## IN — Senior Infra / SRE / DevOps

**Always on in light mode**, deep mode escalates to subagent when infra files touched.

### Concerns

- Network-call hygiene: timeouts, retries with backoff, circuit breakers, idempotency keys.
- Observability: structured logs at decision points, metrics for new code paths, traces for cross-service calls.
- Resource limits: connection pools, memory limits, file descriptors, request-size caps.
- CI/CD: new pipeline steps that could block deploys, secrets in workflow files, action versions pinned by SHA.
- IaC: Terraform state implications, blast radius of resource changes, drift potential.
- Migration safety (ops dimension): online vs. blocking, lock-taking, rollback path.
- Performance: N+1 queries, unbounded loops, missing indexes (operational hot-path concern).
- Graceful shutdown: SIGTERM handling, drain logic, in-flight request preservation.

### Anti-overlap

IN owns **operational** concerns. Algorithm-level performance (O(n²) where O(n log n) is possible) is SE4 LAYERING territory or a `ship-clean-code` smell. IN cares about the production-impact dimension: "will this fall over at 100 RPS?"

On schema files, DA wins over IN — DA owns the schema-correctness dimension while IN owns the migration ops dimension. They can both fire on the same migration (DA on irreversibility, IN on lock-time), but they fingerprint differently and don't collide.

### Finding IDs

| ID | Label | When to fire |
|----|-------|--------------|
| IN1 | PROD-OUTAGE-RISK | A change that could cause an outage: no timeout on external call, blocking migration in a hot table, no rollback path, secrets misconfigured. The "you'll be paged at 3am" tier. |
| IN2 | OBSERVABILITY-GAP | New code path has no metric, no log, or wrong log level. Decision points without traces. |
| IN3 | RESOURCE-LIMITS | Unbounded loop, unbounded queue, unbounded request body, no connection-pool sizing, no memory cap. |
| IN4 | IDEMPOTENCY | Write operation that could be retried (or sent twice by upstream) without idempotency protection. |
| IN5 | CI-PIPELINE | CI workflow change that: unpinns an action, adds a secret reference, increases pipeline runtime > 10x, changes branch protection bypass. |
| IN6 | IAC-DRIFT | IaC change with high blast radius: resource destruction, region migration, IAM permission expansion, network ACL changes. |
| IN7 | PERF-HOTPATH | Operational performance regression in a hot code path: N+1 in a request handler, sync I/O in async context, missing cache on repeated computation. |

### Examples

**IN1 firing:**
```diff
+const resp = await fetch(`https://payment-gateway.example.com/charge`, {
+  method: "POST",
+  body: JSON.stringify(payload),
+});
```
> **[IN1-PROD-OUTAGE-RISK] src/services/payments.ts:55**: External `fetch` to payment-gateway has no timeout. A slow gateway will pile up requests and exhaust event-loop / connection-pool capacity. → Add `signal: AbortSignal.timeout(5000)` and a retry policy with exponential backoff (see `src/lib/http.ts` for the team's standard helper).

**IN2 firing:**
```diff
+app.post("/api/orders", async (req, res) => {
+  const order = await orderService.create(req.body);
+  res.json(order);
+});
```
> **[IN2-OBSERVABILITY-GAP] src/api/orders.ts:12**: New endpoint emits no metric, no structured log. Cannot tell from production telemetry whether this endpoint is healthy. → Add `logger.info("order.created", { user_id, order_id })` and increment a counter `orders.create.success` / `orders.create.failure`.

### Common false-positives

- A timeout-less call to a localhost service (e.g., a sidecar). Note in Confidence; don't fire IN1.
- An "unbounded" loop with a clear external bound (e.g., paginating an external API with hard limit). Suppress.

---

## DA — Senior Data Engineer

**Conditional.** Activates when schema/event/migration files touched. Always escalates to subagent because it needs to read adjacent context (existing schema, downstream consumers).

### Concerns

- Schema changes: column type changes, NOT NULL additions to existing columns, foreign key additions, unique constraints on populated tables.
- Migration reversibility: every migration should have a rollback or a documented one-way decision.
- Data loss risk: DROP COLUMN, DROP TABLE, type narrowing (VARCHAR(255) → VARCHAR(100)).
- Backfill: NOT NULL on an existing column requires backfill before the constraint; same for unique/FK.
- Indexes: missing index on a column queried in WHERE/JOIN, indexes added without `CONCURRENTLY` on hot tables.
- Type precision: `FLOAT` for money, `INT` for timestamps, `VARCHAR(N)` where N might be exceeded.
- Event-contract evolution: removing a field from an Avro/protobuf schema, changing semantics of an event without versioning.
- Retention / PII: new column collecting PII without a documented retention policy.

### Anti-overlap

DA owns **schema correctness and data integrity**. IN owns **migration ops** (lock time, online vs. blocking).

| Concern | DA or IN |
|---------|----------|
| Migration takes a table-level lock for 10 minutes | IN1 |
| Migration drops a column referenced by ETL | DA1 |
| Migration adds NOT NULL without backfill | DA3 + IN1 (both — DA on correctness, IN on operational failure) |
| FLOAT for money | DA5 |
| Migration is not reversible (no `down`) | DA2 |
| Migration uses `CREATE INDEX` without `CONCURRENTLY` on a 100M-row table | IN1 |

When both fire on a single line, they're recorded with their distinct fingerprints — no dedup. The reviewer sees both perspectives.

### Finding IDs

| ID | Label | When to fire |
|----|-------|--------------|
| DA1 | SCHEMA-BREAK | A schema change breaks downstream readers/ETL/replicas without coordination. DROP COLUMN where the column is referenced elsewhere. |
| DA2 | DATA-LOSS-RISK | Type narrowing, irreversible migration without `down`, DROP without archive, truncation. |
| DA3 | BACKFILL-MISSING | NOT NULL added to existing column without a documented backfill step. Same for unique constraints, FK constraints. |
| DA4 | INDEX-MISSING | New WHERE/JOIN on a column without an index, on a table that will have meaningful volume. |
| DA5 | TYPE-PRECISION | Wrong type for the domain: FLOAT for currency, INT for timestamps that need ms or tz, VARCHAR too short, NUMERIC without precision/scale. |
| DA6 | EVENT-CONTRACT | Schema change to a published event without versioning: removing a field, changing semantics of a field, narrowing a union. |
| DA7 | RETENTION-PII | New PII column without retention policy documented, or PII column added to a table that's replicated to non-PII-cleared environments. |

### Examples

**DA1 firing:**
```diff
+ALTER TABLE users DROP COLUMN legacy_external_id;
```
> **[DA1-SCHEMA-BREAK] migrations/0042_drop_legacy_id.sql:1**: Dropping `users.legacy_external_id` — this column is referenced by `analytics-etl` (see `dbt/models/users_dim.sql:14`) and the `customer_export` Lambda. → Coordinate with the data team: deprecate the column for one release, update the ETL, then drop in a follow-up migration.

**DA3 firing:**
```diff
+ALTER TABLE orders ADD COLUMN tier TEXT NOT NULL;
```
> **[DA3-BACKFILL-MISSING] migrations/0043_add_tier.sql:1**: Adding NOT NULL `tier` to existing `orders` table. Existing rows will fail the constraint and the migration will fail on any table with data. → Three-step migration: (1) add column nullable with default, (2) backfill in app or batch, (3) add NOT NULL constraint in a separate migration after backfill completes.

### Common false-positives

- DA1 / DA3 / DA4 on an empty / brand-new table — the column has no readers and no data. Suppress if the table was created in the same PR.
- DA5 (FLOAT for money) when the column is a *rate* or *percentage*, not a currency amount.

---

## FE — Senior Frontend Engineer

**Conditional.** Activates when the diff touches React component files (`*.tsx`, `*.jsx`, or `.ts`/`.js` files declaring `useState`/`useEffect`/returning JSX), framework configs (`next.config.*`, `vite.config.*`, `webpack.config.*`), a11y attributes (`aria-*`, `role=`, `tabIndex`), or library workspaces (`packages/*/src/`). Always escalates to subagent because it needs to read adjacent context: the test file alongside each component (to detect missing axe-state coverage), the package's `index.ts` for exported types, sibling `*.css.ts` token files, and `.changeset/*.md` bodies (for FE7 cross-check).

### Concerns

- **Accessibility contract correctness**: `aria-*` references resolve to elements actually rendered in the DOM; accessible names persist across display/edit DOM swaps; `role="img"` elements have a meaningful label.
- **Controlled-vs-uncontrolled state desync**: `useEffect` that resets internal state/history every time a controlled prop changes; callbacks emitting a subset of internal state the consumer cannot reconstruct.
- **Command-pattern / undo-history completeness**: keyboard handlers that bypass the dispatch path; delete operations that record overlapping commands twice.
- **No-op prop values**: TypeScript union props with variants that no implementation branch matches.
- **SSR / framework constraints**: global CSS imports inside non-entry modules (breaks Next.js App Router); `window`/`document` referenced at module top-level without `'use client'`.
- **Numeric range/clamp at boundaries**: normalized 0..1 values crossing into a consumer expecting that range without clamping.
- **Changeset / release-notes accuracy**: `.changeset/*.md` body claims scope that contradicts what the diff actually ships.
- **Component-library hygiene**: package self-importing its own published asset path.

### Anti-overlap

FE does **not** emit findings about:
- Color contrast, alt-text quality, or aria-label *content* quality (e.g., "this label is too vague") — those are `ship-clean-code` P5 smells.
- React render performance (`useEffect` with no deps array running every render, unnecessary `useMemo`) — stays IN7-PERF-HOTPATH.
- Test design, framework idioms, or AAA structure — TS persona / `ship-tested-code`.
- Public-API contract drift on backend SDKs — SE2.

FE owns **frontend correctness as the user (and consumer) experiences it**: did the component honor the contract it advertises, and does the rendered DOM satisfy the a11y attributes attached to it?

| Concern | FE or other |
|---------|-------------|
| `aria-errormessage` references a non-existent id | FE1 |
| Display element has `aria-label` but the `<input>` it swaps to has none | FE1 |
| `useEffect` resets command history on every prop change | FE2 |
| `onConnect` callback emits `{source, target}` but the internal handler generates an id | FE2 |
| Arrow-key nudges bypass the command-history dispatch | FE3 |
| Two command entries pushed in the same user action with overlapping scope | FE3 |
| TS prop type `'click' \| 'focus'` accepted but only `'click'` is branched on | FE4 |
| `import './styles.css'` inside a non-entry React module | FE5 |
| `viewportRect.width` can be > 1, sent to a consumer expecting [0,1] | FE6 |
| `.changeset/X.md` says "lands later" but X ships in this PR | FE7 |
| Package self-imports its own published asset path | FE8 |
| `useEffect(() => { ... })` with no deps array running every render | IN7 (not FE) |
| Color contrast on text-vs-background | `ship-clean-code` |
| New component has no test file | TS1 |

### Finding IDs

| ID | Label | When to fire |
|----|-------|--------------|
| FE1 | A11Y-CONTRACT-BROKEN | An `aria-*` attribute references a target that isn't rendered in the same component tree, OR an accessible name sits on an element that gets swapped for a different element type (display→input) without the name carrying over, OR a `role="img"` lacks `aria-label`/`aria-labelledby` when no other accessible name applies. |
| FE2 | CONTROLLED-STATE-DESYNC | A controlled component re-syncs internal state from a prop with `useEffect` and resets internal history/selection on that sync, OR a callback emits a subset of internal state (e.g. `{source, target}`) while the internal handler generates an id/timestamp the consumer cannot reproduce, OR an internal command stores more data than the corresponding outward callback emits. |
| FE3 | COMMAND-HISTORY-INCOMPLETE | A keyboard/imperative handler mutates state but bypasses the same command/dispatch path used by click/menu handlers, OR two command entries are pushed in the same user action with overlapping scope (e.g. `delete-node` already cascades incident edges + a separate `delete-edge` is also pushed for those same edges, so undo re-adds them twice). |
| FE4 | NO-OP-PROP-VALUE | A TypeScript union prop accepts a value that no implementation branch matches (e.g. `activate: 'click' \| 'focus'` but no `if (activate === 'focus')` or `switch(activate) { case 'focus':` anywhere). |
| FE5 | SSR-GLOBAL-CSS | Non-entry module contains `import './styles.css'` (Next.js App Router only permits global CSS imports from `layout.tsx`/`_app.tsx`), OR `window`/`document` referenced at module top-level without `'use client'`. |
| FE6 | RANGE-CLAMP-MISSING | A computed normalized value lacks `Math.max(0, Math.min(1, x))` clamping at the boundary, OR an arithmetic output crosses into a downstream consumer's documented numeric range without validation. |
| FE7 | CHANGESET-DRIFT | A `.changeset/*.md` body describes scope that contradicts the diff. Includes "lands in next iteration" / "follow-up PR will add X" claims that conflict with code present in the same PR. |
| FE8 | REDUNDANT-INTERNAL-IMPORT | A package internally imports its own published asset path (e.g. `@scope/pkg/styles.css` from inside `packages/pkg/src/`), or a module both exports a side-effecting stylesheet via `package.json#exports` AND internally `import`s it. |

### Examples

**FE1 firing (a11y target missing):**
```diff
+<input
+  aria-invalid={error ? true : undefined}
+  aria-errormessage={error ? `${rest.id ?? 'inline-edit'}-error` : undefined}
+  className={inputStyles({ size, tone: error ? 'err' : 'default' })}
+/>
```
> **[FE1-A11Y-CONTRACT-BROKEN] packages/ui/src/components/InlineEdit/InlineEdit.tsx:234**: `aria-errormessage` references `${id}-error`, but no element with that id is rendered in the component tree. The string returned by `validate()` lives only in `error` state — sighted users get the red border, AT users get a dangling ARIA reference. → Render the error inline: `{error && <p id={`${id}-error`} role="alert" className="text-err mt-1 text-[11px]">{error}</p>}` and wrap the `<input>` + `<p>` in a fragment.

**FE1 firing (accessible-name carryover):**
```diff
 if (!editing) {
   return <button aria-label={`Edit ${value}`} onClick={startEdit}>{value}</button>;
 }
-return <input value={draft} onChange={...} />;
+return <input value={draft} onChange={...} />;
```
> **[FE1-A11Y-CONTRACT-BROKEN] packages/ui/src/components/InlineEdit/InlineEdit.tsx:223**: When the component swaps from display to edit mode, the display element's `aria-label="Edit ${value}"` doesn't carry to the `<input>`. Screen readers announce nothing meaningful for the input that just appeared. → Apply the same computed label to the input: `<input aria-label={`Editing ${value}`} ...>` (or `aria-labelledby` pointing to a stable id).

**FE2 firing (history reset on every controlled-prop change):**
```diff
+useEffect(() => {
+  setNodes(adapter.nodesToReactFlow(elements));
+  setEdges(adapter.edgesToReactFlow(elements));
+  history.reset();
+}, [elements]);
```
> **[FE2-CONTROLLED-STATE-DESYNC] packages/graph-editor/src/GraphEditorCanvas.tsx:175**: This effect re-syncs internal state from the `elements` prop and resets history on every change. Consumers who update `elements` in response to `onNodeMove`/`onConnect` (as the docs examples do) will see history cleared after every edit — undo/redo is unusable. → Treat `elements` as initial state (rename to `initialElements`, sync only on mount + an explicit `resetKey`), or move history into the controlled value.

**FE2 firing (callback emits less than the internal command stores):**
```diff
+function handleConnect(params: { source: string; target: string }) {
+  const newEdge = { id: `e-${Date.now()}`, ...params };
+  applyCommand({ kind: 'add-edge', edge: newEdge });
+  onConnect?.({ source: params.source, target: params.target });
+}
```
> **[FE2-CONTROLLED-STATE-DESYNC] packages/graph-editor/src/GraphEditorCanvas.tsx:231**: `handleConnect` generates an internal edge id (`e-${Date.now()}`) but the outward `onConnect` callback only emits `{source, target}`. A controlled consumer will create an edge with a different id. Internal history/selection/edge-delete events then diverge from the consumer's persisted graph. → Either include the generated id in the callback (`onConnect?.({ source, target, id: newEdge.id })`) or accept a `createEdgeId` factory prop so the consumer chooses.

**FE3 firing (keyboard bypasses command dispatch):**
```diff
+useGraphEditorKeyboard({
+  onArrow: (direction) => {
+    const change = makePositionChange(direction);
+    baseOnNodesChange([change]);  // bypasses applyCommand → not in history
+  },
+});
```
> **[FE3-COMMAND-HISTORY-INCOMPLETE] packages/graph-editor/src/GraphEditorCanvas.tsx:387**: Arrow-key nudges flow through `baseOnNodesChange` while drag-end goes through `applyCommand`. `⌘Z` will undo drags but not nudges, and the keyboard path silently corrupts history when interleaved with mouse actions. → Route both through `applyCommand({ kind: 'move-node', from, to })`.

**FE3 firing (overlapping command entries):**
```diff
+function handleDelete() {
+  deleteSelectedNodes();  // applyCommand({ kind: 'delete-node', incidentEdges })
+  deleteSelectedEdges();  // applyCommand({ kind: 'delete-edge', edge }) for each
+}
```
> **[FE3-COMMAND-HISTORY-INCOMPLETE] packages/graph-editor/src/GraphEditorCanvas.tsx:397**: When Delete is pressed with both nodes and edges selected, `deleteSelectedNodes()` records a `delete-node` command that includes incident edges in its inverse, AND `deleteSelectedEdges()` records `delete-edge` for each selected edge. If a selected edge is incident to a selected node, undo re-adds it twice (duplicate edges). → Dedup: before pushing `delete-edge` commands, subtract edges already covered by a `delete-node` in this batch.

**FE4 firing (dead variant):**
```diff
 export type Activation = 'click' | 'focus';
 export interface InlineEditProps {
   activate?: Activation;
   ...
 }

 function handleClick() {
   if (activate === 'click') startEdit();
 }
```
> **[FE4-NO-OP-PROP-VALUE] packages/ui/src/components/InlineEdit/InlineEdit.tsx:86**: `activate` accepts `'focus'`, but no implementation branch on `activate === 'focus'` exists. The prop value is type-system-valid and silently does nothing at runtime. → Either implement focus activation (start edit on `onFocus` when `activate === 'focus'`), or remove `'focus'` from the `Activation` union.

**FE5 firing:**
```diff
+import './styles.css';
+
+export function GraphEditorCanvas(props) { ... }
```
> **[FE5-SSR-GLOBAL-CSS] packages/graph-editor/src/GraphEditorCanvas.tsx:34**: Global CSS imported inside a non-entry module. Next.js App Router only permits global CSS imports from `layout.tsx`/`_app.tsx`. The package already exports `@ship-it-ui/graph-editor/styles.css` for consumer-side import. → Drop the internal import; document that consumers must import the stylesheet once from their entry module.

**FE6 firing:**
```diff
+function computeViewportRect(viewport, bbox) {
+  const tl = projectToBbox(viewport.tl, bbox);
+  const br = projectToBbox(viewport.br, bbox);
+  return { x: clamp01(tl.x), y: clamp01(tl.y), width: br.x - tl.x, height: br.y - tl.y };
+}
```
> **[FE6-RANGE-CLAMP-MISSING] packages/graph-editor/src/MiniMap.tsx:92**: `viewportRect.width/height` can exceed 1 when the viewport is panned past the graph bbox. `GraphMinimap` expects normalized 0..1 fractions; values > 1 produce rendering artifacts (rect extends past the minimap frame). → Clamp width/height using the already-clamped top-left: `width: clamp01(br.x) - clamp01(tl.x)`, same for height.

**FE7 firing:**
```diff
+---
+"@ship-it-ui/graph-editor": minor
+---
+
+Initial GraphEditorCanvas surface. Renders nodes/edges and emits onNodeMove/onConnect/onSelect.
+
+Keyboard handling, undo/redo, mini-map, and the +Add palette land in the next iteration.
```
> **[FE7-CHANGESET-DRIFT] .changeset/add-graph-editor-canvas.md:7**: Changeset says keyboard/undo/mini-map/+Add "land in the next iteration", but those behaviors are implemented in this PR (see `keyboard.ts`, `history.ts`, `MiniMap.tsx`, and the `applyCommand({ kind: 'add-node' })` path in `GraphEditorCanvas.tsx`). Release notes will be misleading and downstream consumers will not know the surface is available. → Either remove this changeset (a sibling changeset already covers the behaviors) or rewrite the body to describe what actually ships.

**FE8 firing:**
```diff
+// inside packages/graph-editor/src/GraphEditorCanvas.tsx
+import '@ship-it-ui/graph-editor/styles.css';
```
> **[FE8-REDUNDANT-INTERNAL-IMPORT] packages/graph-editor/src/GraphEditorCanvas.tsx:34**: Package internally imports its own published asset path. This forces a self-loop through the package resolver and tends to break under bundlers that haven't resolved the workspace yet. → Use a relative import (`import './styles.css'`) if internal, or — better, per FE5 — drop the internal import entirely and document consumer-side import.

### Common false-positives

- **FE1 on `aria-label={label}` where `label` is a ReactNode at the type level but a string at runtime.** The fallback path matters; the rubric only fires when the fallback branch does the wrong thing for AT.
- **FE2 on small controlled components without internal history or command pattern.** The desync only matters when the component owns multi-step state. If the component is a stateless render of `value` + emits `onChange`, FE2 doesn't apply.
- **FE5 when the file IS the entry module** (`layout.tsx`, `_app.tsx`, `page.tsx`, `main.tsx`, `index.html`-loaded entry). Do not fire.
- **FE6 when the value is already clamped at the producer.** One side of the boundary is enough; only fire when neither side clamps.
- **FE7 when the changeset content matches the diff.** The mismatch IS the fire condition. Generic / boilerplate changeset bodies are not FE7.
- **FE4 on union props whose unmatched variant is intentionally a "future" surface** if the variant is annotated `/** @experimental */` or `@deprecated`. Note in Confidence; don't fire.

---

## TS — Test Reviewer

**Always on, delegation-only.** TS exists to surface the gap signal at the PR-review level. All test-quality depth (AAA, mocking, flakiness, naming) defers to `/ship-tested-code`.

### Concerns

TS owns exactly two questions:
1. Did the PR add or substantively modify production code? If yes, are there test files added or modified?
2. Does the PR description say it fixes a bug (`fixes #N`, `closes #N`)? If yes, is there a test that captures the regression?

### Anti-overlap

TS does **not** evaluate test quality. The test code style, framework idioms, mocking strategy, AAA structure — all of that is `ship-tested-code`. TS only computes a ratio + a binary regression-test check.

### Finding IDs

| ID | Label | When to fire |
|----|-------|--------------|
| TS1 | NO-TEST-FOR-NEW-CODE | `code` bucket files modified with ≥ 30 added lines, AND no `test` bucket files added or modified. Threshold tunable in `overrides.md`. |
| TS2 | NO-REGRESSION-FOR-BUGFIX | PR description matches `(fixes|closes|resolves) #\d+` AND no `test` bucket file added or modified. |

Both findings ALWAYS render as a single delegation bullet, never as a long inline finding:

> **[TS1-NO-TEST-FOR-NEW-CODE]** PR adds 247 lines of production code across 3 files with no test files added. → Run `/ship-tested-code` against this PR — it will identify which files need tests, what the right level is (unit / integration), and whether the diff introduces testability problems.

> **[TS2-NO-REGRESSION-FOR-BUGFIX]** PR description references `fixes #4711` but no test was added. → A bug fix that ships without a test will recur. Run `/ship-debugged-code` to design the regression test, then `/ship-tested-code` to review it.

### Decision-matrix interaction

- TS1 alone → COMMENT (advisory; can be ignored if author already plans to ship tests in a follow-up).
- TS2 alone → REQUEST_CHANGES. A bugfix without a regression test is the textbook fix-that-doesn't-stick pattern.

### Common false-positives

- PR is docs-only or config-only — no `code` bucket files touched. TS doesn't fire.
- PR deletes code (refactor removing dead module). TS adjusts: only fire TS1 if NET addition ≥ 30 lines.
- Test file was modified but not added — count as "tests touched", do not fire TS1 even if the ratio is unfavorable. The author engaged with tests; trust them.

---

## Persona-pass orchestration order

The order matters for dedup. Within the orchestrator's context, run:

1. **SC** first — highest-priority, scans everything, sets the strongest fingerprints. Other personas dedup against SC.
2. **DA** second (if activated) — owns schema priority. Runs as subagent in parallel with IN-deep and FE.
3. **FE** third (if activated) — frontend-correctness specialist. Runs as subagent in parallel with DA and IN-deep.
4. **IN** fourth (light or deep) — operational dimension.
5. **SE** fifth — synthesis lead; reviews the diff after the specialist personas have set their fingerprints, so SE can focus on cross-cutting concerns. On TSX files, FE2-CONTROLLED-STATE-DESYNC wins over SE2-CONTRACT-DRIFT in dedup (FE2 framing is more actionable for component consumers).
6. **TS** last — computes ratios from final file list and PR description.

This ordering is intentional: specialists first (they have the strongest claim on their domain), generalists last (they fill remaining gaps).
