# Pull Request to Review

**Title**: Fix crash in dashboard

**Body**:
> The dashboard was crashing for some users with a TypeError. Added a check to handle the case. LGTM.

**Diff**:
```diff
 export function renderDashboard(user, widgets) {
+  if (!widgets) return <EmptyState />;
   return (
     <div>
       <Header user={user} />
       {widgets.map((w) => <Widget key={w.id} {...w} />)}
     </div>
   );
 }
```

**Commit message**:
```
fix dashboard
```

**No tests added.** No reference to a Sentry issue, support ticket, or reproduction case.
