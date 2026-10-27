<p align="center">
  <img src="docs/assets/pytokencalc-banner.svg" alt="PyTokenCalc — know your LLM costs before you hit send" width="100%" />
</p>

# PyTokenCalc

[![PyPI](https://img.shields.io/pypi/v/pytokencalc)](https://pypi.org/project/pytokencalc/)
[![CI](../PyTokenCalc/actions/workflows/ci.yml/badge.svg)](../PyTokenCalc/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

LLM token counting and cost estimation across cloud, local, and custom providers.

## What it is

PyTokenCalc counts tokens across OpenAI, Anthropic, Google, Cohere, Azure-hosted OpenAI
models, HuggingFace/open-source models, Ollama, and custom endpoints, then estimates the
dollar cost of a request from a maintained per-model pricing table. It is pure Python —
the speed comes from the `tiktoken` and HuggingFace `tokenizers` libraries it wraps, not
from compiled code in PyTokenCalc itself. It installs and imports as `pytokencalc`.

## What's new in 1.5.0

- **Model catalog** — context windows, output limits, modalities, tokenizer
  families, aliases, provider-prefixed IDs, and optional endpoint metadata.
- **Usage-aware costs** — cache reads/writes, request fees, line-item
  `CostBreakdown`, and `compare_models()`.
- **Chat preflight** — `preflight(messages, tools=..., max_output_tokens=...)`
  reports prompt tokens, context fit, and expected cost before sending.
- **Usage reconciliation** — `reconcile(response)` normalizes OpenAI,
  Anthropic, and OpenRouter usage and compares actual vs expected cost.
- **OpenRouter snapshot import** — offline import for model and endpoint
  snapshots, including per-provider pricing/uptime/latency metadata.
- **Endpoint comparison** — `compare_endpoints()` ranks providers serving the
  same model by cost.
- **Usage ledger** — optional JSONL spend/usage summaries.
- **Parity benchmark** — compare local counts against provider-reported usage.
- **REST v1 + OpenAPI** — `/v1/models`, `/v1/cost`, `/v1/reconcile`,
  `/v1/preflight`, and `/openapi.json`.

## Features / Highlights

- **Multi-provider** — OpenAI, Anthropic Claude, Google Gemini, Cohere, Azure-hosted
  OpenAI models, HuggingFace/open-source models, Ollama, and any custom HTTP endpoint you
  register.
- **Provider-accurate tokenization** — `tiktoken` for OpenAI and Azure-hosted OpenAI
  models, the HuggingFace `transformers` tokenizer, and live count-tokens endpoints for
  Anthropic/Google/Cohere.
- **Pricing freshness** — `pricing_status()` reports the snapshot's age and
  flags it stale after 90 days; `load_pricing_override(path)` merges a local
  JSON pricing file into the built-in table for newer/private models (use
  `replace=True` to replace it). `pytokencalc pricing` exposes it.
- **Real cost estimation** — `estimate_cost()` is backed by a per-model USD pricing table
  (input vs. output rates), not a guess; see
  [`pytokencalc/pricing.py`](pytokencalc/pricing.py) for sources and last-updated date.
- **Model catalog** — `get_model_spec()` / `list_models()` expose context windows,
  output limits, tokenizer families, modalities, aliases, and provider-prefixed IDs.
- **Usage-aware costing** — `estimate_usage()` handles cache reads/writes, request
  fees, and line-item cost breakdowns; `compare_models()` ranks models for one
  usage profile. The legacy `estimate_cost()` API still works.
- **Reconciliation** — `reconcile(response)` normalizes OpenAI, Anthropic, and
  OpenRouter usage metadata and compares actual cost with your preflight estimate.
- **OpenRouter snapshot import** — `import_openrouter_catalog_file()` converts a
  downloaded `/api/v1/models` JSON snapshot into local catalog/pricing metadata;
  `import_openrouter_endpoints_file()` adds per-provider endpoint pricing/stats.
- **Endpoint comparison** — `compare_endpoints()` ranks providers serving the same
  model by cost, with uptime/latency/throughput metadata when imported.
- **Parity benchmark** — `benchmark_counts()` compares local counts with
  provider-reported usage from a JSONL sample set.
- **Optional usage ledger** — `UsageLedger` appends reconciliation records as JSONL
  and summarizes spend by model/provider; no service or database required.
- **REST + OpenAPI** — `/v1/models`, `/v1/cost`, `/v1/reconcile`, `/v1/preflight`,
  and `/openapi.json`, alongside the existing count/cache endpoints.
- **Chat preflight** — `preflight(messages, tools=..., max_output_tokens=...)`
  estimates prompt tokens, context fit, and cost before sending a request.
- **Fast local counting** — sub-millisecond for local (tiktoken/HuggingFace) providers on
  typical hardware.
- **Batch processing** — count tokens for many prompts in one call.
- **Custom / BYOM models** — register your own provider or fine-tuned model (see
  [`CUSTOM_PROVIDERS.md`](CUSTOM_PROVIDERS.md)).
- **Streaming/incremental counting** — `counter.streaming(model)` gives a running token
  count as chunks of a live LLM response arrive, correct across chunk/BPE-merge
  boundaries (not a naive per-chunk sum).
- **Encoding drift detection** — `get_tokenizer_info()["drift_warnings"]` flags if an
  installed encoding's tokenization has changed since it was last verified.
- **CLI** — `pytokencalc` and the `pycount` shortcut, installed automatically.

## API at a glance

| Need | API |
|---|---|
| Count plain text | `count_tokens(text, model)` |
| Estimate input/output cost | `estimate_cost(model, input_tokens, output_tokens)` |
| Price cache/request usage | `Usage` + `estimate_usage(model, usage)` |
| Compare models | `compare_models(models, usage)` |
| Check a chat request before sending | `preflight(messages, model, tools=..., max_output_tokens=...)` |
| Check actual usage after a response | `reconcile(model, response)` |
| Look up context/metadata | `get_model_spec(model)` / `list_models()` |
| Compare providers for one model | `compare_endpoints(model, usage)` |
| Import OpenRouter data | `import_openrouter_catalog_file(path)` / `import_openrouter_endpoints_file(path)` |
| Persist usage | `UsageLedger(path)` |
| Measure tokenizer parity | `benchmark_counts(samples)` |

## Who it's for / Use cases

- **Budget tracking** — count a prompt and price the input/output before sending a
  request.
- **Preventing cost overruns** — reject requests above a cost threshold.
- **Comparing providers** — price the same prompt across models before choosing one.
- **Preflight checks** — reject a request before it exceeds context or budget.
- **Spend reconciliation** — compare estimated and provider-reported cost.
- **Provider selection** — compare endpoint prices for open models.
- **Streaming cost awareness** — track tokens as a response streams in.

## What it is not

- **MCP transport is optional.** `pytokencalc.TokenCalculator` has real handlers (token
  counts from the tokenizer registry, costs from the pricing table), and the FastMCP
  transport ships only with `pip install "pytokencalc[mcp]"`; without that extra,
  building a server raises an actionable install error. Budget/usage tools are in-memory
  and process-scoped.
- **No committed benchmark result.** `benchmark_counts()` provides an offline
  harness, but there is no checked-in provider results file backing a specific
  performance claim. The speed numbers are informal local observations; for
  OpenAI models PyTokenCalc *is* `tiktoken` under the hood, with a roughly 2–5%
  wrapper overhead, not a speedup.
- **Lint/type coverage is partial.** `ruff check` runs in CI, but `black` formatting and
  `mypy` typing are configured yet not enforced (separate passes).
- **Anthropic/Google/Cohere counting makes a live network call** to the provider's API, so
  those paths need the relevant package installed and an API key set.
- **Provider coverage is a maintained table, not exhaustive.** See
  [`docs/MODELS.md`](docs/MODELS.md) for exactly which models are covered.
- **Catalog and preflight metadata are snapshots, not live truth.** Context
  windows, aliases, and pricing can drift. Chat framing, tool-schema overhead,
  and image tokens are estimates; use `reconcile(response)` against provider
  usage to measure the difference on your own workload.

## Project status

**Beta.** Current version **1.5.0** (`Development Status :: 4 - Beta` in
`pyproject.toml`). The local OpenAI/HuggingFace counting path is well covered by tests;
provider-specific paths require their optional dependencies. See
[`docs/internal/ROADMAP_HONEST.md`](docs/internal/ROADMAP_HONEST.md) for the full honest status and technical-debt
list.

## MCP server

The 12 MCP tools are now served over a real FastMCP transport:

```bash
pip install "pytokencalc[mcp]"

# stdio (Claude Desktop, Cursor, etc.)
pytokencalc-mcp --transport stdio

# HTTP
pytokencalc-mcp --transport http --host 127.0.0.1 --port 8778
```

```python
from pytokencalc import TokenCalculator

server = TokenCalculator().create_mcp_server()
server.run(transport="stdio")
```

The tools are the same real handlers documented in `_mcp_tools.py`; no
external `dab` binary or separate service is involved. Budget/usage state is
process-scoped, as documented.

## Installation

```bash
pip install pytokencalc
# or with uv
uv pip install pytokencalc

# with local tokenizer support (tiktoken + HuggingFace transformers)
pip install "pytokencalc[tokenizers]"

# optional HTTP surfaces
pip install "pytokencalc[server]"   # Flask REST API
pip install "pytokencalc[mcp]"      # FastMCP transport
```

Requires Python 3.9+.

## Quick start

```python
from pytokencalc import count_tokens, estimate_cost

# Count tokens instantly (runs locally via tiktoken — no API key needed)
tokens = count_tokens("Tell me a story about a robot", model="gpt-4o")
print(f"Tokens: {tokens}")

# Estimate cost from the pricing table
cost = estimate_cost("gpt-4o", input_tokens=tokens)
print(f"Cost: ${cost:.6f}")
```

## Usage

**Budget tracking** (Anthropic/Google/Cohere models require the relevant package and an
API key; OpenAI/GPT models work offline out of the box):

```python
from pytokencalc import count_tokens, estimate_cost

prompt = "Hello"
reply_tokens_estimate = 50  # however you estimate expected output length

input_tokens = count_tokens(prompt, model="claude-3-opus")
cost = estimate_cost("claude-3-opus", input_tokens, reply_tokens_estimate)
print(f"Estimated cost: ${cost:.4f}")
```

**Prevent overruns:**

```python
tokens = count_tokens(prompt, model="gpt-4")
if estimate_cost("gpt-4", tokens) > 0.10:
    print("Request too expensive, rejected")
```

**Compare providers:**

```python
prompt = "Explain quantum computing in one paragraph."
for model in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]:
    tokens = count_tokens(prompt, model=model)
    cost = estimate_cost(model, tokens)
    print(f"{model}: {tokens} tokens, ${cost:.6f}")
```

**Compare models for one usage profile:**

```python
from pytokencalc import Usage, compare_models

usage = Usage(input_tokens=2_000, output_tokens=500, cached_input_tokens=800)
for item in compare_models(["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet"], usage):
    cost = item.cost.total_usd if item.cost else None
    print(item.model, cost, item.error)
```

**Preflight a chat request before sending it:**

```python
from pytokencalc import preflight

result = preflight(
    [
        {"role": "system", "content": "Be concise."},
        {"role": "user", "content": "Explain vector databases."},
    ],
    "gpt-4o",
    max_output_tokens=500,
)
print(result.input_tokens, result.context_remaining, result.fits)
print(result.estimated_cost_usd, result.warnings)
```

**Reconcile provider usage after a response:**

```python
from pytokencalc import reconcile

result = reconcile(
    "gpt-4o",
    response,  # full provider response or {"usage": ...}
    provider="openrouter",
    expected_cost_usd=0.001,
)
print(result.cost.total_usd, result.delta_usd, result.provider_reported_cost_usd)
```

**Import OpenRouter snapshots and compare endpoints** — explicit and offline;
the library never fetches these URLs for you:

```bash
curl -s https://openrouter.ai/api/v1/models -o models.json
pytokencalc catalog import --file models.json
curl -s https://openrouter.ai/api/v1/models/openai/gpt-4o/endpoints -o endpoints.json
pytokencalc endpoints import --file endpoints.json --model openai/gpt-4o
```

```python
from pytokencalc import Usage, compare_endpoints

for item in compare_endpoints("openai/gpt-4o", Usage(input_tokens=1_000)):
    print(item.endpoint.provider, item.cost.total_usd if item.cost else item.error)
```

**Record usage in an optional JSONL ledger:**

```python
from pytokencalc import UsageLedger, reconcile

ledger = UsageLedger("usage.jsonl")
ledger.record_reconciliation(
    reconcile("gpt-4o", response, expected_cost_usd=0.001),
    tags={"env": "prod"},
    generation_id="gen-1",
)
print(ledger.summary())
```

**Measure tokenizer parity against real provider usage:**

```python
from pytokencalc import benchmark_counts
from pytokencalc.benchmark import load_samples

summary = benchmark_counts(load_samples("samples.jsonl"))
print(summary.exact_match_rate, summary.mean_absolute_percent_error)
```

**Streaming/incremental counting** — recomputes against the full accumulated text on each
chunk, so it stays correct across BPE chunk boundaries:

```python
from pytokencalc import TokenCounterRegistry

registry = TokenCounterRegistry()
stream = registry.get_counter("openai").streaming(model="gpt-4o")

for chunk in live_response_chunks:  # e.g. OpenAI SSE deltas
    delta = stream.add_chunk(chunk or "")
    print(f"+{delta} tokens, {stream.total_tokens} total")
```

**Historical baseline estimates (opt-in, not exact)** — if you have saved
samples for a provider/model/task, `estimate_from_baseline()` extrapolates
total tokens from the historical output/input ratio. This is a planning
estimate, **not** a tokenizer count, and `count_tokens()`/`estimate_cost()`
never use it:

```python
from pathlib import Path
from pytokencalc import OKFTokenBaselines, TokenBaseline, estimate_from_baseline

store = OKFTokenBaselines(baseline_dir=Path("token_baselines"))
store.save_baseline(TokenBaseline(
    provider="openai", model="gpt-4o", task_type="chat",
    avg_input_tokens=100, avg_output_tokens=50, samples=200,
    percentile_95_input=250, percentile_95_output=140,
))

estimate = estimate_from_baseline("openai", "gpt-4o", "chat", 1000)
print(estimate.total_tokens)  # 1500 -- baseline estimate, not exact
print(estimate.p95_output_tokens)           # stored historical p95 output
print(estimate.predicted_p95_output_tokens) # p95 scaled to the 1000-token input
```

`BaselineEstimate` also exposes `p95_output_tokens` (the stored historical
95th-percentile output) and `predicted_p95_output_tokens` (that p95 scaled by
`input_tokens / avg_input_tokens`, matching the mean prediction). Both are
planning estimates for tail behavior, not guarantees.

Save baselines from real `(prompt, output_tokens)` samples with the CLI.
Prompts are tokenized with the exact counter for the given model; output
tokens should come from your own request logs. Samples are never fabricated
or padded.

```bash
# JSONL: one object per line
# {"prompt": "Explain BPE", "output_tokens": 120}
pytokencalc baseline from-jsonl samples.jsonl \
    --provider openai --model gpt-4o --task-type chat

# JSON: an array, or {"provider": ..., "model": ..., "task_type": ..., "samples": [...]}
pytokencalc baseline save --samples samples.json \
    --provider openai --model gpt-4o --task-type chat

pytokencalc baseline list --provider openai
pytokencalc baseline compare --provider openai --task-type chat
```

`baseline compare` reports averages plus `p95_input_tokens`,
`p95_output_tokens`, and `p95_total_tokens` for each model. All commands accept
`--baseline-dir DIR` (default: `./token_baselines`).

Returns `None` when no baseline exists. For exact counts use `count_tokens()`.

**CLI:**

```bash
pytokencalc --help
pycount "Tell me a story about a robot" --model gpt-4o
```

## Documentation

- [API Reference](docs/API.md) — top-level functions, the full registry API, CLI, and REST server
- [Supported Models](docs/MODELS.md) — provider list, offline vs. API-backed, pricing table coverage
- [Custom Providers](CUSTOM_PROVIDERS.md) — register your own endpoint or BYOM
- [CLI Quick Start](QUICK_START_CLI.md) — the `pycount` terminal command
- [Architecture](docs/ARCHITECTURE.md) — component overview, request flow, and honest architectural gaps
- [Examples](examples/) — runnable code samples
- [Honest status & roadmap](docs/internal/ROADMAP_HONEST.md) — what's tested, what isn't, known bugs, and technical debt
- [Changelog](CHANGELOG.md) — release history, including 1.5.0

## Known issues and deferred work

**Blocked / failed:**
- Automated upstream price feed (deliberately out of scope).
- Complete current-generation model coverage.

**Rejected / deferred:**
- Bundling the MCP transport (FastMCP) as a mandatory dependency.

Full shipped/blocked/rejected detail: [`docs/internal/QUEUE_STATUS.md`](docs/internal/QUEUE_STATUS.md).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report security issues per
[SECURITY.md](SECURITY.md).

```bash
pip install -e ".[dev,tokenizers]"
pytest tests/ -v --cov=pytokencalc
ruff check .
```

## Related projects

- [PyStreamXL](../PyStreamXL) — stream large Excel workbooks with constant memory
- [PyStreamPDF](../PyStreamPDF) — token-efficient PDF extraction for RAG
- [PyStreamMCP](../PyStreamMCP) — context and token optimization for AI agents
- [PyStreamAI](../PyStreamAI) — ML deployment toolkit (canary/A-B, cost tracking, ONNX)
- [PyTokenCalc](../PyTokenCalc) — LLM token counting and cost estimation
- [Browse all projects](../Mullassery-profile)

## License

This project is licensed under the [Apache License 2.0](LICENSE).

---

If PyTokenCalc saves you from a surprise bill, a star helps other engineers find it.
