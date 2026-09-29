# INC-003 — DNS rebinding / validation-to-use hardening

**Status:** Resolved  
**Category:** SSRF boundary / network diagnostics

## Finding

The API validated that a hostname resolved only to public addresses before diagnostics, but the network tools later used the hostname again. A DNS answer can change between validation and use, leaving a validation-to-use gap.

## Risk

A hostile or rapidly changing DNS record could pass the initial public-address check and later resolve to a private/reserved address when the diagnostic command or socket operation executed.

For a network diagnostic service, that boundary is security-sensitive because the server performs outbound connections on behalf of the requester.

## Reproduction

A regression test was committed first to model a domain resolving to a private address at the execution boundary. CI failed because the execution layer had no public-address pinning helper.

The test also covers mixed DNS answer sets containing both public and private addresses.

## Fix

- Added `resolve_public_target_ip()` at the network execution boundary.
- Reject the entire answer set if any address is non-public.
- Select a deterministic public address.
- Pin ping, traceroute, TCP fallback, and port checks to the validated IP.
- Keep the original domain only as the support/display target.
- Added `resolved_ip` to the diagnostic response for troubleshooting transparency.

## Verification

The failing regression commit is preserved in Git history, followed by the hardening commits and passing CI.

## Lesson

Input validation is not enough when a resource can change between validation and use. Network tooling should validate as close as possible to the outbound operation and avoid re-resolving an already approved hostname.
