# TypeScript / JavaScript Testing Idioms

## Test Runner & Conventions

- **Vitest** (preferred for Vite-based projects) or **Jest** as test runner
- Name test files `*.test.ts` or `*.spec.ts`
- Use `describe`/`it`/`test` hierarchy. `describe` groups related tests; `it` reads as a sentence
- Use `beforeEach`/`afterEach` for per-test setup/teardown; `beforeAll`/`afterAll` sparingly

```typescript
describe('CartService', () => {
  describe('addItem', () => {
    it('increases item count', () => { /* ... */ });
    it('rejects negative quantities', () => { /* ... */ });
  });

  describe('checkout', () => {
    it('creates order with correct total', () => { /* ... */ });
    it('fails when cart is empty', () => { /* ... */ });
  });
});
```

## Component Testing (React / Vue / Angular)

- Use **Testing Library** (React Testing Library, Vue Testing Library, Angular Testing Library)
- Query priority: `getByRole` > `getByLabelText` > `getByText` > `getByPlaceholderText` > `getByTestId`
- `getByTestId` is a last resort. Every `getByTestId` is a missed opportunity to verify accessibility
- Use `userEvent.setup()` over `fireEvent` for realistic user interactions
- Test what the user sees, not internal component state

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('displays error when submitting empty form', async () => {
  const user = userEvent.setup();
  render(<LoginForm onSubmit={vi.fn()} />);

  await user.click(screen.getByRole('button', { name: /sign in/i }));

  expect(screen.getByRole('alert')).toHaveTextContent('Email is required');
});
```

## API Mocking with MSW

- Use **Mock Service Worker (MSW)** for mocking APIs at the network level
- Do NOT mock your own API client, data layer, or hooks -- mock the network so real code executes
- Define handlers in a shared file; use `server.use()` for per-test overrides

```typescript
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const handlers = [
  http.get('/api/products', () => HttpResponse.json(mockProducts)),
];

const server = setupServer(...handlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('shows error when API fails', async () => {
  server.use(
    http.get('/api/products', () => HttpResponse.error())
  );
  render(<ProductList />);
  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(/failed to load/i);
  });
});
```

## Async Testing

- Use `waitFor` and `findBy*` queries for async assertions -- never `sleep` or `setTimeout`
- Use `vi.useFakeTimers()` / `jest.useFakeTimers()` for timer-dependent code
- Always `await` async operations before assertions

```typescript
// GOOD: wait for UI to update
await user.click(submitButton);
await waitFor(() => {
  expect(screen.getByText('Success')).toBeInTheDocument();
});

// BAD: arbitrary wait
await new Promise(resolve => setTimeout(resolve, 3000));
expect(screen.getByText('Success')).toBeInTheDocument();
```

## E2E Testing with Playwright

- **Playwright** is the recommended E2E framework (over Cypress for new projects)
- Use page functions over page object classes for lighter abstraction
- Wait for network responses, not arbitrary timeouts
- Use `storageState` for authenticated tests (avoid logging in through UI every test)

```typescript
test('complete checkout flow', async ({ page }) => {
  await page.goto('/products');
  await page.getByRole('button', { name: /add to cart/i }).first().click();
  await page.getByRole('link', { name: /cart/i }).click();
  await page.getByRole('button', { name: /checkout/i }).click();

  await page.waitForResponse(resp =>
    resp.url().includes('/api/orders') && resp.status() === 201
  );

  await expect(page.getByRole('heading', { name: /order confirmed/i })).toBeVisible();
});
```

## Mock Functions & Spies

- Use `vi.fn()` (Vitest) or `jest.fn()` for mock functions
- Use `vi.spyOn()` to spy on existing methods without replacing them
- Always restore mocks: `vi.restoreAllMocks()` in `afterEach`

```typescript
test('calls onSubmit with form data', async () => {
  const handleSubmit = vi.fn();
  const user = userEvent.setup();
  render(<ContactForm onSubmit={handleSubmit} />);

  await user.type(screen.getByLabelText(/name/i), 'Jane Doe');
  await user.click(screen.getByRole('button', { name: /send/i }));

  expect(handleSubmit).toHaveBeenCalledWith(
    expect.objectContaining({ name: 'Jane Doe' })
  );
});
```

## Property-Based Testing

- Use **fast-check** for property-based testing
- Test invariants: roundtrip encode/decode, sort stability, idempotence

```typescript
import fc from 'fast-check';

test('JSON roundtrip preserves data', () => {
  fc.assert(
    fc.property(fc.anything(), (value) => {
      expect(JSON.parse(JSON.stringify(value))).toEqual(value);
    })
  );
});
```

## Snapshot Testing

- Use **inline snapshots** for small, critical outputs only: `toMatchInlineSnapshot()`
- Never snapshot entire components or large objects -- use behavioral assertions instead
- When using snapshots, review every diff in PRs. If reviewers rubber-stamp, the snapshots have no value

```typescript
// GOOD: Small, stable, inline
test('formatPrice handles currencies', () => {
  expect(formatPrice(29.99, 'USD')).toMatchInlineSnapshot(`"$29.99"`);
  expect(formatPrice(29.99, 'EUR')).toMatchInlineSnapshot(`"€29.99"`);
});

// BAD: Large component tree snapshot
test('renders dashboard', () => {
  const { container } = render(<Dashboard />);
  expect(container).toMatchSnapshot(); // Never do this
});
```

## Performance Testing

- Use **size-limit** for bundle size budgets in CI. Fail the build if a PR increases bundle size
- Use Lighthouse CI for Core Web Vitals thresholds (LCP, CLS, INP)

```json
{
  "size-limit": [
    { "path": "dist/index.js", "limit": "75 kB", "gzip": true },
    { "path": "dist/vendor.js", "limit": "120 kB", "gzip": true }
  ]
}
```

## Accessibility Testing

- Run **axe-core** via `jest-axe` or `@axe-core/playwright` in every component test
- One line of code catches real accessibility issues. No excuse to skip it

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

test('ProductCard is accessible', async () => {
  const { container } = render(<ProductCard product={mockProduct} />);
  expect(await axe(container)).toHaveNoViolations();
});
```

## Type-Level Testing

- Use **expect-type** or **tsd** to verify TypeScript types at compile time
- Catches type regressions that runtime tests miss

```typescript
import { expectTypeOf } from 'expect-type';

test('createUser returns User type', () => {
  expectTypeOf(createUser).returns.toEqualTypeOf<User>();
});
```

## Common Traps

- **Not awaiting async operations**: Assertions run before state updates. Always `await` user interactions and use `waitFor`.
- **Testing with `fireEvent` instead of `userEvent`**: `fireEvent` dispatches raw DOM events. `userEvent` simulates real user behavior (focus, type, click sequence).
- **Mocking modules instead of network**: `jest.mock('./api')` tests wiring, not behavior. Use MSW to mock at the network level.
- **Snapshot proliferation**: Every component gets `toMatchSnapshot()`. Every PR updates 30 snapshots. Reviewers stop reading. Snapshots become stale lies.
- **Forgetting to cleanup**: Missing `server.resetHandlers()` or `vi.restoreAllMocks()` causes state leakage between tests.
