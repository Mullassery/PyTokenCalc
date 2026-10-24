# Competitive intelligence in roadmap and upgrade work

**Policy date:** 2026-10-19

Competitive findings are an input to product decisions, not a one-off report.
Every pending roadmap item, new feature, and routine dependency upgrade should
check the repository's [`AUDIT_FINDINGS.md`](AUDIT_FINDINGS.md) before work
starts, and record the decision in the PR or changelog.

## Required check before building

1. **Read `AUDIT_FINDINGS.md`.** Find the relevant competitor row and the
   ranked next actions. If the finding is stale, update it with a dated source.
2. **Name the competitor and the user problem.** A feature is not justified by
   "competitor has it". State the workflow it unlocks, who needs it, and how
   often. Mark unverified demand as a hypothesis.
3. **Prefer reuse over new code.** Check whether an existing Mullassery repo
   already provides the capability (see `BUNDLES.md` in the profile repo and
   the bundle role file in this repo, when present). Typical reuse:
   - crawling/fetching/robots/SSRF → **MudFish**
   - architecture maps / PR diffs → **CodeAtlas**
   - data-quality contracts / validation → **StatGuardian**
   - token counting / cost tables → **PyTokenCalc**
   - dependency graph / advisories / SBOM → **PyDeepMesh**
   - segmentation / CLV / churn → **ClusterAudienceKit**
   - activation / lineage / PII → **PyReverseETL**
   - fleet state sync → **SyncFleet** (only after conflict resolution)
4. **Choose one disposition:** build, integrate, defer, or reject. Write it
   down. A rejection with a reason is a successful outcome.
5. **For routine upgrades**, check whether the upgrade closes a known
   competitor gap or breaks a differentiated capability. Run the tests that
   cover the affected path; do not merge a green build that silently changes a
   user-visible contract.

## PR / changelog checklist

- [ ] Competitor and source URL/date recorded (or "no direct competitor").
- [ ] User impact and frequency stated; unverified demand labelled.
- [ ] Reuse check done against sibling repos/bundles.
- [ ] Failure mode and rollback considered (especially auth, PII, cost).
- [ ] Docs/roadmap status updated honestly.
- [ ] Tests or a manual verification command included.

## Review cadence

- Refresh the competitor row when a release changes the capability.
- Re-check the full `AUDIT_FINDINGS.md` at least quarterly and before a major
  release.
- If a finding is wrong or stale, correct it in the same PR that relies on it.

## Non-goals

- Copying features for parity.
- Adding a dependency just because a competitor uses it.
- Treating star counts or download counts as proof of user need.

## OSS gap analysis — 2026-10-24

**Scope.** Covers PyTokenCalc v1.5.0 as implemented here: ten counters, a static
24-model USD table, `Usage`/`CostBreakdown`, preflight/reconcile, the ledger, REST
v1, and optional MCP tools. Compared with OSS token-counting and cost tools.

### Comparable OSS projects

| Project | License | Activity | Why comparable |
|---|---|---|---|
| tiktoken | MIT | PyPI 0.14.0, 2026-08-17 | Offline OpenAI tokenization |
| tokencost | MIT | 0.1.26, 2025-08-13; repo 2025-09-05 | Multi-model token cost estimation |
| LiteLLM | MIT (core) | 1.106.3, 2026-10-24 | Provider abstraction with token/cost tracking |
| Helicone | Apache-2.0 | Latest release not verified | OSS LLM observability with cost tracking |

### Capability comparison

| Capability | PyTokenCalc | tiktoken | tokencost | LiteLLM | Helicone |
|---|---|---|---|---|---|
| Offline OpenAI token counts | Yes | Yes | Partial | Partial | No |
| Multi-provider token counting | Yes | No | Partial | Partial | Partial |
| Bundled pricing table | Yes | No | Yes | Yes | Yes |
| Broad model pricing coverage | Partial | No | Yes | Yes | Yes |
| Cache/reasoning/request-fee detail | Yes | No | Partial | Yes | Partial |
| Provider-reported cost reconciliation | Yes | No | No | Partial | Partial |
| Pre-call cost estimation | Yes | No | Yes | Partial | No |
| Usage ledger | Yes | No | No | Yes | Yes |
| REST API or MCP | Yes | No | No | Yes | Yes |
| Zero required runtime dependencies | Yes | No | No | No | No |
| Automatic request capture | No | No | No | Yes | Yes |

"Partial": tokencost/LiteLLM lean on OpenAI tokenizers and approximate elsewhere;
Helicone derives counts from traffic, so it cannot count offline. PyTokenCalc has
broad provider hooks but only 24 priced models.

### Gaps that matter (ranked)

1. **Pricing breadth and freshness are the biggest accuracy gap.** The table has
   24 models with `PRICING_LAST_UPDATED = "2026-09"` and is updated by hand;
   tokencost advertises 400+ models and LiteLLM maintains a broad cost map.
   Billing-adjacent use needs provenance per row and a repeatable refresh path.
   Build an import pipeline with source URLs, retrieval dates, and CI freshness
   checks; do not scrape sources whose terms forbid it.

2. **Anthropic, Google, and Cohere counting requires a live vendor API.** Those
   counters call the provider with credentials, so CI and offline estimation need
   network access and secrets. Build local tokenizers where licenses and artifacts
   permit; otherwise label results approximate and keep the API for exact counts.

3. **Usage capture is caller-supplied.** `Usage` is constructed by the caller;
   there is no interception of SDK calls or gateway traffic. LiteLLM and Helicone
   capture automatically. Integrate with OpenAnchor/LiteLLM callbacks instead of
   writing provider SDK wrappers here.

4. **No spend enforcement or quota layer.** The ledger records costs but does not
   enforce team/key budgets or block calls. That is a gateway concern covered by
   LiteLLM/Helicone. Defer it; expose the ledger and preflight so a gateway or
   OpenAnchor can enforce policy.

5. **No dashboard or team-facing UI.** REST v1 and MCP expose the data, but there
   is no cost explorer, budget view, or alerting. Defer it; integrate with an
   existing observability backend rather than growing one here.

### Where we are differentiated

- Provider-agnostic counting through a registry, with offline OpenAI/Azure and
  Hugging Face paths plus custom providers, in a zero-dependency core.
- `CostBreakdown` handles cache reads/writes, request fees, reasoning tokens, and
  provider-reported reconciliation rather than a single input/output rate.
- Preflight, JSONL ledger, REST v1, and optional MCP expose the same cost model to
  scripts, services, and agents without a gateway.
- Pricing is local and deterministic, with no network call required for estimates.

### Disposition

- **Build:** a provenance-rich pricing import/refresh pipeline with CI freshness
  checks; local Anthropic/Google tokenizers where permitted; default staleness
  warnings and accuracy labels.
- **Integrate/reuse:** OpenAnchor or LiteLLM callbacks for automatic usage;
  vendor pricing pages and published tokenizer artifacts; existing observability
  backends for dashboards and alerts.
- **Defer/reject:** gateway quota enforcement, a hosted cost dashboard, and
  scraping pricing without clear terms. Those duplicate LiteLLM/Helicone.

### Sources

- tiktoken: https://github.com/openai/tiktoken (MIT; PyPI 0.14.0, 2026-08-17).
- tokencost: https://github.com/AgentOps-AI/tokencost (MIT; 0.1.26, 2025-08-13).
- LiteLLM: https://github.com/BerriAI/litellm (1.106.3, 2026-10-24; MIT core).
- Helicone: https://github.com/Helicone/helicone (Apache-2.0).
- Local: `README.md`, `pytokencalc/pricing.py`, `pytokencalc/tokenizers/`.
