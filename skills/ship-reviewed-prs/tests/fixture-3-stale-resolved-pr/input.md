# Synthetic PR Input for Fixture 3: Lifecycle Suppression

You are reviewing a long-lived PR with substantial review history. Treat the input below as the result of the `gh` fetch phase.

## PR metadata

```json
{
  "owner": "acme",
  "repo": "billing",
  "number": 4980,
  "title": "Refactor payment processing for retries",
  "body": "Refactors processPayment to support idempotent retries with exponential backoff. Out-of-scope: changing the retry policy itself — that's tracked in #5001.",
  "headRefName": "feat/payment-retries",
  "baseRefName": "main",
  "author": "erin",
  "isDraft": false,
  "labels": [],
  "files": [
    {"path": "services/payments.ts", "additions": 45, "deletions": 22}
  ],
  "statusCheckRollup": {"state": "SUCCESS"},
  "commits": [
    {"sha": "111aaa", "committedDate": "2026-04-25T10:00:00Z"},
    {"sha": "222bbb", "committedDate": "2026-04-28T14:00:00Z"},
    {"sha": "333ccc", "committedDate": "2026-05-05T09:00:00Z"},
    {"sha": "444ddd", "committedDate": "2026-05-10T16:00:00Z"}
  ]
}
```

## Diff (gh pr diff)

```diff
diff --git a/services/payments.ts b/services/payments.ts
@@ -10,22 +10,45 @@ import { stripeClient } from "./stripe";
+import { withRetry } from "../lib/retry";

-export async function processPayment(order) {
-  const result = await stripeClient.charge(order.amount, order.token);
-  return result;
+export async function processPayment(order: Order, idempotencyKey: string): Promise<ChargeResult> {
+  return withRetry(
+    () => stripeClient.charge(order.amount, order.token, { idempotencyKey }),
+    { maxAttempts: 3, backoff: "exponential" }
+  );
 }
```

(45 net added lines total; this is an excerpt.)

## Review threads (gh api graphql) — 6 threads

```json
{
  "reviewThreads": [
    {
      "id": "T1",
      "isResolved": true,
      "isOutdated": false,
      "path": "services/payments.ts",
      "line": 12,
      "originalLine": 12,
      "comments": [
        {"body": "Should this be parameterized to take a custom retry policy?", "author": {"login": "alice"}, "authorAssociation": "MEMBER", "createdAt": "2026-04-26T10:00:00Z"}
      ]
    },
    {
      "id": "T2",
      "isResolved": true,
      "isOutdated": false,
      "path": "services/payments.ts",
      "line": 14,
      "originalLine": 14,
      "comments": [
        {"body": "Idempotency key should be a UUID, not user-supplied.", "author": {"login": "bob"}, "authorAssociation": "OWNER", "createdAt": "2026-04-27T11:00:00Z"}
      ]
    },
    {
      "id": "T3",
      "isResolved": true,
      "isOutdated": false,
      "path": "services/payments.ts",
      "line": 18,
      "originalLine": 18,
      "comments": [
        {"body": "Missing structured log on retry attempts.", "author": {"login": "carol"}, "authorAssociation": "COLLABORATOR", "createdAt": "2026-04-29T15:00:00Z"}
      ]
    },
    {
      "id": "T4",
      "isResolved": false,
      "isOutdated": false,
      "path": "services/payments.ts",
      "line": 22,
      "originalLine": 22,
      "comments": [
        {"body": "What about supporting different retry policies per merchant?", "author": {"login": "dave"}, "authorAssociation": "COLLABORATOR", "createdAt": "2026-05-02T09:00:00Z"},
        {"body": "Out of scope for this PR, tracked in #5001.", "author": {"login": "erin"}, "authorAssociation": "MEMBER", "createdAt": "2026-05-02T12:00:00Z"}
      ]
    },
    {
      "id": "T5",
      "isResolved": false,
      "isOutdated": false,
      "path": "services/payments.ts",
      "line": 30,
      "originalLine": 30,
      "comments": [
        {"body": "Could you also add a circuit breaker?", "author": {"login": "frank"}, "authorAssociation": "MEMBER", "createdAt": "2026-05-08T10:00:00Z"},
        {"body": "Discussed offline with frank — agreed to skip for now.", "author": {"login": "erin"}, "authorAssociation": "MEMBER", "createdAt": "2026-05-08T13:00:00Z"}
      ]
    },
    {
      "id": "T6",
      "isResolved": false,
      "isOutdated": false,
      "path": "services/payments.ts",
      "line": 38,
      "originalLine": 38,
      "comments": [
        {"body": "Add a test for the retry exhaustion path.", "author": {"login": "grace"}, "authorAssociation": "MEMBER", "createdAt": "2026-05-11T14:00:00Z"}
      ]
    }
  ]
}
```

## CI checks

All green.

---

Run the multi-persona PR review. Pay special attention to lifecycle classification and suppression — the skill should NOT re-raise concerns that map to T1, T2, T3 (resolved), T4 (won't-fix via tracking ref), T5 (won't-fix via "agreed to skip"). T6 is an OPEN thread that should be acknowledged.
