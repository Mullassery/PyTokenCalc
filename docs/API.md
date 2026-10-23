# API Reference

## Quick start (top-level API)

```python
from pytokencalc import count_tokens, estimate_cost

tokens = count_tokens("Tell me a story about a robot", model="gpt-4o")
cost = estimate_cost("gpt-4o", input_tokens=tokens)
```

### `count_tokens(text, model="gpt-4o", provider=None) -> int`

Counts tokens in `text` for `model` and returns the input token count as a
plain `int`. Thin wrapper around `TokenCounterRegistry.count_tokens()`.

- `text` (str): text to tokenize.
- `model` (str): model ID, e.g. `"gpt-4o"`, `"claude-3-5-sonnet"`,
  `"llama-3-8b"`. Defaults to `"gpt-4o"` (local, offline, no API key).
- `provider` (str, optional): explicit provider (`"openai"`, `"anthropic"`,
  `"google"`, `"cohere"`, `"azure"`, `"huggingface"`, `"opensource"`,
  `"ollama"`). Auto-detected from `model` if omitted.

Raises `ValueError` if no counter matches, `RuntimeError` if the counter
itself fails (e.g. a network error for API-backed providers).

### `estimate_cost(model, input_tokens, output_tokens=0) -> float`

Returns the estimated cost **in USD** for a request, using the static
pricing table in [`pytokencalc/pricing.py`](../pytokencalc/pricing.py).
Raises `ValueError` if the model isn't safely resolvable to a pricing entry
(see [MODELS.md](MODELS.md) for what's covered, and the module docstring for
sources / update instructions).

Matching is exact or snapshot/version-suffixed: `gpt-4o-2024-11-20` resolves
to `gpt-4o`, but a genuinely different model such as `gpt-4.1` does **not**
inherit `gpt-4` pricing. Provider-prefixed IDs (`openai/gpt-4o`) are accepted.

```python
estimate_cost("gpt-4o", input_tokens=1000, output_tokens=250)
```

Note: this is unrelated to `OKFTokenBaselines.estimate_cost()`, which
predicts a *token count* from a historical input/output ratio, not a
dollar figure.

### `estimate_from_baseline(provider, model, task_type, input_tokens, *, baseline_dir=None) -> Optional[BaselineEstimate]`

Opt-in **historical baseline estimate** backed by saved samples in
`token_baselines/<provider>_<model>_<task_type>.json` (written by
`OKFTokenBaselines.save_baseline()`).

> **This is not an exact token count.** It extrapolates expected output from
> the stored average output/input ratio for that provider/model/task. It does
> not run a tokenizer. Use `count_tokens()` when you need exact counting.

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
# estimate.total_tokens == 1500, estimate.samples == 200
```

Returns `None` if no matching baseline exists. Raises `TypeError` for a
non-int `input_tokens`, `ValueError` for a negative one. `count_tokens()`
and `estimate_cost()` do **not** consult baselines.

## Lower-level API

For anything beyond the two convenience functions above, use
`TokenCounterRegistry` directly (`pytokencalc.tokenizers`):

```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()

# Full result object (input/output/image/system/tool tokens, latency,
# cache status, provider/platform metadata, timestamp)
result = registry.count_tokens("gpt-4o", "Hello world")
print(result.input_tokens, result.latency_ms, result.source)

# Vision (text + image) token counting, where the provider supports it
result = registry.count_vision("gpt-4-turbo", "Describe this image", num_images=1)

# Batch counting (strict by default: failures raise)
results = registry.count_batch([
    {"model": "gpt-4o", "text": "First prompt"},
    {"model": "gpt-4o", "text": "Second prompt"},
])

# Opt into zero-token error placeholders instead of raising
results = registry.count_batch(requests, strict=False)

