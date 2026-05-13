# Expected Investigation Output — fixture-1-bug-report

The skill, in investigation mode, should resist the user's request to add an auto-retry. A retry-as-fix (F5/D6) papers over a real bug. The skill should drive the user through reproduction and root-cause analysis first.

The response should substantially match the structure below.

---

Before adding a retry, let's make sure we understand what's actually wrong. An auto-retry that papers over a bug usually means the same bug appears later in a worse form (data inconsistency, double-charges, lost work).

Three questions I'd want answered before any code change:

**1. Can we reproduce it on demand?** Right now we have "sometimes empty." Sometimes means there's a determinant — a specific user, a specific dataset size, a specific timing window. Without finding it, any fix is a guess.

Some likely candidates to check, in order of probability:
- **Timing**: is `export_csv` async and the download is fired before the rows are flushed?
- **Data dependency**: is the empty file always for a specific user, role, or filter combination? (Check the access log for the failing requests.)
- **Session/auth**: does the empty file correlate with an expired session, redirect to login that returns an empty 200?
- **Browser**: is it always Safari, or always behind a specific proxy?

**2. What does "empty" actually mean?**
- 0 bytes? → likely a streaming/flush issue or auth redirect.
- Just headers, no rows? → likely a query returning zero rows for that user.
- Some rows, then truncated? → likely a timeout mid-stream.

Each of these has a different root cause and different fix.

**3. What does the server log say for a failing request?** Find a recent failing case (the user reporting it would be ideal — get the timestamp), and look at the request:
- Was the response a 200 with `Content-Length: 0`?
- Was there a 302 redirect to login?
- Did the query complete in a normal time?
- Were there any errors during streaming?

## Suggested next steps

1. Ask the reporting user for a precise timestamp and (if possible) their user ID. Pull the corresponding server log entries.
2. Reproduce: with the same user account and the same query state, hit the export endpoint repeatedly. If you can reproduce, capture the failing request as a curl reproduction.
3. State your hypothesis explicitly (e.g., "the empty file appears when the query takes longer than 30s because the proxy times out").
4. Test that hypothesis with one targeted experiment.
5. Once you know the cause, fix it at the right layer — not at the retry boundary.

If the bug is genuinely intermittent and you cannot identify the cause within a reasonable investigation window, we can talk about a guarded retry as a stopgap — but it would need to be paired with an alert and an investigation ticket, not a silent retry.

Where would you like to start? If you can share the reporter's timestamp and user ID, I can help you trace the exact failing request.
