# PyTokenCalc

**Know your LLM costs before you hit send.**

Stop guessing tokens. PyTokenCalc counts tokens across OpenAI, Anthropic,
Google, Cohere, Azure-hosted OpenAI models, HuggingFace/open-source models, Ollama, and
custom endpoints, then estimates the dollar cost of a request from a
maintained per-model pricing table.

[![PyPI](https://img.shields.io/pypi/v/pytokencalc)](https://pypi.org/project/pytokencalc)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![CI](https://github.com/Mullassery/PyTokenCalc/actions/workflows/ci.yml/badge.svg)](https://github.com/Mullassery/PyTokenCalc/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

---

## 30-Second Start

```python
from pytokencalc import count_tokens, estimate_cost

# Count tokens instantly (runs locally via tiktoken -- no API key needed)
tokens = count_tokens("Tell me a story about a robot", model="gpt-4o")
print(f"Tokens: {tokens}")

# Estimate cost from the pricing table
cost = estimate_cost("gpt-4o", input_tokens=tokens)
print(f"Cost: ${cost:.6f}")
```

---

## Why PyTokenCalc?

**The Problem:**
- LLM costs are unpredictable (different models, different tokenizers)
- Manual calculation is error-prone
- No way to estimate before sending requests
- Each provider has different pricing

**The Solution:**
- One API across cloud, local, and custom providers
- Token counting that matches each provider's own tokenizer
- Real cost estimation from a maintained pricing table (see
  [docs/MODELS.md](docs/MODELS.md) for exactly which models are covered)

---

## Key Features

- **Multi-provider:** OpenAI, Anthropic Claude, Google Gemini, Cohere,
  Azure-hosted OpenAI models, HuggingFace/open-source models, Ollama, and
  any custom HTTP endpoint you register
- **Accurate tokenization:** uses each provider's own tokenizer/API
  (`tiktoken` for OpenAI and Azure-hosted OpenAI models, the HuggingFace
  `transformers` tokenizer, the live count-tokens endpoint for
  Anthropic/Google/Cohere)
- **Real cost estimation:** `estimate_cost()` is backed by a per-model USD
  pricing table (input vs. output rates), not a guess -- see
  [pytokencalc/pricing.py](pytokencalc/pricing.py) for sources and the
  last-updated date
- **Fast local counting:** sub-millisecond in our testing for the local
  (tiktoken/HuggingFace) providers on typical hardware -- see
  [Performance](#performance) below
- **Batch processing:** count tokens for many prompts in one call
- **Custom / BYOM models:** register your own provider or fine-tuned model
  (see [CUSTOM_PROVIDERS.md](CUSTOM_PROVIDERS.md))
- **Streaming/incremental counting:** `counter.streaming(model)` gives you a
  running token count as chunks of a live LLM response arrive, correct
  across chunk/BPE-merge boundaries (not a naive per-chunk sum)
- **Encoding drift detection:** OpenAI's tiktoken encoding resolution now
  prefers `tiktoken.encoding_for_model()` (stays current with tiktoken
  upgrades) and flags in `get_tokenizer_info()["drift_warnings"]` if an
  installed encoding's actual tokenization behavior has changed since this
  library was last verified against it

---

## Real-World Use Cases

*The examples below use Claude/GPT-4 interchangeably for illustration.
Anthropic/Google/Cohere models require the relevant package installed and
an API key set (see [docs/MODELS.md](docs/MODELS.md)); OpenAI/GPT-4 models
work offline out of the box.*

**Budget Tracking:**
```python
from pytokencalc import count_tokens, estimate_cost

prompt = "Hello"
reply_tokens_estimate = 50  # however you estimate expected output length

input_tokens = count_tokens(prompt, model="claude-3-opus")
cost = estimate_cost("claude-3-opus", input_tokens, reply_tokens_estimate)
print(f"Estimated cost: ${cost:.4f}")
```

**Prevent Overruns:**
```python
tokens = count_tokens(prompt, model="gpt-4")
if estimate_cost("gpt-4", tokens) > 0.10:
    print("Request too expensive, rejected")
```

**Compare Providers:**
```python
prompt = "Explain quantum computing in one paragraph."
for model in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]:
    tokens = count_tokens(prompt, model=model)
    cost = estimate_cost(model, tokens)
    print(f"{model}: {tokens} tokens, ${cost:.6f}")
```

---

## Performance

Local (tiktoken/HuggingFace-backed) counting is fast -- in informal local
benchmarking, a single uncached `count_tokens()` call against `gpt-4o` on a
few dozen words took well under 1ms. PyTokenCalc itself is pure Python; the
speed comes from `tiktoken` (OpenAI and Azure-hosted OpenAI models) and the HuggingFace `tokenizers`
library, both of which have compiled (Rust) cores under their Python
bindings. There is no compiled/Rust code in PyTokenCalc itself. Anthropic,
Google, and Cohere counting makes a live network call to the provider's
API, so latency there is dominated by that round trip (with response
caching to avoid repeat calls for identical input).

### vs tiktoken, on real text

For OpenAI models, PyTokenCalc *is* `tiktoken` under the hood (see
[`openai_counter.py`](pytokencalc/tokenizers/openai_counter.py)), so this
isn't a "which tokenizer is right" contest -- it's a correctness check on
the wrapper (does it ever diverge from the ground truth it wraps?) plus an
honest measurement of the wrapper's own overhead.

**Correctness**, `gpt-4o` (`o200k_base`) and `gpt-4` (`cl100k_base`), against
real, live-fetched text -- four real READMEs/articles (Flask's, Requests',
PyTorch's, and the full English Wikipedia "Artificial intelligence" article,
121KB combined) plus six adversarial edge cases (empty string, emoji,
Japanese, Chinese, mixed code+CJK, a 22.5KB repeated-phrase block):

| | tiktoken (ground truth) | PyTokenCalc |
|---|---|---|
| Real-corpus exact matches | 8/8 | 8/8 |
| Edge-case exact matches | 6/6 | 6/6 |
| **Total exact match rate** | -- | **14/14 (100%)** |

**Speed**, warm (both encoders pre-loaded), 200 *interleaved* iterations
(alternating tiktoken/PyTokenCalc calls each iteration so both see the same
system-load noise -- this machine had other background jobs running during
measurement, and non-interleaved back-to-back blocks swung between "PyTokenCalc
faster" and "tiktoken faster" run to run purely from load drift) over a
22.5KB block: tiktoken **~1.3-1.8ms** median/call, PyTokenCalc
**~1.4-1.9ms** median/call across repeated runs -- consistently a
**small (roughly 2-5%) wrapper overhead**, not a speedup. That's the
honest number; don't trust any single non-interleaved timing on a loaded
machine, including earlier drafts of this benchmark.

**Where PyTokenCalc adds real value tiktoken alone doesn't provide** --
verified, not just claimed: its `StreamingTokenCounter` (for counting
tokens as an LLM response streams in) recomputes against the full
accumulated text on each chunk rather than naively summing per-chunk
counts in isolation. On a real 148-character string chopped into 3-byte
SSE-style chunks (englishtext + 日本語 + an emoji, deliberately split
mid-token), the correct whole-text count is 30 tokens; PyTokenCalc's
streaming counter matches it exactly (30), while the naive
sum-each-chunk-separately approach it explicitly guards against would have
overcounted by **34 tokens (more than double)** -- a real, reproducible BPE
chunk-boundary error PyTokenCalc avoids and raw per-chunk `tiktoken` calls
would not.

Reproduce: [`docs/bench/tiktoken_comparison.py`](docs/bench/tiktoken_comparison.py)
fetches the same live sources and re-runs all of the above.

---

## Installation

```bash
pip install pytokencalc
# or with uv
uv pip install pytokencalc

# with local tokenizer support (tiktoken + HuggingFace transformers)
pip install "pytokencalc[tokenizers]"
```

Requires Python 3.9+.

---

## Documentation

- [API Reference](docs/API.md) — top-level functions, the full registry API, CLI, and REST server
- [Supported Models](docs/MODELS.md) — provider list, offline vs. API-backed, pricing table coverage
- [Custom Providers](CUSTOM_PROVIDERS.md) — register your own endpoint or BYOM
- [CLI Quick Start](QUICK_START_CLI.md) — the `pycount` terminal command (installed automatically with the package)
- [Architecture](docs/ARCHITECTURE.md) — component overview, request flow, and honest architectural gaps
- [Examples](examples/) — runnable code samples
- [Honest status & roadmap](ROADMAP_HONEST.md) — what's tested, what isn't, known bugs, and technical debt

---

## Known issues

- ~~A network failure while loading tiktoken's OpenAI encodings can take down the entire token-counter registry~~ **Fixed**: `TokenCounterRegistry._register_default_counters` (`pytokencalc/tokenizers/registry.py`) now catches `Exception` broadly around each individual provider's construction, not just `ImportError`, so a failure in one provider (e.g. `OpenAITokenCounter.__init__` raising `RuntimeError` on a failed tiktoken download) only skips that provider — Anthropic/Google/Cohere/HuggingFace/Ollama/custom-provider counting are unaffected. See `tests/test_registry_resilience.py` for the regression test.
- ~~**No timeout on HuggingFace tokenizer downloads**~~ **Fixed**: `count_tokens(text, model=<huggingface-or-fallback model>)` now bounds every `AutoTokenizer.from_pretrained()` call via `pytokencalc/tokenizers/_timeout.py` (`call_with_timeout`, thread-based). Default ceiling is 30s, overridable per counter (`load_timeout=` kwarg) or via the `PYTOKENCALC_HF_TIMEOUT` env var; on timeout it raises a `RuntimeError` instead of blocking for the full OS-level connect timeout. Covered by `tests/test_timeout.py`.
- The MCP tool surface exported as `pytokencalc.TokenCalculator` was a fake stub (hardcoded token counts/rates) and shelled out to an external `dab` binary. **Rebuilt in this pass**: every handler is now real — token counts come from the actual tokenizer registry, costs come from the static pricing table — and is covered by `tests/test_mcp_tools.py` (23 tests). It does **not** start a server: `start_mcp_connector()` raises `NotImplementedError` because PyTokenCalc ships no MCP transport (the `dab` path was removed). Budget/usage tools are in-memory and process-scoped.
- ~~`pytokencalc.estimate_cost()` / `pytokencalc.pricing.PRICING_TABLE` has no dedicated test file~~ **Fixed**: covered by `tests/test_pricing_and_api.py` (pricing table, prefix/case resolution, cost math, error paths, and the top-level `count_tokens`/`estimate_cost` API).
- ~~Lint (`ruff`/`black`/`mypy`) is configured but not run in CI; `ruff check pytokencalc/` reports 299 findings~~ **Fixed**: `pyproject.toml` now has an explicit curated `[tool.ruff.lint] select` (`E,F,W,I,B,C4,PIE,SIM`; `E501` ignored, owned by black) and `.github/workflows/ci.yml` gained a `lint` job running `ruff check .`, which is clean. `black`/`mypy` are still not enforced (separate formatting/typing pass).
- The "Performance" numbers above are informal, uncommitted local observations, not a checked-in benchmark result — there is no benchmark script or results file in this repo backing a specific number as fact.
- No open GitHub issues and no `TODO`/`FIXME` markers in `pytokencalc/` at the time of this writing.

See [ROADMAP_HONEST.md](ROADMAP_HONEST.md) for the full technical-debt list, including exactly what has and hasn't been tested.

## License

This project is licensed under the [Apache License 2.0](LICENSE).

---

**PyTokenCalc v1.2.1** | Python 3.9+
