# TypeScript / React Test Transformations

## Example 1: Implementation Details → Behavior-Based

### Before
```tsx
import { render } from '@testing-library/react';
import { ProductList } from './ProductList';

jest.mock('./hooks/useProducts', () => ({
  useProducts: () => ({
    data: [{ id: 1, name: 'Widget', price: 29.99 }],
    loading: false,
    error: null,
  }),
}));

jest.mock('./components/ProductCard', () => ({
  ProductCard: ({ product }: any) => <div data-testid="product">{product.name}</div>,
}));

test('renders products', () => {
  const { container } = render(<ProductList />);
  expect(container.querySelectorAll('[data-testid="product"]')).toHaveLength(1);
  expect(container).toMatchSnapshot();
});
```

**Problems:**
- Mocks the hook AND the child component — tests almost nothing (M1)
- Uses `container.querySelectorAll` instead of accessible queries (N/A)
- Snapshot of a mostly-mocked tree — meaningless (A3)
- No error or loading state tests (C1)
- Single vague test name (N3)

### After
```tsx
import { render, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { ProductList } from './ProductList';

const mockProducts = [
  { id: 1, name: 'Widget', price: 29.99, inStock: true },
  { id: 2, name: 'Gadget', price: 49.99, inStock: false },
];

const server = setupServer(
  http.get('/api/products', () => HttpResponse.json(mockProducts))
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('displays loading indicator while fetching', () => {
  render(<ProductList />);
  expect(screen.getByRole('progressbar')).toBeInTheDocument();
});

test('renders product names and prices after loading', async () => {
  render(<ProductList />);

  await waitFor(() => {
    expect(screen.getByText('Widget')).toBeInTheDocument();
  });

  expect(screen.getByText('$29.99')).toBeInTheDocument();
  expect(screen.getByText('Gadget')).toBeInTheDocument();
  expect(screen.getAllByRole('listitem')).toHaveLength(2);
});

test('shows out-of-stock badge for unavailable products', async () => {
  render(<ProductList />);

  await waitFor(() => {
    expect(screen.getByText('Gadget')).toBeInTheDocument();
  });

  const gadgetCard = screen.getByText('Gadget').closest('li')!;
  expect(within(gadgetCard).getByText(/out of stock/i)).toBeInTheDocument();
});

test('displays error message when API fails', async () => {
  server.use(
    http.get('/api/products', () => HttpResponse.error())
  );

  render(<ProductList />);

  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(/failed to load/i);
  });
});

test('shows empty state when no products exist', async () => {
  server.use(
    http.get('/api/products', () => HttpResponse.json([]))
  );

  render(<ProductList />);

  await waitFor(() => {
    expect(screen.getByText(/no products found/i)).toBeInTheDocument();
  });
});
```

**Improvements:**
- MSW mocks at network level — real hooks, components, and rendering execute
- Accessible queries: `getByRole`, `getByText` — verifies accessibility
- Tests loading, success, error, and empty states
- Each test has a descriptive name and tests one behavior
- No snapshots — behavioral assertions are specific and meaningful

---

## Example 2: Brittle Selectors → Accessible Queries

### Before
```tsx
test('submits form', async () => {
  const { container } = render(<ContactForm onSubmit={mockFn} />);

  const nameInput = container.querySelector('#name-input');
  const emailInput = container.querySelector('input[type="email"]');
  const submitBtn = container.querySelector('.btn-primary');

  fireEvent.change(nameInput!, { target: { value: 'Jane' } });
  fireEvent.change(emailInput!, { target: { value: 'jane@test.com' } });
  fireEvent.click(submitBtn!);

  expect(mockFn).toHaveBeenCalledTimes(1);
});
```

**Problems:**
- CSS selectors break on any styling change (D7)
- `fireEvent` doesn't simulate real user behavior
- Non-null assertions (`!`) hide potential test bugs
- Assertion only checks call count, not arguments (A1)

### After
```tsx
test('submits form with user input', async () => {
  const handleSubmit = vi.fn();
  const user = userEvent.setup();
  render(<ContactForm onSubmit={handleSubmit} />);

  await user.type(screen.getByLabelText(/name/i), 'Jane Doe');
  await user.type(screen.getByLabelText(/email/i), 'jane@test.com');
  await user.click(screen.getByRole('button', { name: /send/i }));

  expect(handleSubmit).toHaveBeenCalledWith(
    expect.objectContaining({
      name: 'Jane Doe',
      email: 'jane@test.com',
    })
  );
});
```

**Improvements:**
- `getByLabelText` and `getByRole` — accessible, resilient to styling changes
- `userEvent` simulates real typing and clicking (focus, keypress sequence)
- Assertion verifies the submitted data, not just that something was called
- No `!` assertions — queries throw if element not found

---

## Example 3: Missing Async Handling → Proper Waits

### Before
```tsx
test('loads user profile', async () => {
  render(<UserProfile userId="123" />);

  // Wait for data to load
  await new Promise(resolve => setTimeout(resolve, 2000));

  expect(screen.getByText('John Doe')).toBeInTheDocument();
});
```

**Problems:**
- `setTimeout` is arbitrary — flaky in CI (F1)
- 2 seconds wasted even when data loads in 50ms
- No error handling test

### After
```tsx
test('displays user name after loading', async () => {
  render(<UserProfile userId="123" />);

  expect(await screen.findByText('John Doe')).toBeInTheDocument();
  expect(screen.getByText('john@example.com')).toBeInTheDocument();
});

test('shows loading skeleton while fetching', () => {
  render(<UserProfile userId="123" />);
  expect(screen.getByRole('progressbar')).toBeInTheDocument();
});

test('displays error when user not found', async () => {
  server.use(
    http.get('/api/users/999', () => HttpResponse.json(null, { status: 404 }))
  );

  render(<UserProfile userId="999" />);

  expect(await screen.findByRole('alert')).toHaveTextContent(/user not found/i);
});
```

**Improvements:**
- `findByText` waits automatically — no sleep, no arbitrary timeout
- Tests all three states: loading, success, error
- Fast: resolves as soon as the element appears
- Deterministic: no timing-dependent assertions