# Discover providers/models
registry.list_providers()
registry.list_models()            # all models across providers
registry.list_models("openai")    # just one provider
```

### `TokenCountResult` fields

`input_tokens`, `output_tokens`, `image_tokens`, `system_tokens`,
`tool_tokens`, `total_tokens` (property, sum of the above), `cached`,
`source` (`"local"` / `"api"` / `"formula"` / `"cache"`), `latency_ms`,
`provider`, `model`, `platform`, `timestamp`, `session_id`.

When a result comes from the in-memory cache, `cached` is `True` and the
original `source`/`provider` metadata is preserved.

## CLI

```bash
pytokencalc count "Hello world" gpt-4          # full CLI, JSON output
pytokencalc providers
pytokencalc models [provider]
pytokencalc catalog [provider]                  # metadata + pricing
pytokencalc catalog import --file models.json   # OpenRouter snapshot
pytokencalc model-info gpt-4o
pytokencalc preflight --file request.json --model gpt-4o --max-output 500
pytokencalc reconcile --file response.json --model gpt-4o --expected-cost 0.001
pytokencalc usage add --file response.json --model gpt-4o --ledger usage.jsonl
pytokencalc usage report --ledger usage.jsonl
pytokencalc compare --models gpt-4o,gpt-4o-mini --input-tokens 1000 --output-tokens 500
pytokencalc endpoints import --file endpoints.json --model openai/gpt-4o
pytokencalc endpoints list --model openai/gpt-4o
pytokencalc endpoints compare --model openai/gpt-4o --input-tokens 1000
pytokencalc benchmark --file samples.jsonl
pytokencalc cache-stats
pytokencalc help

pycount "Hello world"                          # quick one-liner CLI
pycount -m claude-3-sonnet -j "Hello world"    # JSON output
```

## Model catalog

```python
from pytokencalc import get_model_spec, list_models

spec = get_model_spec("openai/gpt-4o")
print(spec.context_length, spec.max_output_tokens, spec.input_modalities)
print(spec.pricing.input_per_million)

for model in list_models("anthropic"):
    print(model.id, model.context_length)
```

The catalog is a reviewed built-in snapshot (not a live feed). `ModelSpec`
carries canonical ID, aliases, provider, tokenizer family, context/output
limits, modalities, and optional provider endpoints. Add custom metadata with
`register_model_spec()`.

## Usage-aware costs

`Usage` separates total prompt tokens from cache reads/writes:

```python
from pytokencalc import Usage, estimate_usage

usage = Usage(
    input_tokens=1_000,
    output_tokens=250,
    cached_input_tokens=400,   # subset of input_tokens
    cache_write_tokens=100,    # subset of input_tokens
)
breakdown = estimate_usage("gpt-4o", usage)
print(breakdown.total_usd)
print(breakdown.to_dict())
```

`cached_input_tokens` and `cache_write_tokens` are billed at the model's cache
rates when configured, otherwise at the normal input rate. `reasoning_tokens`
is informational and is normally included in `output_tokens`, so it is not
billed twice. `Usage.request_count` applies any per-request fee.

```python
from pytokencalc import compare_models

for item in compare_models(["gpt-4o", "gpt-4o-mini"], usage):
    print(item.model, item.cost.total_usd if item.cost else item.error)
```

## Reconciliation

```python
from pytokencalc import reconcile

result = reconcile(
    "gpt-4o",
    response,                       # full provider response or {"usage": ...}
    provider="openrouter",
    expected_cost_usd=0.001,
)
print(result.usage)
print(result.cost.total_usd, result.delta_usd, result.delta_percent)
print(result.provider_reported_cost_usd)
```

Supports OpenAI (`prompt_tokens` / `completion_tokens`), Anthropic
(`input_tokens`, cache creation/read), OpenRouter (`usage.cost`,
`cache_write_tokens`), and generic usage mappings.

## Chat preflight

```python
from pytokencalc import preflight

result = preflight(
    [
        {"role": "system", "content": "Be concise."},
        {"role": "user", "content": "Explain vector databases."},
    ],
    "gpt-4o",
    tools=[...],                    # optional tool schemas
    max_output_tokens=500,
)
print(result.input_tokens, result.fits, result.estimated_cost_usd)
print(result.warnings)
```

Text tokens use the real model tokenizer. Chat framing, tool-schema overhead,
and image tokens are estimates; `warnings` says when image counting is not
available for the selected provider. Context fit uses the catalog's context
window (`None` when the model is unknown).

## OpenRouter snapshot import

No network request is made by the library. Download the public catalog, then
import it explicitly:

```bash
curl -s https://openrouter.ai/api/v1/models -o models.json
pytokencalc catalog import --file models.json
```

```python
from pytokencalc import import_openrouter_catalog_file

