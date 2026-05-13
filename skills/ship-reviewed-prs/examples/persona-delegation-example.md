# Persona Delegation Example

Worked example showing how the SE persona defers a finding to `/ship-clean-code` instead of duplicating that skill's rubric.

---

## The PR

A small refactor of an order-processing function:

```diff
diff --git a/services/orders.ts b/services/orders.ts
@@ -10,42 +10,68 @@
 export async function processOrder(o) {
+  const t = o.total;
+  const c = o.customer;
+
   // validate
-  if (!o.items.length) throw new Error("empty");
+  if (!o.items.length) {
+    throw new Error("empty");
+  }
+
+  // tax stuff
+  const taxRate = 0.08;
+  const tax = t * taxRate;
+  const grandTotal = t + tax;
+
+  // discount stuff
+  if (c.tier == "premium") {
+    const discount = grandTotal * 0.1;
+    const finalTotal = grandTotal - discount;
+    console.log("Premium discount applied:", discount);
+    return { ...o, total: finalTotal };
+  } else if (c.tier == "pro") {
+    const discount = grandTotal * 0.05;
+    const finalTotal = grandTotal - discount;
+    console.log("Pro discount applied:", discount);
+    return { ...o, total: finalTotal };
+  } else {
+    return { ...o, total: grandTotal };
+  }
-  return { ...o, total: o.total * 1.08 };
 }
```

**Diff observations** that any sufficiently nitpicky reviewer would note:
- Variables `t`, `c` are single-letter (naming)
- Function does multiple things: validate, tax, discount (SRP)
- `==` instead of `===` (style)
- Magic numbers `0.08`, `0.1`, `0.05` (magic numbers)
- `console.log` instead of structured logger (logging)
- Repeated discount-computation pattern in if/else (DRY violation)
- Comments "tax stuff" and "discount stuff" are noise

---

## What a naive multi-persona reviewer would emit

Every one of those bullet points as a separate finding from the SE persona. The output explodes:

```
- [SE6] Line 11: variable `t` is single-letter, rename to `total`
- [SE6] Line 12: variable `c` is single-letter, rename to `customer`
- [SE6] Line 21: use === instead of ==
- [SE6] Line 17: magic number 0.08 should be a named constant TAX_RATE
- [SE6] Line 22: magic number 0.1 should be PREMIUM_DISCOUNT_RATE
- [SE6] Line 28: magic number 0.05 should be PRO_DISCOUNT_RATE
- [SE5] Function does multiple things: validate, tax, discount — split into separate functions
- [SE4] console.log should be logger.info
- [SE5] Premium/Pro branches duplicate discount logic, extract to applyDiscount(tier, total)
- [SE6] Comments "tax stuff" / "discount stuff" add no information, remove
```

10 findings on a 40-line refactor. The reviewer's eyes glaze over. The actual important concerns — if any — get drowned in style noise.

---

## What this skill produces instead

```
### Important (should fix)

- (no SE findings on services/orders.ts in this severity tier)

### Delegations

- Run `/ship-clean-code` on `services/orders.ts` — the refactor introduces multiple file-level concerns (naming, SRP, magic numbers, logging, DRY, comment quality) that `ship-clean-code` has the right rubric for. After the cleanup, return here for a final PR-level review.
```

That's the entire SE output for this file.

---

## The reasoning (from the delegation table in SKILL.md)

| If the finding is fundamentally about... | Replace with |
|---|---|
| Naming (single-letter `t`, `c`) | Delegation to `ship-clean-code` (catches P6) |
| Function doing multiple things (SRP) | Delegation to `ship-clean-code` (catches P5) |
| `==` vs `===` | Delegation to `ship-clean-code` (catches P7) |
| Magic numbers (0.08, 0.1, 0.05) | Delegation to `ship-clean-code` (catches P6) |
| `console.log` instead of logger | Delegation to `ship-clean-code` (catches in lang-typescript.md observability section) |
| Duplicated branches (DRY) | Delegation to `ship-clean-code` (catches G5) |
| Mumble comments ("tax stuff") | Delegation to `ship-clean-code` (catches C4) |

Every single one is **fundamentally about** file-level code quality, with no PR-shaped dimension. SE only fires when a finding has a PR-specific angle that `ship-clean-code` can't see — e.g., this refactor introduces a public-API breaking change, or removes a deprecated symbol without a deprecation window, or changes a contract.

---

## When SE *would* fire on this file

Adjust the diff slightly:

```diff
-export async function processOrder(o) {
+export async function processOrder(o: Order, options: { skipTax: boolean }) {
```

Now SE fires:

```
- [SE2-CONTRACT-DRIFT] services/orders.ts:10: `processOrder` adds a required `options` parameter, breaking all existing callers. → Make `options` optional with a default `{ skipTax: false }`, or add an overload, or rename to `processOrderV2` and keep the old signature deprecated for one release.
```

That's an SE finding. PR-shaped. Not a code-quality concern.

The delegation table is what makes the four skills compose instead of compete. Each one has a clear job. PR review is for PR-shaped concerns; code-quality review is for file-shaped concerns.

---

## A second example: TS persona delegation

Same PR's lifecycle:

```diff
diff --git a/services/orders.ts (+58 lines)
# no test file changes
```

The TS persona observes:
- 58 net added lines in `code` bucket
- 0 changes in `test` bucket
- ratio = bad (TS1 threshold of 30 exceeded)

TS emits:

```
### Delegations

- Run `/ship-tested-code` on this PR — 58 lines of production code added in services/orders.ts with no test files modified. TS1 triggered. `ship-tested-code` will design tests at the right level (probably unit tests for the discount/tax math, integration for the full processOrder flow) and identify any testability issues in the refactor.
```

Note how the delegation explains *why* and *what* the delegated skill will do — the reviewer doesn't need to wonder if the delegation is meaningful.

---

## Outcome

The four skills work together:

1. **ship-reviewed-prs** does its PR-shaped review (decision matrix, lifecycle, contract concerns).
2. **ship-clean-code** is invoked manually by the author on the noisy file.
3. **ship-tested-code** is invoked manually to design and review the tests.
4. **ship-debugged-code** would be invoked if the PR is a bugfix.

The author sees a clear path forward instead of one giant wall of findings.
