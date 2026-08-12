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

- `gpt-4*`, `gpt-3.5*`, `text-davinci-*`, `text-embedding-*` → OpenAI
- `claude-*` → Anthropic
- `gemini-*` → Google
- `command*` → Cohere
- `gpt-35*`, or `gpt-4*` combined with "azure" in the name → Azure OpenAI
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

## Cost estimation coverage

`estimate_cost()` (see [API.md](API.md)) is backed by a static pricing
table in [`pytokencalc/pricing.py`](../pytokencalc/pricing.py), currently
covering:

- **OpenAI:** gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-4-32k, gpt-3.5-turbo, text-davinci-003/002
- **Azure OpenAI:** gpt-35-turbo (+ the shared OpenAI entries above)
- **Anthropic:** claude-3-opus, claude-3-5-sonnet, claude-3-sonnet, claude-3-5-haiku, claude-3-haiku
- **Google:** gemini-1.5-pro, gemini-1.5-flash, gemini-2-flash, gemini-pro
- **Cohere:** command-r-plus, command-r, command-light, command

Model names with date suffixes (e.g. `gpt-4o-2024-11-20`) resolve via
longest-prefix match. Pricing is a manually maintained snapshot -- see the
module docstring for the last-updated date and provider pricing-page links,
and verify current rates before relying on this for billing-critical
decisions.
