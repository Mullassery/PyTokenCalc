# Audit findings — 2026-10-19

This file records the repository-specific findings from the portfolio audit
conducted on 2026-10-19. It is documentation only; no code or release artifacts
were changed in this pass unless explicitly noted under "Implementation status".

Sources: the repository's own README/source/workflows, GitHub metadata and
Actions runs, PyPI metadata, and official competitor documentation. Claims are
marked as verified, inferred, or open questions. "Absent" means not found in the
inspected repository/docs, not proof that it cannot exist.

## What it is

Token counting and cost estimation across cloud, local, and custom LLM providers, with streaming counts, drift warnings, and a CLI.

## Verified strengths

- tiktoken/HF/local + live provider endpoints; streaming incremental count across BPE boundaries; custom providers; drift warnings; CLI; pure-Python wheel; 16 tests.
- One API across providers + cost is a useful utility.

## Verified gaps and user-facing risks

- Pricing table is a static snapshot and explicitly lacks current-generation GPT-5/Claude-4-era models.
- Anthropic/Google/Cohere counting requires network; README says no MCP transport despite the description; '99.9% accuracy' has no committed benchmark.
- GitHub release v0.1.0 vs PyPI 1.3.2.

## Direct competitors

- tiktoken (OpenAI exact), LiteLLM token/cost utilities, provider count-tokens APIs, Helicone cost tracking.

## Ranked next actions

- P1: automated pricing freshness + fail closed on unknown models (M).
- P1: align GitHub release/tag with PyPI (S).
- P2: offline provider tokenizers/no-network fallback (M).

## Do not build

- MCP transport; low demand and no clear workflow.

## Evidence gaps / validation needed

- No accuracy benchmark vs provider APIs; no per-row pricing-source audit trail.

## Recommended disposition

Invest; freshness is existential for a cost tool.

## Implementation status

Shipped pricing freshness + local overrides in this pass:

- `pricing_status()` (age/stale/model count/source) and
  `load_pricing_override(path)` for a local JSON table.
- CLI `pytokencalc pricing [--file PATH]`.
- 23 pricing/API tests pass; `tests/test_pricing_and_api.py` covers status,
  override cost calculation, and invalid files.

Still open: a fully automated upstream price feed (deliberately out of scope),
and provider-specific tokenizer coverage.
