# Queue status — 2026-10-19

This file records what was shipped, what is blocked/failed, and what is rejected for this repository. It complements `AUDIT_FINDINGS.md`.

## Shipped
- Pricing freshness status and local pricing overrides (1.4.0).
- Real FastMCP transport for the 12 MCP tools, optional `[mcp]` extra (1.4.1).

## Blocked / failed
- Automated upstream price feed (deliberately out of scope).
- Complete current-generation model coverage.

## Rejected / deferred
- Bundling FastMCP as a mandatory dependency; the transport stays optional.

## Policy

Any future feature or upgrade must check `AUDIT_FINDINGS.md` and this file before implementation. A blocked item is retried only when its external dependency is available; a rejected item needs new user evidence or a design change to reopen.
