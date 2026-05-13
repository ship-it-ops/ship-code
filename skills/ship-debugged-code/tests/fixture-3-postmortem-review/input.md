# Postmortem to Review

## Incident: Payments API outage, 2025-04-30

**Severity**: SEV-1
**Duration**: 47 minutes
**Impact**: ~3,200 failed payment attempts. Customers saw "Try again later" message.

### Timeline

- 14:02 — Alex pushes commit `f2a91c` to main
- 14:05 — Deploy completes
- 14:11 — Pages start firing for high 5xx rate on `/api/payments`
- 14:18 — Alex begins investigating
- 14:32 — Sam joins on-call rotation
- 14:48 — Rollback initiated
- 14:58 — Service restored

### What happened

Alex's commit changed the connection pool size from 20 to 5 as part of a config consolidation. Under normal load this still worked, but during the lunchtime traffic spike, requests started queueing and timing out. The error rate climbed steadily, but the alert threshold was set to 10% and traffic above that took about 6 minutes to manifest. By the time pages fired, customers were already affected.

### Action items

- We should add better alerting on connection pool exhaustion.
- We should improve our config change process.
- We should have caught this in code review.
