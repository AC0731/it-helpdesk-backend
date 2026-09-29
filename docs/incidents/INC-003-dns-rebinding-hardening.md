# INC-003 — DNS rebinding / validation-to-use hardening

**Status:** Resolved  
**Category:** SSRF boundary / network diagnostics

## Finding

The API validated that a hostname resolved only to public addresses before diagnostics, but the network tools later used the hostname again. A DNS answer can change between validation and use, leaving a validation-to-use gap.

## Risk

A hostile or rapidly changing DNS record could pass the initial public-address check and later resolve to a private/reserved address when the diagnostic command or socket operation executed.

For a network diagnostic service, that boundary is security-sensitive because the server performs outbound connections on behalf of the requester.

## How I found it

While tracing the validation and connection flow, I found that the hostname was resolved before validation and then could be resolved again when the diagnostic actually connected. That meant the address used by the network tool was not guaranteed to be the same address that passed validation. I added regression coverage for that boundary before changing the execution path.

The regression coverage also checks mixed DNS answer sets containing both public and private addresses.

## Fix

- Added `resolve_public_target_ip()` at the network execution boundary.
- Reject the entire answer set if any address is non-public.
- Select a deterministic public address.
- Pin ping, traceroute, TCP fallback, and port checks to the validated IP.
- Keep the original domain only as the support/display target.
- Added `resolved_ip` to the diagnostic response for troubleshooting transparency.

## Verification

The commit history shows the regression coverage, the hardening change, and the later passing CI run.

## Lesson

Input validation is not enough when a resource can change between validation and use. Network tooling should validate as close as possible to the outbound operation and avoid re-resolving an already approved hostname.
