# Synthetic PR Input for Fixture 6: Clean Frontend PR (False-Positive Guard)

You are reviewing the following PR. Treat the input below as the result of the `gh` fetch phase. Do not actually run `gh` commands.

This fixture's purpose is to guard against false positives in the FE persona. The PR adds a small, well-shaped presentational React component. The FE persona should activate (TSX file touched) but produce no findings. Decision: APPROVE.

## PR metadata

```json
{
  "owner": "acme",
  "repo": "design-system",
  "number": 2201,
  "title": "Add Badge component",
  "body": "## Summary\n\nAdds a small presentational `Badge` component with `tone` and `size` variants. Used by the inbox UI to label message status (unread, archived, pinned).\n\n## Test plan\n\n- Unit test renders all variants.\n- Axe a11y check in default + each tone.",
  "headRefName": "feat/badge",
  "baseRefName": "main",
  "author": "kira",
  "isDraft": false,
  "labels": [],
  "files": [
    {"path": "packages/ui/src/components/Badge/Badge.tsx", "additions": 45, "deletions": 0},
    {"path": "packages/ui/src/components/Badge/Badge.test.tsx", "additions": 60, "deletions": 0},
    {"path": "packages/ui/src/components/Badge/index.ts", "additions": 4, "deletions": 0},
    {"path": "packages/ui/src/index.ts", "additions": 2, "deletions": 0}
  ],
  "statusCheckRollup": {"state": "SUCCESS"},
  "commits": [{"sha": "ba94e21", "committedDate": "2026-05-19T14:00:00Z"}]
}
```

## Diff (gh pr diff)

```diff
diff --git a/packages/ui/src/components/Badge/Badge.tsx b/packages/ui/src/components/Badge/Badge.tsx
new file mode 100644
@@ -0,0 +1,45 @@
+import { cva, type VariantProps } from 'class-variance-authority';
+import { cn } from '@ship-it-ui/cn';
+import type { ComponentPropsWithoutRef } from 'react';
+
+export const badgeStyles = cva(
+  'inline-flex items-center rounded-full px-2 text-xs font-medium',
+  {
+    variants: {
+      tone: {
+        neutral: 'bg-neutral-100 text-neutral-700',
+        success: 'bg-success-100 text-success-700',
+        warning: 'bg-warning-100 text-warning-700',
+        danger: 'bg-danger-100 text-danger-700',
+      },
+      size: {
+        sm: 'h-5 py-0',
+        md: 'h-6 py-0.5',
+      },
+    },
+    defaultVariants: {
+      tone: 'neutral',
+      size: 'md',
+    },
+  },
+);
+
+export type BadgeTone = NonNullable<VariantProps<typeof badgeStyles>['tone']>;
+export type BadgeSize = NonNullable<VariantProps<typeof badgeStyles>['size']>;
+
+export interface BadgeProps extends ComponentPropsWithoutRef<'span'>, VariantProps<typeof badgeStyles> {}
+
+export function Badge({ tone, size, className, children, ...rest }: BadgeProps) {
+  return (
+    <span className={cn(badgeStyles({ tone, size }), className)} {...rest}>
+      {children}
+    </span>
+  );
+}

diff --git a/packages/ui/src/components/Badge/Badge.test.tsx b/packages/ui/src/components/Badge/Badge.test.tsx
new file mode 100644
@@ -0,0 +1,60 @@
+import { describe, it, expect } from 'vitest';
+import { render, screen } from '@testing-library/react';
+import { axe } from 'vitest-axe';
+import { Badge } from './Badge';
+
+describe('Badge', () => {
+  it('renders children', () => {
+    render(<Badge>Unread</Badge>);
+    expect(screen.getByText('Unread')).toBeInTheDocument();
+  });
+
+  it('applies tone classes', () => {
+    render(<Badge tone="success">OK</Badge>);
+    expect(screen.getByText('OK')).toHaveClass('bg-success-100');
+  });
+
+  it('has no a11y violations in each tone', async () => {
+    for (const tone of ['neutral', 'success', 'warning', 'danger'] as const) {
+      const { container } = render(<Badge tone={tone}>label</Badge>);
+      expect(await axe(container)).toHaveNoViolations();
+    }
+  });
+});

diff --git a/packages/ui/src/components/Badge/index.ts b/packages/ui/src/components/Badge/index.ts
new file mode 100644
@@ -0,0 +1,4 @@
+export { Badge, badgeStyles } from './Badge';
+export type { BadgeProps, BadgeTone, BadgeSize } from './Badge';

diff --git a/packages/ui/src/index.ts b/packages/ui/src/index.ts
@@ -10,3 +10,5 @@ export * from './components/InlineEdit';
 export * from './components/Card';
+export * from './components/Badge';
```

## Review threads (gh api graphql)

```json
{
  "reviewThreads": []
}
```

## CI checks (gh pr checks)

All green.

## Invocation flags

The user invoked the skill with `--auto-approve`.

---

Run the multi-persona PR review. FE activates (TSX file touched, packages/*/src/ in a UI library workspace) but should not produce any findings. The expected decision is APPROVE. Because `--auto-approve` is set on a green-path APPROVE, the skill should submit without prompting.
