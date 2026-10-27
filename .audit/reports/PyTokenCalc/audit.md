# Audit Report: PyTokenCalc

**Audit Date:** 2026-10-26  
**Repository Path:** `/Users/georgimullassery/Desktop/Projects/PyTokenCalc`  
**Audit Type:** Read-only systems design audit  
**Version:** 1.5.0 (`pytokencalc/_version.py`)  
**Branch:** `main`  
**Source Size:** ~14,483 Python LOC in package + tests; 358 test functions; 26 test modules

## Executive Summary

PyTokenCalc is a pure-Python multi-provider token-counting and cost-estimation library with CLI, REST, and MCP surfaces. Its strongest part is the provider abstraction: a broad set of deterministic local encoders, provider-API counters, model/catalog metadata, pricing and usage reconciliation, preflight checks, and explicit fallback behavior. The project has no default runtime dependencies, which keeps installation simple and makes the deterministic path genuinely local.

The main risks are accuracy honesty and operational behavior, not a fake core. The Ollama counter obtains prompt token counts by calling the generation endpoint without a token limit, so counting can trigger a full generation. The custom-provider counter can silently estimate from response text while still reporting an API source. The cache is a process-local dict with no locking and mixed naive/UTC timestamps. Release documentation and CI claims are partly stale, and the networked REST/MCP surfaces have no authentication, though localhost binding is the default and the exposure risk is documented.

## Purpose and Positioning

- **What it is:** a universal token-counting and LLM-cost utility for cloud, local, custom, and bring-your-own-model providers.
- **Who it is for:** application developers, agent frameworks, workflow tools, and FinOps/usage teams that need pre-request context and cost estimates.
- **What it is not:** an inference runtime, a billing system of record, a guaranteed-accurate tokenizer for every closed model, or a hardened multi-tenant service.
- **Differentiator:** one API across deterministic local encoders, provider counters, pricing, model catalog, reconciliation, and preflight, with zero default dependencies.

## Architecture

```text
Public API / CLI / REST / MCP
  api.py, cli.py, quick_cli.py, server.py, mcp_server.py, _mcp_tools.py
        |
        v
TokenCounterRegistry (tokenizers/registry.py)
  OpenAI, Anthropic, Google, Cohere, Azure OpenAI
  HuggingFace, tiktoken, local inference, Ollama, custom providers
        |
        v
Provider tokenizer adapters + global TokenCounterCache
  deterministic encoders where possible; provider HTTP APIs otherwise
        |
        v
Pricing / catalog / usage / reconciliation / preflight
  pricing.py, catalog.py, endpoints.py, ledger.py, reconcile.py, preflight.py
```

### Main paths

- **Deterministic path:** local tokenizer or encoding for supported models; no API key or network call.
- **Provider path:** provider-specific HTTP API for models whose tokenizer is not public.
- **Fallback path:** character-based estimate when a provider cannot return a count.
- **Cost path:** pricing table plus optional overrides, usage classes, cache-read/write pricing, endpoint comparison.
- **Automation path:** CLI, Flask REST server, FastMCP stdio/HTTP server, StatGuardian adapter.

## Repository Layout

```text
pytokencalc/                 package
  api.py                     top-level count_tokens / estimate_cost
  tokenizers/                provider adapters, registry, cache, streaming
  pricing.py                 pricing table, overrides, usage costs
  catalog.py                 model metadata and aliases
  preflight.py               context/cost preflight
  reconcile.py               provider usage reconciliation
  server.py                  optional Flask REST surface
  mcp_server.py              optional FastMCP surface
  cli.py, quick_cli.py       command-line entry points
tests/                       26 test modules, 358 test functions
docs/                        usage and design documentation
quality_contracts/           contract data
token_validations/           validation fixtures/data
scripts/, tools/             maintenance and benchmark helpers
```

## Technology Stack and Dependencies

- **Language:** Python 3.9+.
- **Default runtime dependencies:** none.
- **Extras:** `mcp` (`fastmcp`), `server` (`flask`), `tokenizers` (`tiktoken`, `transformers`).
- **Optional integrations:** provider SDKs are generally avoided in favor of HTTP; StatGuardian is optional.
- **Testing:** pytest, pytest-asyncio, hypothesis, requests/flask/fastmcp for optional surfaces, benchmark and property tests.
- **Build:** setuptools + wheel; version is sourced from `pytokencalc/_version.py`.
- **CI:** pytest matrix on Python 3.9–3.13 with `.[dev,tokenizers]`, ruff, and pip-audit.

## Public API

The top-level package exports, among others:

- Core counting: `count_tokens`, `TokenCounter`, `TokenCounterRegistry`, `TokenCounterCache`, `TokenCountResult`.
- Cost/pricing: `estimate_cost`, `estimate_usage`, `get_model_pricing`, `compare_models`, `pricing_status`, `load_pricing_override`, `Usage`, `CostBreakdown`.
- Catalog/endpoints: `get_model_spec`, `list_models`, `register_model_spec`, `compare_endpoints`, `endpoint_pricing`.
- Workflow: `preflight`, `reconcile`, `parse_usage`, `benchmark_counts`.
- Usage ledger and OpenRouter catalog import.
- CLI classes, REST server, MCP connector, and optional StatGuardian contracts.

