# PyTokenCalc

[![PyPI](https://img.shields.io/pypi/v/pytokencalc)](https://pypi.org/project/pytokencalc/)
[![CI](https://github.com/Mullassery/PyTokenCalc/actions/workflows/ci.yml/badge.svg)](https://github.com/Mullassery/PyTokenCalc/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

LLM token counting and cost estimation across cloud, local, and custom providers.

## What it is

PyTokenCalc counts tokens across OpenAI, Anthropic, Google, Cohere, Azure-hosted OpenAI
models, HuggingFace/open-source models, Ollama, and custom endpoints, then estimates the
dollar cost of a request from a maintained per-model pricing table. It is pure Python —
the speed comes from the `tiktoken` and HuggingFace `tokenizers` libraries it wraps, not
from compiled code in PyTokenCalc itself. It installs and imports as `pytokencalc`.

## Features / Highlights

- **Multi-provider** — OpenAI, Anthropic Claude, Google Gemini, Cohere, Azure-hosted
  OpenAI models, HuggingFace/open-source models, Ollama, and any custom HTTP endpoint you
  register.
- **Provider-accurate tokenization** — `tiktoken` for OpenAI and Azure-hosted OpenAI
  models, the HuggingFace `transformers` tokenizer, and live count-tokens endpoints for
  Anthropic/Google/Cohere.
- **Real cost estimation** — `estimate_cost()` is backed by a per-model USD pricing table
  (input vs. output rates), not a guess; see
  [`pytokencalc/pricing.py`](pytokencalc/pricing.py) for sources and last-updated date.
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

## Who it's for / Use cases

- **Budget tracking** — count a prompt and price the input/output before sending a
  request.
- **Preventing cost overruns** — reject requests above a cost threshold.
- **Comparing providers** — price the same prompt across models before choosing one.
- **Streaming cost awareness** — track tokens as a response streams in.

## What it is not

- **No MCP transport ships.** `pytokencalc.TokenCalculator` now has real handlers (token
  counts from the tokenizer registry, costs from the pricing table), but
  `start_mcp_connector()` raises `NotImplementedError` because PyTokenCalc ships no MCP
  transport. Budget/usage tools are in-memory and process-scoped.
- **No committed benchmark result.** The performance numbers are informal local
  observations, not a checked-in benchmark; there is no results file backing a specific
  claim. For OpenAI models PyTokenCalc *is* `tiktoken` under the hood, with a roughly
  2–5% wrapper overhead, not a speedup.
- **Lint/type coverage is partial.** `ruff check` runs in CI, but `black` formatting and
  `mypy` typing are configured yet not enforced (separate passes).
- **Anthropic/Google/Cohere counting makes a live network call** to the provider's API, so
  those paths need the relevant package installed and an API key set.
- **Provider coverage is a maintained table, not exhaustive.** See
  [`docs/MODELS.md`](docs/MODELS.md) for exactly which models are covered.

## Project status

**Beta.** Current version **1.3.0** (`Development Status :: 5 - Production/Stable` in
`pyproject.toml`). The local OpenAI/HuggingFace counting path is well covered by tests;
provider-specific paths require their optional dependencies. See
[`ROADMAP_HONEST.md`](ROADMAP_HONEST.md) for the full honest status and technical-debt
list.

## Installation

```bash
pip install pytokencalc
# or with uv
uv pip install pytokencalc

# with local tokenizer support (tiktoken + HuggingFace transformers)
pip install "pytokencalc[tokenizers]"
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
- [Honest status & roadmap](ROADMAP_HONEST.md) — what's tested, what isn't, known bugs, and technical debt

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

- [PyStreamXL](https://github.com/Mullassery/PyStreamXL) — stream large Excel workbooks with constant memory
- [PyStreamPDF](https://github.com/Mullassery/PyStreamPDF) — token-efficient PDF extraction for RAG
- [PyStreamMCP](https://github.com/Mullassery/PyStreamMCP) — context and token optimization for AI agents
- [PyStreamAI](https://github.com/Mullassery/PyStreamAI) — ML deployment toolkit (canary/A-B, cost tracking, ONNX)
- [PyTokenCalc](https://github.com/Mullassery/PyTokenCalc) — LLM token counting and cost estimation
- [Browse all projects](https://github.com/Mullassery?tab=repositories)

## License

This project is licensed under the [Apache License 2.0](LICENSE).
