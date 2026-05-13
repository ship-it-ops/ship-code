# Expected Review Output — fixture-3-postmortem-review

---

## Debug Review: Payments API outage postmortem, 2025-04-30

### Critical (must fix before merge)

- **[D7-DOC / P2 — Blame language] "What happened" section**: The writeup attributes the incident to Alex personally ("Alex's commit changed..."). A blameless postmortem focuses on the system that allowed the change to ship, not the engineer who made it. → Rewrite in systemic terms: "A config-consolidation change reduced the connection pool from 20 to 5 and was merged with no load-test validation. Code review did not catch the capacity implication. The pre-deploy CI did not run a representative load test." The fact that a specific commit caused it can be referenced neutrally as a hash.

- **[D7-DOC / P3 — Action items without owners or deadlines] "Action items" section**: All three action items are "we should..." with no name and no date. Without ownership, these will not happen, and the next incident will reference the same gaps. → Each action item needs: a specific change, an owner, a tracking ticket, and a target date. Example: "AI-1: Add Datadog alert for connection-pool utilization >80% sustained 60s. Owner: Sam. Ticket: INFRA-4521. Target: 2025-05-14."

### Important (should fix)

- **[D7-DOC / P1 — Timeline without causation] "Timeline" section**: The timeline is correct but does not explain why detection took 6 minutes or why nobody noticed during code review. → Add a "Why detection was late" subsection: alert threshold was 10% error rate, but capacity-induced failures ramp slowly; alerts should trigger on connection-pool utilization, not output-side error rate. Add a "Why review missed it" subsection: the PR was framed as "config consolidation" and the pool size change was buried in a 200-line diff.

- **[D6-INTERMITTENT] "What happened" section**: The post mentions the bug "still worked under normal load" — this matches the smell pattern of a latent capacity bug that surfaces only under specific traffic. → Document the load profile that triggered failure (lunchtime traffic spike: ~3x baseline) so future load tests can reproduce.

- **Regression measure missing**: A postmortem should describe how the team will detect *this exact class* of incident faster next time. → Add a section "Detection improvements": pool-utilization metric, alert at 70% sustained, runbook for connection-pool incidents.

### Suggestions (improve when convenient)

- **Add a "Root cause(s)" section**: Distinguish the proximate cause (pool size reduced to 5) from latent causes (no load-test gating, alerts not tied to capacity metrics, review process did not flag capacity-affecting changes). The 5 Whys would surface these.

- **Include customer-impact detail**: 3,200 failed payment attempts is useful, but the postmortem should also note: did any customers see double-charges, partial-completion, or other state issues that need cleanup? Or were all failures clean "try again" prompts?

### What's Good

- The timeline is precise to the minute and includes deploy correlation — that is the most useful kind of data for understanding incident dynamics, and many postmortems lack it.
- The customer impact (3,200 failures, 47 minutes) is stated quantitatively in the header. Senior leadership and trust/safety teams need this framing; it is often omitted in technical postmortems.
- The instinct to write a postmortem at all for a 47-minute SEV-1 is healthy. Many teams skip this for "minor" incidents and lose the learning.
