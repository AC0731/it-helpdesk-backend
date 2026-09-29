# Live smoke check — 2026-09-29

**Environment:** deployed SupportOps frontend + backend  
**Target used:** `example.com`  
**Scope:** read-only verification; no ticket creation, saved insight, deletion, or record modification

## Diagnostic result

The deployed diagnostic flow completed successfully.

- Request reference: `f2bd8ba4e517419c95d6a5e3422a7a29`
- Pinned public address: `104.20.23.154`
- TCP fallback:
  - 443 reachable in 2.18 ms
  - 80 reachable in 2.33 ms
  - 22 not reachable or filtered
- Common-port result:
  - 21 closed
  - 22 closed
  - 80 open
  - 443 open
  - 3389 closed

The hosting environment did not expose native `ping` or `traceroute` commands. The application displayed the expected fallback messaging and continued with DNS validation, TCP reachability, and port checks.

No raw backend exception was visible in the diagnostic result and no layout issue was observed.

## Dashboard availability observation

During the first page load in the same smoke check, these sections returned client timeout messages:

- Analytics
- Saved AI Insights
- Ticket Dashboard

An immediate read-only recheck after the backend was warm showed all three sections loading normally:

- Analytics: system online, zero tickets
- Ticket Dashboard: empty-state message, no timeout
- Saved AI Insights: empty-state message, no timeout

This suggests the first-page timeout was transient during that observation. This smoke check does not establish an uptime SLA or production-scale latency profile.

## What this verifies

This dated check confirms that the deployed application could, at that time:

1. accept the public target;
2. return a request reference;
3. pin a public IP for the diagnostic;
4. complete TCP/port checks;
5. render the diagnostic result without exposing a raw server exception.

## What this does not verify

- sustained load or concurrency capacity
- long-duration availability
- native ICMP/traceroute execution on the hosting platform
- ticket creation or AI-insight persistence in this read-only run
- that the transient first-load dashboard timeout cannot recur
