# Observability and support diagnostics

The API returns a correlation ID on each response using `X-Request-ID`. A valid caller-provided ID is preserved; invalid or missing values are replaced.

Every response also includes:

- `X-Process-Time-Ms`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`

## Health model

| Endpoint | Purpose |
|---|---|
| `/health/live` | Confirms the application process is responding |
| `/health/ready` | Confirms the application can execute a database query |
| `/health` | Compatibility alias for the liveness check |

A load balancer or uptime monitor should use readiness when routing user traffic and liveness when deciding whether the process itself should be restarted.

## Incident handoff

When an API request fails, capture:

- request ID
- UTC timestamp
- endpoint and method
- response status
- affected target/ticket ID where safe
- whether readiness is healthy
- whether the failure reproduces from another client
- recent deployment/configuration change

The frontend is designed to surface request references in failure messages so support can correlate a user report with server-side telemetry.
