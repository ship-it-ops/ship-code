# TypeScript / JavaScript Debugging Idioms

## Browser DevTools

- `debugger;` statement pauses execution when DevTools is open — like a one-shot breakpoint that lives in the code
- **Conditional breakpoints**: right-click a line in the Sources panel → "Add conditional breakpoint" → enter a JS expression. Pauses only when true. Critical for bugs that happen on iteration 1000 of a loop
- **Logpoints** (Chrome 73+, VS Code): like a `console.log` you can add without editing the file. Right-click → "Add logpoint" → write the message with `${expr}` interpolation
- **DOM breakpoints**: right-click any DOM node in Elements panel → "Break on" → subtree modifications / attribute modifications / node removal. Finds the code that mutated something unexpected
- **Event listener breakpoints**: Sources panel → Event Listener Breakpoints sidebar → check categories (e.g., "Mouse > click"). Pauses on any handler
- **XHR / fetch breakpoints**: Sources panel → XHR/fetch Breakpoints → add URL substring. Pauses when matching request fires

## Node.js Debugging

- Run with `node --inspect script.js` (or `--inspect-brk` to pause on entry) and attach Chrome DevTools at `chrome://inspect` or VS Code's "Attach to Node" config
- `console.trace(msg)` prints the current stack trace
- `process.on("uncaughtException", handler)` for last-resort logging in production
- `process.on("unhandledRejection", handler)` for missed promise rejections — **always set this in production**, otherwise rejections silently fail

## VS Code Debug Configurations

- Built-in support for Node, Chrome, Edge, Deno, Bun
- `launch.json` patterns: "Launch via npm", "Attach to Node Process", "Launch Chrome against localhost", "Jest current file"
- Set breakpoints by clicking the gutter; conditional/hit-count breakpoints via right-click

## Stack Traces

- Source maps are **essential** for debugging transpiled/minified code. Verify your build emits them (`devtool: "source-map"` in webpack; `sourcemap: true` in Vite)
- `Error.cause` (ES2022): `throw new Error("operation failed", { cause: original })` preserves the original error
- `Error.captureStackTrace(target, constructorOpt)` (Node) gives precise stacks for custom error classes
- In async code, default stack traces are useless (they show only the microtask boundary). Use `--async-stack-traces` (default on in modern Node) for full async chains

## Logging for Debugging

- `console.log` is fine for development; use a real logger (`pino`, `winston`, `bunyan`) for anything that hits production
- `console.dir(obj, { depth: null })` for deeply nested objects (default depth is 2)
- `console.table(rows)` renders arrays of objects as a table — useful for comparing state across many items
- `console.group(label) ... console.groupEnd()` for nested log structure
- `console.time(label) / console.timeEnd(label)` for ad-hoc timing measurements
- `console.assert(condition, msg)` logs only when condition is false — cheap inline invariant checks

## Inspecting State

- `JSON.stringify(obj, null, 2)` for structured view (but loses functions, undefined, circular refs)
- Use `structuredClone(obj)` to snapshot state for later comparison
- `Object.keys`, `Object.entries`, `Object.getOwnPropertyDescriptors` for full state inspection
- In Chrome DevTools console: `copy(obj)` copies to clipboard, `$_` is the last expression, `$0` is the selected DOM node
- React DevTools: inspect component state, props, hooks; profile re-renders. Always install for React apps
- Vue DevTools / Redux DevTools / Zustand DevTools for state libraries

## Common JS/TS Bug Patterns

- **`this` binding lost**: `arr.map(this.method)` — `this` is undefined inside. Fix: `arr.map((x) => this.method(x))` or `arr.map(this.method.bind(this))`.
- **Floating promise**: `async` function called without `await`. Symptom: code "after" runs before the async work, or rejection silently swallowed. Fix: always `await`, or `.then().catch()`, or use the `no-floating-promises` ESLint rule.
- **`typeof null === "object"`**: classic gotcha when type-checking. Fix: `value === null` separately.
- **`==` vs `===`**: `[] == false` is `true`, `null == undefined` is `true`. Always use `===`.
- **Mutating a prop**: child mutates an object received from parent. Symptom: React doesn't re-render because reference is unchanged. Fix: spread to create a new reference.
- **Closure over loop variable with `var`**: `for (var i = 0; ...) setTimeout(() => console.log(i))` prints final value. Fix: `let` (block-scoped) or `for...of`.
- **`Date` parsing**: `new Date("2025-01-15")` is UTC; `new Date("2025/01/15")` is local. Always use ISO 8601 with timezone.
- **Number precision**: `0.1 + 0.2 === 0.3` is `false`. Use a tolerance comparison, or libraries like `decimal.js` for financial code.
- **Array sparse holes**: `[1, , 3].length` is 3 but `[1, , 3][1]` is undefined. `Array.from` and most array methods normalize these inconsistently.
- **`setState` in React is async**: reading state immediately after `setState` shows the old value. Use the functional updater `setState(prev => ...)` or the next render.

## Profiling

- **Chrome DevTools Performance tab**: records CPU + rendering + network in one timeline. Use for "why is this slow" questions
- **Chrome DevTools Memory tab**: heap snapshots, allocation timelines, retainer trees. Use for memory leaks
- **`--cpu-prof` flag for Node.js**: writes a `.cpuprofile` you can open in Chrome DevTools
- **Lighthouse**: end-to-end performance audit for web pages, including Core Web Vitals

## Network Debugging

- DevTools Network tab: filter by type, slow-throttle the connection, capture HAR file
- **`fetch` failures don't include the response body by default** — log `await response.text()` to see what the server actually returned
- CORS errors show in the console; the actual response is unreadable from JS but visible in the Network tab
- `--inspect-brk` + Node + a `debugger;` in your request handler lets you step through a real HTTP request

## Remote Debugging

- VS Code "Attach to Node Process" works on any reachable Node with `--inspect`
- For Kubernetes: `kubectl port-forward pod/X 9229:9229` then attach VS Code
- Never leave `--inspect` open on a public port — it allows arbitrary code execution

## Common Traps

- **Source maps missing in production builds**: error reports point at minified line:column, useless for debugging. Upload source maps to Sentry/Datadog or your error tracker.
- **`console.log` left in production**: pollutes logs, can leak data. Use a real logger and a linter rule for `no-console`.
- **`vi.fn()` / `jest.fn()` state leaks between tests**: clear with `vi.clearAllMocks()` / `jest.clearAllMocks()` in `afterEach`.
- **Promise rejections lost in `.forEach`**: `arr.forEach(async fn)` does not await. Use `for...of` with `await` or `Promise.all(arr.map(fn))`.
