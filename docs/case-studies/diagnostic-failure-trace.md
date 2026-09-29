# Case study — controlled diagnostic failure trace

This case study follows one diagnostic request through the SupportOps stack and documents what happens when the normal path breaks.

## Request path

```text
Browser
  │
  │ target + request reference
  ▼
FastAPI request middleware
  │
  ├── X-Request-ID
  ├── processing timer
  ▼
bounded diagnostic worker pool
  │
  ├── input normalization
  ├── public-target validation
  ├── second DNS check at execution boundary
  ├── public-IP pinning
  ├── ping/TCP fallback
  ├── traceroute fallback
  └── bounded port scan
  ▼
database persistence
  │
  ▼
diagnostic_id + request_id + resolved_ip
  │
  ▼
frontend ticket creation
  │
  ▼
ticket summary stores source request reference
```

## Controlled failure matrix

| Failure | Expected API behavior | Persistence behavior | Correlation |
|---|---|---|---|
| private/loopback target | 400 | nothing saved | response header |
| DNS changes to private address at execution boundary | 400 | nothing saved | response header + warning log |
| diagnostic worker pool full | 503 | nothing saved | response header + capacity log |
| diagnostic deadline exceeded | 504 | nothing saved | response header + timeout log |
| database commit fails after diagnostics | 503 | transaction rolled back | response header + persistence log |
| tool output exceeds limit | result truncated | bounded text stored | normal request ID |

## Resource limits

Defaults are configuration-driven:

- maximum concurrent diagnostic workers: 4
- overall diagnostic deadline: 30 seconds
- ping subprocess timeout: 15 seconds
- traceroute subprocess timeout: 20 seconds
- TCP fallback timeout: 3 seconds per target port
- port-scan timeout: 0.5 seconds per common port
- diagnostic text output cap: 12,000 characters
- ticket diagnostic payload cap: 12,000 characters per command output

The worker pool is bounded before work is submitted. If an HTTP request times out while the underlying worker is still exiting, that worker keeps its capacity slot until it actually completes.

## Database failure scenario

The regression test forces the SQLAlchemy commit to fail after the network result is produced.

Expected result:

1. diagnostics finish;
2. database commit raises;
3. session rolls back;
4. API returns 503 with a request reference;
5. diagnostic history remains empty.

The result is deliberately not presented as successfully saved because persistence is part of the endpoint contract.

## DNS rebinding scenario

The network-boundary test makes the same hostname resolve to a private address at the execution boundary.

Expected result:

- the second resolution fails closed;
- no socket diagnostic runs against the private address;
- no diagnostic record is written.

## Ticket correlation

A successful diagnostic response contains `request_id`. The frontend sends that reference when creating a support ticket. The saved ticket summary includes the originating diagnostic request, so an operator can move from a user-visible ticket back to the related API logs.

## Recovery

**Database outage:** restore database availability, verify `/health/ready`, then rerun the diagnostic. Failed persistence attempts are not treated as saved history.

**Temporary target failure:** preserve the request reference and retry after confirming the target is intended to be public.

**Capacity saturation:** do not increase concurrency blindly. Check worker duration and outbound dependency behavior first.

## Verification boundary

Automated tests use controlled local failures and mocks for failure injection. They verify the application behavior and safety invariants, not internet-scale load capacity.

The live deployment is separately smoke-tested with a public target to confirm the normal UI → API → pinned-address result path.
