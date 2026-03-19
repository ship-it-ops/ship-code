# TypeScript: Before & After

## Scenario
An order-processing API handler that validates a request, checks inventory,
applies discounts, creates the order, and sends a confirmation email.

---

## Before (8 violations)

```typescript
async function handleOrder(req: any, res: any) {
  var items = req.body.items;
  var user = req.body.user;

  if (items) {
    if (items.length > 0) {
      if (user) {
        var total = 0;
        for (var i = 0; i < items.length; i++) {
          var item: any = items[i];
          item.price = item.price * item.qty;          // mutates input
          total += item.price;

          if (item.status == "available") {
            if (item.qty > 0) {
              // apply discount
              if (user.tier == "gold") {
                item.price = item.price * 0.9;
                total = total - (item.price * 0.1);
              } else if (user.tier == "silver") {
                item.price = item.price * 0.95;
              }
            }
          }
        }

        fetch("/api/inventory/reserve", {
          method: "POST",
          body: JSON.stringify({ items: items }),
        }).then(function (invRes) {
          invRes.json().then(function (invData: any) {
            fetch("/api/orders", {
              method: "POST",
              body: JSON.stringify({
                user: user.id,
                items: items,
                total: total,
                status: "pending",
              }),
            }).then(function (orderRes) {
              orderRes.json().then(function (orderData: any) {
                fetch("/api/email/send", {
                  method: "POST",
                  body: JSON.stringify({
                    to: user.email,
                    subject: "Order Confirmed",
                    orderId: orderData.id,
                  }),
                });
                res.json({ status: "ok", orderId: orderData.id });
              });
            });
          });
        });
      } else {
        res.json({ status: "error", msg: "no user" });
      }
    } else {
      res.json({ status: "error", msg: "empty cart" });
    }
  } else {
    res.json({ status: "error", msg: "no items" });
  }
}
```

---

## After (Corrected)

```typescript
// [5] Magic strings replaced with a union type / enum-like constants
const OrderStatus = {
  Pending: "pending",
  Confirmed: "confirmed",
  Failed: "failed",
} as const;

type OrderStatus = (typeof OrderStatus)[keyof typeof OrderStatus];

// [1] Concrete types instead of `any`
interface OrderItem {
  id: string;
  name: string;
  price: number;
  qty: number;
  status: "available" | "backordered" | "discontinued";
}

interface OrderUser {
  id: string;
  email: string;
  tier: "gold" | "silver" | "standard";
}

interface OrderRequest {
  items: OrderItem[];
  user: OrderUser;
}

// ---- Focused helper functions (one job each) ---- [6]

const GOLD_DISCOUNT = 0.10;               // [5] Named constants for magic numbers
const SILVER_DISCOUNT = 0.05;

function calculateDiscount(                // [8] Returns new value; never mutates input
  price: number,
  tier: OrderUser["tier"],
): number {
  switch (tier) {
    case "gold":
      return price * GOLD_DISCOUNT;
    case "silver":
      return price * SILVER_DISCOUNT;
    default:
      return 0;
  }
}

function computeOrderTotal(                // [6] Extracted from god function
  items: readonly OrderItem[],             // [8] `readonly` prevents mutation
  tier: OrderUser["tier"],
): number {
  return items.reduce((sum, item) => {
    const linePrice = item.price * item.qty;
    const discount = calculateDiscount(linePrice, tier);
    return sum + (linePrice - discount);
  }, 0);
}

async function reserveInventory(items: readonly OrderItem[]): Promise<void> {
  const response = await fetch("/api/inventory/reserve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
  if (!response.ok) {                      // [4] Async errors handled explicitly
    throw new Error(`Inventory reservation failed: ${response.status}`);
  }
}

async function createOrder(
  userId: string,
  items: readonly OrderItem[],
  total: number,
): Promise<string> {
  const response = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user: userId,
      items,
      total,
      status: OrderStatus.Pending,         // [5] Constant, not a raw string
    }),
  });
  if (!response.ok) {
    throw new Error(`Order creation failed: ${response.status}`);
  }
  const data: { id: string } = await response.json();
  return data.id;
}

async function sendConfirmationEmail(
  email: string,
  orderId: string,
): Promise<void> {
  await fetch("/api/email/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to: email, subject: "Order Confirmed", orderId }),
  });
}

// ---- Main handler ---- [3] Flat structure; early returns instead of nesting

function validateOrderRequest(body: unknown): OrderRequest {
  // In production, validate with Zod/io-ts instead of type assertion:
  // const parsed = OrderRequestSchema.parse(body);
  // Using assertion here for example brevity only.
  const { items, user } = body as OrderRequest;
  if (!items || items.length === 0) {      // [2] Strict equality
    throw new Error("Cart is empty or missing items");
  }
  if (!user) {
    throw new Error("User information is required");
  }
  return { items, user };
}

export async function handleOrder(
  req: { body: unknown },                  // [1] Typed request
  res: { json: (data: unknown) => void; status: (code: number) => typeof res },
): Promise<void> {
  try {
    const { items, user } = validateOrderRequest(req.body);

    const total = computeOrderTotal(items, user.tier);

    await reserveInventory(items);         // [4] await + try/catch
    const orderId = await createOrder(user.id, items, total);
    await sendConfirmationEmail(user.email, orderId);

    res.json({ status: OrderStatus.Confirmed, orderId });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    res.status(500).json({ status: OrderStatus.Failed, message });
  }
}
```

---

## Annotations

| # | Violation (Before) | Fix (After) |
|---|---|---|
| 1 | **`any` type everywhere** -- `req: any`, `res: any`, `item: any`, `invData: any` | Introduced `OrderItem`, `OrderUser`, `OrderRequest` interfaces and typed all parameters |
| 2 | **`==` instead of `===`** -- `item.status == "available"`, `user.tier == "gold"` | Changed to strict equality (`===`) and switch statements throughout |
| 3 | **Deeply nested conditionals** -- 5+ levels of `if` nesting for validation | Flat structure with early-return validation in `validateOrderRequest` |
| 4 | **No error handling on async operations** -- fire-and-forget `fetch().then()` chains | Every `fetch` is `await`ed inside a `try/catch`; non-OK responses throw |
| 5 | **Magic strings** -- `"pending"`, `"ok"`, `"error"`, `"gold"` scattered inline | `OrderStatus` const object and union types for tier values |
| 6 | **God function** -- one 60-line function does validation, pricing, inventory, ordering, email | Split into `validateOrderRequest`, `computeOrderTotal`, `reserveInventory`, `createOrder`, `sendConfirmationEmail` |
| 7 | **`var` instead of `const`/`let`** -- all variables declared with `var` | All declarations use `const`; no reassignment needed |
| 8 | **Mutating function parameters** -- `item.price = item.price * item.qty` modifies caller's data | `computeOrderTotal` takes `readonly` arrays and computes values without mutation |