Entry points include the `pytokencalc` CLI, `pytokencalc.server.PyTokenCalcServer`, and `pytokencalc.mcp_server`.

## Design Patterns

- **Registry + adapter:** the registry selects a provider counter; every adapter returns the same `TokenCountResult`.
- **Graceful provider omission:** registry construction catches provider failures so one unavailable dependency does not disable the rest.
- **Local-first with explicit escalation:** deterministic encoders are preferred; API counters are used where the tokenizer is inaccessible.
- **Layered pricing:** static table, override file, model aliases, usage breakdowns, endpoint comparison.
- **Optional surfaces:** REST, MCP, tokenizers, and quality validation are extras rather than default dependencies.
- **Facade API:** `count_tokens()` and `estimate_cost()` hide registry/pricing details.

## Data and Storage

- **Token cache:** process-local `TokenCounterCache`, keyed by provider + model + SHA-256 of text; TTL default 24 hours; max size default 10,000.
- **Cache eviction:** when full, sorts all keys by timestamp and removes roughly the oldest 10%; this is not a strict LRU.
- **Optional persistence:** `save_to_file` / `load_from_file` store token counts and timestamps as JSON; load failures are silently ignored.
- **Pricing data:** static in-code table with `PRICING_LAST_UPDATED = "2026-09"`, optional JSON override, and a freshness status API.
- **Usage ledger:** optional local ledger for usage events.
- **No database, no service-side durable state, no tenant isolation.**

The cache does not include tokenizer/encoding version in its key, so an encoder change can serve a stale count until TTL expiry. Cache statistics and eviction are unsynchronized; under concurrent workers, counters can race and an eviction can remove entries another thread is using.

## Concurrency and Performance

- Deterministic tokenization is CPU-bound and synchronous.
- Provider counters use blocking `requests` calls with timeouts (typically 5–30 seconds).
- The global cache is not protected by a mutex; the GIL makes individual dict operations atomic but not compound lookup/update/eviction sequences.
- The REST server is a normal Flask app; production concurrency depends on the caller's WSGI server.
- The MCP server is either stdio or an HTTP transport; no built-in worker pool or request queue is evident.
- The greatest cost risk is accidental generation in the Ollama path, followed by repeated remote tokenization when caching is bypassed or ineffective.
- No benchmark evidence was reviewed for high-concurrency REST/MCP operation.

## Security and Privacy

### Strengths

- No default network dependency and no default credentials.
- REST server defaults to `127.0.0.1`; the README explicitly warns that binding to `0.0.0.0` exposes an unauthenticated service.
- Provider credentials are configuration/environment inputs, not hardcoded.
- Input text is hashed for cache keys; raw text is not used as the key.
- Optional extras limit the default attack surface.
- Pricing and catalog data are local; no telemetry was observed.
- `SECURITY.md` gives a private-reporting path.

### Gaps

- **Unauthenticated network surfaces:** REST and HTTP MCP have no built-in auth, authorization, rate limiting, or request-size cap. Localhost is the safe default, but a misconfigured bind is a direct data/cost exposure.
- **Provider egress:** custom provider base URLs and Ollama endpoints are caller-controlled; the library does not restrict schemes, destinations, or private-network access.
- **Sensitive prompt text:** counts require the prompt text, and remote counters transmit it to the configured provider. This is inherent but not surfaced as a data-handling policy.
- **Silent estimation:** fallback estimates can be indistinguishable from real provider counts unless callers inspect `source`/metadata.
- **Cache persistence:** JSON cache files contain token counts and model/text hashes, not raw text, but they are unencrypted and unprotected by default.
- **No request authentication between the MCP connector and the library**; trust is process-local.

## Reliability and Observability

- Provider registry failures are logged and isolated.
- Provider HTTP calls use timeouts and, in several adapters, retry/fallback behavior.
- `pricing_status()` exposes table age; this is a useful freshness control.
- Cache hit/miss statistics are available.
- Errors are typed (`APIError`, `TokenCountError`, `ModelNotSupportedError`, etc.) at the public boundary.
- No structured tracing, request IDs, metrics export, or health endpoint for the REST/MCP surfaces.
- No circuit breaker around failing providers; each call can retry independently.
- Silent fallback estimates reduce failure visibility.
- No rate limiter for provider APIs or inbound requests.

## Testing, CI, and Quality

- 26 test modules and 358 static test functions.
- Coverage spans counting, pricing/costs, catalog, CLI, REST server, MCP tools, provider resilience, streaming, timeouts, usage ledger, reconciliation, preflight, and property-based tokenizer boundaries.
- CI runs pytest on Python 3.9–3.13 with `.[dev,tokenizers]`, plus ruff.
- `pip-audit` runs in CI, contradicting `SECURITY.md`'s statement that no dependency scanning exists.
- Optional-provider tests are generally mock-backed; real provider APIs are not exercised in CI.
- No live-provider conformance suite, no load test, no fuzzing for request parsing, and no coverage gate.
- The test suite is broad for a pure-Python library and is a genuine strength.