result = import_openrouter_catalog_file("models.json")
print(result.to_dict())
```

OpenRouter per-token prices are converted to PyTokenCalc's per-million rates;
`request`, cache-read, and cache-write prices are preserved. Variant IDs
containing `:` (`:free`, `:nitro`) are skipped by default; pass
`include_variants=True` to include them. Imported prices are in-memory only --
persist them with a pricing override if you need reproducibility across runs.

## Endpoint comparison

```python
from pytokencalc import compare_endpoints, import_openrouter_endpoints_file, Usage

# Download /api/v1/models/{author}/{slug}/endpoints first; no runtime fetch.
import_openrouter_endpoints_file("endpoints.json", model_id="openai/gpt-4o")

for item in compare_endpoints("openai/gpt-4o", Usage(input_tokens=1_000, output_tokens=500)):
    print(item.endpoint.provider, item.cost.total_usd if item.cost else item.error)
```

Endpoint-specific prices override the model's price. Endpoints without a price
fall back to the model price; if neither exists the endpoint is reported last
with an error. Imported uptime/latency/throughput are metadata only --
PyTokenCalc does not route requests.

## Parity benchmark

```python
from pytokencalc import benchmark_counts
from pytokencalc.benchmark import load_samples

summary = benchmark_counts(load_samples("samples.jsonl"))
print(summary.exact_match_rate, summary.mean_absolute_percent_error)
```

Each JSONL line is a prompt plus provider usage:

```json
{"model": "gpt-4o", "prompt": "Hello world", "usage": {"prompt_tokens": 2}}
```

```bash
pytokencalc benchmark --file samples.jsonl
```

The benchmark is offline; you supply the provider-reported usage samples.

## Usage ledger

```python
from pytokencalc import UsageLedger, reconcile

ledger = UsageLedger("usage.jsonl")
result = reconcile("gpt-4o", response, expected_cost_usd=0.001)
ledger.record_reconciliation(result, tags={"env": "prod"}, generation_id="gen-1")

print(ledger.summary())
print(ledger.list_records(limit=10))
```

```bash
pytokencalc usage add --file response.json --model gpt-4o --ledger usage.jsonl \
  --tags env=prod --generation-id gen-1
pytokencalc usage report --ledger usage.jsonl
pytokencalc usage list --ledger usage.jsonl --limit 10
```

The ledger is append-only JSONL. It is optional; nothing is written unless you
construct a `UsageLedger` and call `record_reconciliation()`/`append()`.

## Pricing overrides

`load_pricing_override(path)` merges `{last_updated, models}` into the built-in
table by default; pass `replace=True` to replace it. Accepts `YYYY-MM` or
`YYYY-MM-DD` for `last_updated`, and unparseable dates are reported as stale
instead of being silently treated as current.

## REST server (optional, `pip install "pytokencalc[server]"`)

```python
from pytokencalc.server import run_server
run_server()  # binds 127.0.0.1:8005 by default
```

`POST /count`, `POST /count-vision`, `GET /providers`, `GET /models`,
`GET /cache`, `DELETE /cache`, `GET /health`.

OpenRouter-style additions:

- `GET /v1/models?provider=...` — normalized catalog metadata
- `POST /v1/cost` — `{model, usage: {input_tokens, output_tokens, ...}}`
- `POST /v1/reconcile` — `{model, response, provider?, expected_cost_usd?}`
- `POST /v1/preflight` — `{model, messages, tools?, max_output_tokens?}`
- `GET /openapi.json` — OpenAPI 3.0 description

The server binds to `127.0.0.1` by default and does not implement
authentication. Pass `host="0.0.0.0"` explicitly only if you're putting
your own auth/network controls in front of it.

## Model discovery

```python
from pytokencalc.model_discovery import ModelDiscovery

ModelDiscovery.suggest_provider("llama-2-7b")     # -> providers list + confidence
ModelDiscovery.lookup_model("llama-2-7b")         # -> detailed lookup dict
print(ModelDiscovery.get_discovery_report("llama-2-7b"))  # human-readable report
```

## Custom / BYOM providers

See [CUSTOM_PROVIDERS.md](../CUSTOM_PROVIDERS.md) and
[ADDING_PROVIDERS.md](archive/ADDING_PROVIDERS_v0.7.md) (historical, describes v0.7).
