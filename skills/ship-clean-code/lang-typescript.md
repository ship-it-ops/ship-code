# TypeScript / JavaScript Clean Code Idioms

## Naming Conventions

- `camelCase` for variables, functions, methods, properties
- `PascalCase` for classes, interfaces, type aliases, enums, React components
- `UPPER_SNAKE_CASE` for true constants (compile-time known values)
- Prefix interfaces with `I` only if project convention requires it (generally avoid)

## Type Safety

- **Never use `any` in production code.** Use `unknown` when the type is truly unknown, then narrow with type guards.
- Add explicit return types on all exported/public functions
- Use discriminated unions over type assertions for variant types
- Use `as const` for literal types and exhaustive switch checks
- Leverage `satisfies` operator for type-safe object literals (TS 4.9+)
- Use branded types for domain IDs (`type UserId = string & { __brand: 'UserId' }`)

## Null Safety

- Enable `strictNullChecks` in tsconfig
- Use optional chaining (`?.`) over nested null checks
- Use nullish coalescing (`??`) over logical OR (`||`) for default values
- Prefer returning `undefined` over `null` (or use Result/Option pattern)
- Never use `!` non-null assertion except in test setup

## Error Handling

- Use typed error classes extending `Error`
- Always set `Error.cause` when wrapping errors (ES2022+)
- Handle all Promise rejections — never leave `.catch()` missing on floating promises
- Use `try/catch` with `async/await` instead of `.then().catch()` chains
- Prefer Result types (`{ok: true, data} | {ok: false, error}`) for expected failures

## Modern Patterns

- `const`/`let` only — never `var`
- `===` and `!==` only — never `==` or `!=`
- Destructuring for cleaner parameter access
- Spread operator for immutable object/array operations
- Template literals over string concatenation
- `for...of` over `for...in` for arrays (or `forEach`/`map`/`filter`)
- Arrow functions for short callbacks, named functions for complex logic

## React-Specific (when applicable)

- Function components over class components
- Custom hooks to extract reusable stateful logic
- `useCallback`/`useMemo` only when there's a measured performance need
- Prefer controlled components
- Keep components under 100 lines; extract sub-components

## Common Traps

- **Truthy/falsy confusion**: `0`, `""`, `NaN` are falsy — use explicit checks when these are valid values.
- **Event listener leaks**: Always pair `addEventListener` with `removeEventListener` (or use AbortController).
- **Floating promises**: `async` function called without `await` — unhandled rejections silently fail.
- **Closure over loop variable**: Use `let` not `var` in for loops, or use `for...of`.
- **Object mutation**: Spread creates shallow copies only — deep nested objects still share references.

## Module Organization

- One export per file for major abstractions (classes, large functions)
- Barrel files (`index.ts`) for clean public APIs — but avoid deep re-export chains
- Use path aliases in tsconfig to avoid `../../../` imports
- Co-locate tests with source files (`foo.ts` / `foo.test.ts`)

## Async Patterns

- Prefer `async/await` over raw Promises for readability
- Use `Promise.all()` for independent concurrent operations
- Use `Promise.allSettled()` when some failures are acceptable
- Avoid mixing callbacks and promises — convert callbacks with `util.promisify` or manual wrapping
- Use `AbortController` for cancellable async operations

## Performance Considerations

- Avoid premature optimization — measure first with profiling tools
- Use `Map`/`Set` over plain objects for frequent additions/deletions
- Prefer `Object.freeze()` or `as const` for truly immutable data
- Lazy-load heavy modules with dynamic `import()`
- Debounce/throttle event handlers that fire rapidly (scroll, resize, input)

## Testing Conventions

- Use `describe`/`it` hierarchy: `describe("UserService")` > `describe("createUser")` > `it("should throw when email is invalid")`
- Prefer `@testing-library/react` with `getByRole`/`getByLabelText` over `getByTestId` — test accessibility, not implementation
- Use `userEvent` over `fireEvent` — it simulates real browser behavior (typing, clicking, tabbing)
- Use MSW (Mock Service Worker) for API mocking in integration tests, not `jest.fn()` on fetch
- Snapshot testing: use only for small, stable serializable outputs (`toMatchInlineSnapshot`). Never snapshot large component trees
- Always `await` in async tests — missing `await` causes false passes
- Clean up: use `afterEach(() => cleanup())` or configure automatic cleanup
- For React: wrap state updates in `act()` or use `waitFor()` from testing-library
