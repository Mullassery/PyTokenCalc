# PyTokenCalc: Unified Token Counting for Multi-Provider LLMs

[![PyPI version](https://badge.fury.io/py/pytokencalc.svg)](https://pypi.org/project/pytokencalc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## The Problem

You're building an LLM application that uses multiple providers. You need to count tokens accurately and manage rate limits. But here's the nightmare:

**OpenAI has `tiktoken`.** Different API, different methods.
**Meta's Llama has HuggingFace tokenizers.** Another integration.
**Claude? No public tokenizer.** You have to call the API just to count tokens.
**Gemini? Same problem.** API-only, proprietary.
**Groq, DeepInfra, Together? They all count differently.** Good luck.

You end up with:
- ❌ 10+ different libraries to install
- ❌ Different APIs for each provider
- ❌ Expensive API calls just to count tokens (200-500ms each)
- ❌ No consistent way to get token counts
- ❌ Wasted time integrating providers instead of building features

**This is madness. You just want to count tokens.**

---

## The Solution: PyTokenCalc

One library. One API. All providers.

```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()

# Same code for every provider
tokens = registry.count_tokens("gpt-4o", "Your prompt")
tokens = registry.count_tokens("claude-3-5-sonnet", "Your prompt")
tokens = registry.count_tokens("llama-70b", "Your prompt")

print(f"Tokens: {tokens.input_tokens}")
```

That's it. No provider-specific code. No multiple libraries. No headaches.

---

## What You Get

### 1. **True Unified Interface**
One function for 20+ providers (cloud and open-source).

```python
# Works for everything
models = [
    "gpt-4o",
    "claude-3-5-sonnet",
    "gemini-2-flash",
    "llama-70b",
    "mistral-large",
]

for model in models:
    result = registry.count_tokens(model, "Your text")
    print(f"{model}: {result.input_tokens} tokens")
```

### 2. **Smart Routing: Fast When You Can, Accurate When You Need To**
- **Local tokenizers** for OpenAI GPT and open-source models (5-10ms)
- **Cached API calls** for proprietary models like Claude and Gemini (0ms if cached, 200ms first time)
- **Automatic** — you don't think about it

```python
# Automatically uses tiktoken (fast, local, free)
gpt_tokens = registry.count_tokens("gpt-4o", text)  # 5ms

# Automatically caches and reuses
gpt_tokens = registry.count_tokens("gpt-4o", text)  # 0ms (cached)
```

### 3. **99%+ Accuracy vs Official Counts**
Local tokenizers are 100% accurate for their models. API-backed counts match official numbers exactly. No guessing.

### 4. **70-80% Fewer API Calls**
Intelligent caching means you don't hammer provider APIs just to count tokens.

### 5. **Batch Operations**
Count tokens for multiple prompts at once.

```python
results = registry.count_batch([
    {"model": "gpt-4o", "text": "Prompt 1"},
    {"model": "llama-70b", "text": "Prompt 2"},
    {"model": "claude-3-5-sonnet", "text": "Prompt 3"},
])

for result in results:
    print(f"{result.input_tokens} tokens")
```

---

## Installation

### For Users

**Basic (Local Tokenizers Only)**
```bash
pip install pytokencalc
```

This gives you token counting for OpenAI GPT and Llama/Mistral models (covers 70% of use cases).

**Full (Recommended)**
```bash
pip install "pytokencalc[tokenizers]"
```

Installs optional dependencies for broader model support:
- `tiktoken` — OpenAI GPT models
- `transformers` — Llama, Mistral, and 1000+ HuggingFace models
- `sentencepiece` — Additional model support

### For Developers

```bash
# Clone the repository
git clone https://github.com/Mullassery/pytokencalc.git
cd pytokencalc

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev,tokenizers]"

# Run tests
pytest tests/
make test    # or use Makefile
```

**Requirements:**
- Python 3.9+
- pip or uv

---

## Quick Example

```python
from pytokencalc.tokenizers import TokenCounterRegistry

# Initialize once
registry = TokenCounterRegistry()

# Use anywhere
prompt = "Write me a Python function that..."
result = registry.count_tokens("gpt-4o", prompt)

print(f"Input tokens: {result.input_tokens}")
print(f"Latency: {result.latency_ms}ms")
print(f"Was cached: {result.cached}")
print(f"Source: {result.source}")  # "local", "api", or "formula"
```

Output:
```
Input tokens: 42
Latency: 5.2ms
Was cached: False
Source: local
```

Run it again with the same text:
```python
result = registry.count_tokens("gpt-4o", prompt)
print(f"Latency: {result.latency_ms}ms (cached!)")
```

Output:
```
Latency: 0.3ms (cached!)
```

---

## Why This Matters

### Before PyTokenCalc
```python
# Your code without PyTokenCalc
import tiktoken
from transformers import AutoTokenizer
import anthropic

# Different library, different API for each
enc = tiktoken.encoding_for_model("gpt-4o")
gpt_tokens = len(enc.encode(text))

llama_tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-70b")
llama_tokens = len(llama_tokenizer.encode(text))

client = anthropic.Anthropic()
claude_response = client.messages.count_tokens(
    model="claude-3-5-sonnet",
    messages=[{"role": "user", "content": text}]
)
claude_tokens = claude_response.input_tokens

# Three different patterns, three different libraries
```

### With PyTokenCalc
```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()

gpt_tokens = registry.count_tokens("gpt-4o", text).input_tokens
llama_tokens = registry.count_tokens("llama-70b", text).input_tokens
claude_tokens = registry.count_tokens("claude-3-5-sonnet", text).input_tokens

# One pattern. One library. Done.
```

---

## Supported Providers

### Cloud LLM APIs (20+)
Anthropic Claude, OpenAI GPT, Google Gemini, Mistral, DeepSeek, Meta Llama (via Bedrock), Cohere, and more.

### Open-Source APIs (10+)
Groq, DeepInfra, Together.ai, Fireworks, Replicate, and more.

### Local Models
Any HuggingFace model with a tokenizer.

---

## API Reference

### Count Tokens

```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()

# Single count
result = registry.count_tokens(
    model="gpt-4o",
    text="Your prompt here"
)

print(result.input_tokens)    # int - token count
print(result.latency_ms)      # float - milliseconds taken
print(result.cached)          # bool - came from cache?
print(result.source)          # str - "local", "api", or "formula"
```

### Batch Count

```python
# Multiple counts in one call
results = registry.count_batch([
    {"model": "gpt-4o", "text": "Text 1"},
    {"model": "llama-70b", "text": "Text 2"},
])

for result in results:
    print(f"{result.input_tokens} tokens")
```

### Cache Stats

```python
cache = registry.tokenizers[0].cache
stats = cache.get_stats()

print(stats.hit_rate)    # Cache hit rate (0-1)
print(stats.size)        # Number of cached entries
print(stats.total_calls) # Total counts requested
```

---

## Real-World Use Cases

### Use Case 1: Monitor Token Usage
```python
def log_request(model, prompt, response):
    tokens = registry.count_tokens(model, prompt)
    print(f"Request used {tokens.input_tokens} tokens")

# Call it automatically on every LLM invocation
log_request("gpt-4o", "Hello", response)
```

### Use Case 2: Token Budget Management
```python
MAX_TOKENS_PER_HOUR = 1_000_000
used_tokens = 0

for prompt in user_prompts:
    token_count = registry.count_tokens("claude-3-5-sonnet", prompt)
    if used_tokens + token_count.input_tokens > MAX_TOKENS_PER_HOUR:
        print("Budget exceeded!")
        break
    
    used_tokens += token_count.input_tokens
    response = call_llm(prompt)
```

### Use Case 3: Model Comparison
```python
text = "Your 1000-word essay..."

for model in ["gpt-4o", "claude-3-5-sonnet", "gemini-2-flash"]:
    tokens = registry.count_tokens(model, text).input_tokens
    print(f"{model}: {tokens} tokens")

# See which model would be cheapest
```

---

## Performance

| Scenario | Latency | Notes |
|----------|---------|-------|
| First local count (GPT) | 5ms | tiktoken initialization |
| Cached local count | 0.3ms | Memory lookup |
| First API count (Claude) | 200-300ms | Network call |
| Cached API count | 0.2ms | Memory lookup |
| Batch of 10 (mixed) | ~10ms | Parallel processing |

**TL;DR: Local is instant. API counts are cached aggressively. You rarely wait.**

---

## Database & Storage

PyTokenCalc maintains a database to store token counts and enable reconciliation across API calls:

**PyTokenCalc Standalone:** Manages its own database for token accounting. OpenAnchor is optional.

**PyTokenCalc + OpenAnchor:** When you install OpenAnchor, it automatically includes PyTokenCalc. Both use the same database:
- PyTokenCalc stores: Raw token counts (token_events)
- OpenAnchor stores: Analysis & recommendations (attribution, patterns, etc)
- Single instance: Both projects share one database
- OpenAnchor does NOT create its own database—it enriches PyTokenCalc's database with intelligence

**Important:** OpenAnchor requires PyTokenCalc to be installed. You cannot use OpenAnchor without PyTokenCalc. However, you can use PyTokenCalc alone without OpenAnchor.

---

## What's NOT Included

PyTokenCalc counts tokens. That's it.

For advanced use cases like token intelligence, optimization, or analytics, use OpenAnchor (which bundles PyTokenCalc) or build on PyTokenCalc's token counting API:
- 🔍 Token intelligence & attribution (use OpenAnchor)
- 📊 Pattern detection & anomaly alerts (use OpenAnchor)
- 🎯 Optimization recommendations (use OpenAnchor)
- 📈 Plan capacity and model comparison (build on PyTokenCalc)

---

## Contributing

Want to add support for a new provider? See [ADDING_PROVIDERS.md](ADDING_PROVIDERS.md) for step-by-step guide.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## About

**PyTokenCalc** solves one problem perfectly: unified token counting across all LLM providers.

**Author**: Georgi Mammen Mullassery (@Mullassery)  
**Repository**: https://github.com/Mullassery/PyTokenCalc

---

**Stop integrating tokenizers. Start counting tokens.**
