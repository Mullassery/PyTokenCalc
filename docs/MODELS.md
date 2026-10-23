# Supported Models & Providers

## Built-in providers

| Provider | `provider` name | Runs offline? | Notes |
|---|---|---|---|
| OpenAI | `openai` | Yes | Local `tiktoken`, no API key or network needed |
| Azure OpenAI | `azure` | Yes | Same tokenizer as OpenAI (`tiktoken`) |
| HuggingFace | `huggingface` | Mostly | `transformers`; downloads tokenizer files from the HF Hub on first use per model, then runs fully locally |
| Open-source (`opensource`) | `opensource` | Mostly | Same as HuggingFace above -- any `org/model` HF repo ID |
| Anthropic Claude | `anthropic` | **No** | Calls the live Anthropic API (`messages.count_tokens`); needs `ANTHROPIC_API_KEY` |
| Google Gemini | `google` | **No** | Calls the live Google Generative AI API; needs an API key |
| Cohere | `cohere` | **No** | Calls the live Cohere `tokenize` API; needs `COHERE_API_KEY` |
| Ollama | `ollama` | Local network | Talks to a local Ollama daemon (default `http://localhost:11434`); not "offline" in the no-network sense, but doesn't leave your machine |

Only OpenAI/Azure (`tiktoken`) and, after the first download, HuggingFace/
open-source models run with zero network calls. Anthropic, Google, and
Cohere token counting is always a live API call.

## Model → provider auto-detection

`TokenCounterRegistry` auto-detects the provider from the model string
(see `pytokencalc/tokenizers/registry.py::_auto_detect_counter`):

- `gpt-4*`, `gpt-3.5*`, `gpt-5*`, `gpt-4.1*`, `gpt-4.5*`,
  `text-davinci-*`, `text-embedding-*`, and `o1*`/`o3*`/`o4*` → OpenAI
- `claude-*` → Anthropic
- `gemini-*` → Google
- `command*` → Cohere
- `gpt-35*`, or an Azure-qualified GPT/o-series name → Azure OpenAI
- provider-prefixed IDs such as `openai/o3-mini` are handled by inspecting the
  final path segment
- `ollama*`, `llama2`, `neural-chat`, `dolphin`, `openchat`, `openhermes`,
  `wizardlm` → Ollama (if reachable)
- `deepseek*`, `falcon*`, `text-bison`, `code-bison`, `llama*`, `mistral*`,
  `qwen*`, `mixtral*`, or anything else unmatched → open-source
  (HuggingFace-backed) fallback

You can always override auto-detection with an explicit `provider=` argument.

For anything not on this list -- a brand-new model, a fine-tuned/proprietary
model, a custom serving endpoint -- see `ModelDiscovery` (pattern-based
suggestions) and `CustomProviderCounter` (register your own endpoint) in
[API.md](API.md) and [CUSTOM_PROVIDERS.md](../CUSTOM_PROVIDERS.md).

## Catalog metadata

`get_model_spec()` and `list_models()` expose a reviewed metadata snapshot
including context window, max output, tokenizer family, modalities, aliases,
and optional provider endpoints:

```python
from pytokencalc import get_model_spec, list_models

spec = get_model_spec("openai/gpt-4o")
print(spec.context_length, spec.max_output_tokens, spec.input_modalities)

for model in list_models("anthropic"):
    print(model.id, model.context_length)
```

The catalog does not add pricing by itself. Use `load_pricing_override()` for
private/new prices, or import a downloaded OpenRouter `/api/v1/models` snapshot
with `import_openrouter_catalog_file()`.

## Cost estimation coverage

`estimate_cost()` (see [API.md](API.md)) is backed by a static pricing
table in [`pytokencalc/pricing.py`](../pytokencalc/pricing.py), currently
covering:

- **OpenAI:** gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-4-32k, gpt-3.5-turbo, text-davinci-003/002
- **Azure OpenAI:** gpt-35-turbo (+ the shared OpenAI entries above)
- **Anthropic:** claude-3-opus, claude-3-5-sonnet, claude-3-sonnet, claude-3-5-haiku, claude-3-haiku
- **Google:** gemini-1.5-pro, gemini-1.5-flash, gemini-2-flash, gemini-pro
- **Cohere:** command-r-plus, command-r, command-light, command

Model names with date/snapshot suffixes (e.g. `gpt-4o-2024-11-20`) resolve
to their base model. Genuinely different variants (e.g. `gpt-4.1` or
`gemini-1.5-flash-8b`) intentionally do **not** inherit a base model's price.
Pricing is a manually maintained snapshot -- see the module docstring for the
last-updated date and provider pricing-page links, and verify current rates
before relying on this for billing-critical decisions.
