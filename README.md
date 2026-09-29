# SupportOps Diagnostic API — Backend

FastAPI backend for a support operations platform that combines network diagnostics, ticket workflows, troubleshooting insight generation, persistence, operational telemetry, and security controls.

The design treats outbound diagnostics as a security-sensitive boundary rather than a simple utility endpoint.

## Live system

- Frontend: https://it-support-diagnostic-portal.vercel.app
- API: https://it-support-api-g0b4.onrender.com
- API docs: https://it-support-api-g0b4.onrender.com/docs
- Frontend repository: https://github.com/AC0731/it-helpdesk-frontend

## Architecture

```text
React/Vite client
      │
      ▼
FastAPI
 ├── request correlation / timing
 ├── target validation
 ├── DNS execution-boundary validation
 ├── pinned public-IP diagnostics
 ├── ticket + diagnostic persistence
 ├── AI redaction / rate limiting
 ├── liveness + database readiness
 └── security headers
      │
      ├── SQLAlchemy / SQLite
      └── optional external AI provider
```

## Security model

The most important boundary is **user input → outbound network connection**.

Controls include:

- reject URLs, credentials, paths, wildcards, malformed targets
- block localhost/private/link-local/reserved/non-global addresses
- validate domain resolution before execution
- resolve again at the execution boundary
- reject mixed public/private DNS answer sets
- pin network diagnostics to the approved public IP
- keep the original hostname only for display/support records
- redact sensitive text before external AI calls
- generic 5xx responses to the browser
- bounded AI rate-limit state
- production dependency vulnerability auditing

See [`docs/security-model.md`](docs/security-model.md).

## Security incident: DNS rebinding / TOCTOU

A security review found that target validation and target use were separated.

The original flow:

```text
validate hostname → later pass hostname into network tool → hostname resolves again
```

That leaves a DNS-rebinding window.

A regression test was committed first and failed. The repair then:

1. added `resolve_public_target_ip()`
2. revalidated the full DNS answer set at execution time
3. rejected the target if any returned address was non-public
4. selected a deterministic public address
5. pinned ping/traceroute/TCP/port checks to that IP
6. exposed `resolved_ip` in the API response

The failure and fix remain visible in Git history.

Incident write-up: [`docs/incidents/INC-003-dns-rebinding-hardening.md`](docs/incidents/INC-003-dns-rebinding-hardening.md)

## Controlled failure trace

The diagnostic path now has a bounded execution model and explicit behavior for the failure cases that matter operationally:

- DNS validation and network execution run outside the async event loop
- concurrent diagnostic jobs are capped
- an overall deadline returns HTTP 504
- saturated capacity returns HTTP 503 without queuing unbounded work
- command output is truncated before storage
- database commit failure rolls back instead of creating partial history
- the same request reference is shown in the UI and copied into the resulting ticket summary

The controlled regression matrix covers blocked/private targets, DNS rebinding, timeout, capacity saturation, persistence failure and output limits.

Case study: [`docs/case-studies/diagnostic-failure-trace.md`](docs/case-studies/diagnostic-failure-trace.md)

**Limit:** this verifies application behavior under injected failures; it is not presented as production-scale load testing.

## Operational controls

### Request correlation

Every response carries:

```text
X-Request-ID
X-Process-Time-Ms
```

A safe caller-provided request ID is preserved; otherwise the API generates one.

### Security headers

Responses include:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
```

### Health model

```http
GET /health/live
GET /health/ready
```

`/health/live` verifies the process is responding.

`/health/ready` executes `SELECT 1` against the database so traffic can be withheld when persistence is unavailable.

See [`docs/observability.md`](docs/observability.md).

## Diagnostics

```http
POST /api/diagnostics
```

Example response:

```json
{
  "diagnostic_id": 42,
  "target": "example.com",
  "resolved_ip": "93.184.216.34",
  "results": {
    "ping": "...",
    "traceroute": "...",
    "ports": {
      "21": "Closed",
      "22": "Closed",
      "80": "Open",
      "443": "Open",
      "3389": "Closed"
    }
  }
}
```

If platform-level `ping` or `traceroute` tools are unavailable, the API degrades cleanly instead of leaking raw process failures.

## Ticket operations

The API supports:

- ticket creation
- priority
- status transitions
- searchable/filterable queue
- analytics
- case detail retrieval
- persisted diagnostic history

## Troubleshooting insights

Insight handling includes:

- redaction before external provider use
- local-rules fallback when no provider key is configured
- saved history
- duplicate protection
- bounded rate limiting
- server-side provider credentials only

## Rate-limit hardening

The in-memory AI rate limiter is synchronized with a lock and bounds the number of stored client keys.

It:

- removes stale clients
- evicts the oldest client when the cap is reached
- prevents unlimited key growth
- has regression coverage for pruning and bounding behavior

For horizontally scaled production, this would be replaced by Redis or another shared rate-limit backend.

## Testing

```bash
pytest
python -m compileall app
```

Coverage includes:

- target validation
- DNS rebinding boundary
- mixed DNS-answer rejection
- deterministic public IP selection
- diagnostics
- tickets/analytics
- insight fallback/redaction
- rate limiting
- request ID behavior
- security headers
- database readiness

## CI and dependency security

Backend CI runs:

```text
pip install -r requirements.txt
python -m compileall app
pip-audit -r requirements.txt
pytest
```

The audit pass found vulnerable pinned versions of AnyIO, IDNA, and Starlette. Those packages were upgraded, then CI was rerun successfully.

Final verified backend CI:  
https://github.com/AC0731/it-helpdesk-backend/actions/runs/36566543153

## Incident/runbook documentation

- [Security model](docs/security-model.md)
- [Observability](docs/observability.md)
- [DNS rebinding hardening incident](docs/incidents/INC-003-dns-rebinding-hardening.md)
- [API degradation runbook](docs/runbooks/api-degradation.md)

## Tech stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Uvicorn
- httpx
- Pytest
- GitHub Actions
- Render

## Environment

```env
ALLOWED_ORIGINS=http://localhost:5173,https://it-support-diagnostic-portal.vercel.app
DATABASE_URL=sqlite:///./supportops.db
OPENAI_API_KEY=
AI_MODEL=
```

## Engineering decisions

**Validate at the point of use.** DNS validation is repeated at the outbound execution boundary.

**Fail closed on ambiguous DNS.** Mixed public/private answers are rejected rather than selecting the convenient address.

**Evidence should be correlatable.** Request IDs and processing time make user reports easier to connect with backend behavior.

**Readiness is not liveness.** A process can be alive while its database is unavailable.

**Dependency security is part of delivery.** Runtime dependency auditing is a CI gate, not a one-time manual check.

## Author

Akanksha Chavda  
GitHub: AC0731
