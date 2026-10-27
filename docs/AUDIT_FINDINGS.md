# Audit Findings: PyTokenCalc

**Audit Date:** 2026-10-26  
**Version:** 1.5.0  
**Branch:** `main`  
**Full report:** [`.audit/reports/PyTokenCalc/audit.md`](../.audit/reports/PyTokenCalc/audit.md)

## Scope

Read-only review of the public API, provider registry, tokenizer adapters, pricing/catalog, cache, REST/MCP surfaces, tests, CI, and packaging. No provider APIs were called and no source was modified.

## Findings

| ID | Severity | Finding | Evidence | Recommendation |
|---|---|---|---|---|
| PTC-01 | Medium | Ollama token counting calls the generation API without a generation limit. | `pytokencalc/tokenizers/ollama_counter.py`: `/api/generate`, `stream: false`, no `num_predict`. | Use a tokenization-only endpoint where possible; otherwise cap generation and document the cost. |
| PTC-02 | Medium | Custom-provider fallback silently estimates from response text but reports `source="api"`. | `pytokencalc/tokenizers/custom_provider_counter.py`: `len(text) // 4 + 1`, `source="api"`. | Add an explicit estimated/fallback source, log it, and allow callers to reject estimates. |
| PTC-03 | Medium | Cache state is unsynchronized and mixes naive local time with UTC. | `pytokencalc/tokenizers/cache.py`: plain dict, `datetime.now()` vs `datetime.utcnow()`. | Add a lock or thread-safe cache; use monotonic TTL plus UTC timestamps. |
| PTC-04 | Medium | REST and HTTP MCP surfaces have no built-in auth, rate limit, or body-size cap. | `pytokencalc/server.py`, `pytokencalc/mcp_server.py`; localhost default is documented. | Require explicit remote-bind opt-in and add auth, limits, and startup warnings. |
| PTC-05 | Low/Medium | Provider endpoints are caller-controlled with no egress policy. | Custom provider `base_url`; Ollama `base_url`. | Allowlist schemes/hosts, optionally deny private networks, and document prompt egress. |
| PTC-06 | Low | Pricing table can drift from provider prices. | `PRICING_TABLE`, `PRICING_LAST_UPDATED = "2026-09"`, `pricing_status()`. | Keep freshness checks; document override workflow and update cadence. |
| PTC-07 | Low | Cache key omits encoder/model revision. | `_get_key(provider, model, text)` in `cache.py`. | Include tokenizer/encoding version in the key. |
| PTC-08 | Low | Cache eviction is approximate, not true LRU. | `_store` sorts all keys and removes oldest 10%. | Use an actual bounded LRU or document the behavior accurately. |
| PTC-09 | Low | `SECURITY.md` says no dependency scanning, but CI runs pip-audit. | `SECURITY.md` vs `.github/workflows/ci.yml`. | Reconcile documentation with CI. |
| PTC-10 | Low/Medium | Optional provider integrations are only mock-tested. | CI has no live provider conformance job. | Add opt-in/nightly live tests and adapter contract tests. |

## Positive Controls

- Zero default runtime dependencies; deterministic local path is real.
- Registry isolates provider-construction failures.
- Localhost is the REST default with an explicit unauthenticated-exposure warning.
- Prompt text is hashed for cache keys rather than stored as a key.
- Pricing freshness metadata and overrides exist.
- Large test suite: 26 modules, 358 static test functions, including property and failure-path tests.
- CI covers Python 3.9–3.13, ruff, and pip-audit.

## Audit Limitations

- Provider APIs and live tokenizer accuracy were not exercised.
- REST/MCP servers were reviewed statically; no fuzzing or load testing.
- Test counts are definitions, not a verified pass count.
- Dependency advisories were not independently re-scanned.
