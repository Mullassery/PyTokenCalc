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
Raises `ValueError` if the model isn't in the pricing table (see
[MODELS.md](MODELS.md) for what's covered, and the module docstring for
sources / update instructions).

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

# Batch counting
results = registry.count_batch([
    {"model": "gpt-4o", "text": "First prompt"},
    {"model": "gpt-4o", "text": "Second prompt"},
])

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

## CLI

```bash
pytokencalc count "Hello world" gpt-4          # full CLI, JSON output
pytokencalc providers
pytokencalc models [provider]
pytokencalc cache-stats
pytokencalc help

pycount "Hello world"                          # quick one-liner CLI
pycount -m claude-3-sonnet -j "Hello world"    # JSON output
```

## REST server (optional, requires `flask`)

```python
from pytokencalc.server import run_server
run_server()  # binds 127.0.0.1:8005 by default
```

`POST /count`, `POST /count-vision`, `GET /providers`, `GET /models`,
`GET /cache`, `DELETE /cache`, `GET /health`.

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