## Documentation, Packaging, and Release

- Source version is 1.5.0 and the package metadata is consistent with it.
- README has an explicit “What's new in 1.5.0” section and broad API examples.
- `SECURITY.md` is stale about dependency scanning.
- Pricing freshness is documented but the static table can lag provider changes; overrides are the escape hatch.
- Optional dependency versions are not fully pinned for library consumers; `requirements-lock.txt` supports reproducible development.
- Distribution artifacts exist under `dist/`; release provenance/signing was not verified.
- No tagged-release audit was performed.

## Strengths

- Broad, coherent provider abstraction with a stable result type.
- Strong deterministic/local path with zero default dependencies.
- Transparent pricing metadata, overrides, usage breakdowns, and freshness status.
- Registry resilience: one bad provider does not take down all counting.
- Good optional-surface separation for REST, MCP, and tokenizers.
- Substantial test suite, including property tests and failure-path coverage.
- Clear localhost default and an explicit warning about unauthenticated exposure.
- Honest fallback metadata exists (`source`, `cached`, provider/model), even though fallbacks can be silent in practice.

## Risks and Gaps

| Risk | Severity | Evidence | Impact |
|---|---|---|---|
| Ollama counting can trigger full generation | Medium | `tokenizers/ollama_counter.py`: `/api/generate`, `stream: false`, no `num_predict` | Unexpected GPU/CPU cost and latency for a “count” operation. |
| Custom-provider fallback reports estimated counts as API results | Medium | `tokenizers/custom_provider_counter.py`: response-length estimate, `source="api"` | Cost/context decisions use fabricated precision; failures are hidden. |
| Cache is unsynchronized and uses mixed clock semantics | Medium | `tokenizers/cache.py`: plain dict, `datetime.now()` vs `datetime.utcnow()` | Races in concurrent servers; TTL behavior around DST/clock changes. |
| REST/MCP surfaces have no auth or rate limiting | Medium | `server.py`, `mcp_server.py`; localhost default documented | Misconfigured bind exposes prompt text, provider credentials, and cost amplification. |
| Networked callers can direct requests to arbitrary provider endpoints | Low/Medium | custom provider `base_url`, Ollama `base_url` | SSRF-like egress and credential leakage to unintended hosts. |
| Static pricing table can drift | Low | `PRICING_TABLE`, `PRICING_LAST_UPDATED = "2026-09"` | Cost estimates become wrong until override/update. |
| Cache key omits encoder/model revision | Low | `_get_key(provider, model, text)` | Tokenizer changes can serve stale counts for up to TTL. |
| Eviction is approximate, not LRU | Low | oldest-10% sort in `_store` | Hot entries can be evicted; cache effectiveness is lower than claimed. |
| `SECURITY.md` understates CI scanning | Low | CI uses pip-audit; SECURITY says no scanning | Misleads security reviewers. |
| Optional integrations are not exercised against real services | Low/Medium | mock-backed tests | Provider/API drift may only appear in production. |

## Prioritized Recommendations

### P0 — accuracy and exposure truth

1. Change Ollama counting to use a non-generating tokenization endpoint when available, or set an explicit generation limit and document the cost. Never call `/api/generate` with an unbounded prompt for a pure counting request.
2. Make custom-provider fallback explicit: return a distinct source/quality flag, log it, and let callers opt out of estimated counts. Do not report character estimates as authoritative API counts.
3. Require explicit non-localhost opt-in for REST/MCP, and add authentication, request-size limits, rate limiting, and a startup warning before network exposure.
4. Add a provider egress policy: allowed schemes/hosts, optional private-network denial, and clear documentation that prompt text leaves the process.

### P1 — concurrency and correctness

5. Protect cache state with a lock or redesign it as a thread-safe bounded cache; use one clock domain (`time.monotonic()` for TTL, UTC for timestamps).
6. Include tokenizer/encoding version in cache keys and expose cache invalidation on pricing/tokenizer updates.
7. Add a circuit breaker and per-provider concurrency/timeout budget so one slow provider cannot exhaust worker threads.
8. Add live-provider contract tests (nightly/opt-in) plus a deterministic mock suite for every adapter.

### P2 — quality and documentation

9. Reconcile `SECURITY.md` with actual pip-audit/CI behavior and document the threat model for local vs network use.
10. Add load tests for REST/MCP under concurrent requests, and a coverage gate for the provider/fallback paths.
11. Document the difference between deterministic, provider-reported, and estimated counts in the public API reference.
12. Verify release artifacts and publish a reproducible build/provenance note.

## Audit Limitations

- No live provider API calls were made; provider behavior, rate limits, and current tokenizer accuracy were not revalidated.
- Unknown-model/freshness behavior in `pricing.py` was inspected at the API/table level but not exhaustively exercised across every alias and override combination.
- The REST/MCP servers were reviewed statically; no adversarial network testing, fuzzing, or load testing was performed.
- Test counts are static definitions, not a guaranteed pass count in this environment.
- Dependency vulnerabilities were not independently re-scanned; CI configuration was reviewed, not a fresh advisory database run.
