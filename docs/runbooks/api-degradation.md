# Runbook — API degradation or failed diagnostics

## 1. Establish scope

Determine whether the issue affects one request, one diagnostic target, or all users.

Check:

```http
GET /health/live
GET /health/ready
```

## 2. Capture request context

Record the response status and `X-Request-ID`. Avoid copying secrets or full unredacted payloads into public tickets.

## 3. Separate failure domains

- **Liveness fails:** application/process/platform issue.
- **Liveness passes, readiness fails:** database connectivity or database availability.
- **Health passes, one target fails validation:** target safety/DNS issue.
- **Health passes, many diagnostics time out:** outbound network/platform degradation.
- **Only insight calls fail:** provider/rate-limit path; diagnostic and ticket workflows can remain available.

## 4. Validate target safety

If a hostname is rejected because it resolves to a non-public address, do not bypass the guardrail. Validate DNS externally and confirm the target is intended to be public.

## 5. Escalation evidence

Include request ID, timestamps, health status, affected endpoint, safe target details, deployment revision, and actions already attempted.
