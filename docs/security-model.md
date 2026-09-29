# Security model

SupportOps accepts user-supplied network targets, so the diagnostic boundary is treated as an SSRF-sensitive surface.

## Trust boundaries

1. **Browser → API** — all target strings, ticket fields, and diagnostic evidence are untrusted input.
2. **API → network** — diagnostic destinations must remain public at execution time.
3. **API → AI provider** — diagnostic text is redacted before any external model request.
4. **API → database** — only validated/normalized fields are persisted.

## Network target controls

- Full URLs, paths, credentials, wildcards, and malformed targets are rejected.
- Localhost, private, link-local, reserved, loopback, and other non-global IP ranges are blocked.
- Domain targets are resolved and checked before diagnostics.
- Diagnostics perform a second resolution at the execution boundary.
- The full DNS answer set is rejected if **any** answer is non-public.
- Network commands and port checks are pinned to the selected validated public IP rather than resolving the hostname again.

This last step closes the validation-to-use gap that can otherwise permit DNS rebinding.

## API controls

- Production CORS origins are allow-listed through configuration.
- Response headers include request correlation, processing time, `nosniff`, frame denial, and a strict referrer policy.
- AI insight endpoints use bounded, synchronized request-rate state.
- User-facing 5xx messages do not echo backend exception details.
- Readiness includes a database query rather than returning a static success response.

## Data handling

- API keys and provider credentials remain server-side.
- Troubleshooting evidence is redacted before external AI prompt construction.
- Published project evidence uses public/sanitized targets only.
- Real customer credentials, internal hostnames, private addressing, and tenant information must not be committed.

## Remaining production controls

For a real multi-user deployment I would add authenticated users, RBAC, an external/distributed rate limiter, database migrations, centralized logs/metrics, secret scanning, and per-tenant authorization.
