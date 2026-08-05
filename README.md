# PyTokenCalc

**Know your LLM costs before you hit send.**

Stop guessing tokens. PyTokenCalc counts tokens from 20+ LLM providers (Claude, GPT-4, Gemini, Llama, Mistral, and more) with 99.9% accuracy in a single function call. Estimate costs, track usage, optimize spending—no setup required.

[![PyPI](https://img.shields.io/pypi/v/pytokencalc)](https://pypi.org/project/pytokencalc)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![Tests Passing](https://img.shields.io/badge/tests-passing-success)](./tests)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](./LICENSE)

---

## 30-Second Start

```python
from pytokencalc import count_tokens, estimate_cost

# Count tokens instantly
tokens = count_tokens("Claude", "Tell me a story")
print(f"Tokens: {tokens}")  # 5

# Estimate cost
cost = estimate_cost("gpt-4", tokens, input_only=True)
print(f"Cost: ${cost:.4f}")  # $0.0015
```

---

## Why PyTokenCalc?

**The Problem:**
- LLM costs are unpredictable (different models, different tokenizers)
- Manual calculation is error-prone
- No way to estimate before sending requests
- Each provider has different pricing

**The Solution:**
- Unified API for all LLM providers
- Accurate token counting for 20+ models
- Real-time cost estimation
- Works offline (no API calls needed)

---

## Key Features

- **20+ Providers:** Claude, GPT-4, Gemini, Llama 2, Mistral, Cohere, PaLM, and more
- **Accurate Tokenization:** Matches official provider tokenizers (99.9% accuracy)
- **Fast:** <1ms per count (precompiled Rust core)
- **No Dependencies:** Works standalone, no external APIs
- **Cost Estimation:** Input-only, output, or full conversation costs
- **Batch Processing:** Count tokens for entire conversations at once
- **Custom Models:** Define your own tokenizer patterns

---

## Real-World Use Cases

**Budget Tracking:**
```python
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
]
total_cost = estimate_cost("claude-3-opus", messages)
print(f"Conversation will cost: ${total_cost}")
```

**Prevent Overruns:**
```python
# Reject requests that cost too much
if estimate_cost("gpt-4", prompt) > 0.10:
    print("Request too expensive, rejected")
```

**Compare Providers:**
```python
for model in ["claude-3-opus", "gpt-4", "gemini-pro"]:
    cost = estimate_cost(model, prompt)
    print(f"{model}: ${cost:.4f}")
```

---

## Performance

| Operation | Time |
|-----------|------|
| Count tokens (100 words) | <1ms |
| Estimate cost | <1ms |
| Batch process (1000 messages) | <100ms |

---

## Installation

```bash
pip install pytokencalc
# or with uv
uv pip install pytokencalc
```

---

## Documentation

- [API Reference](docs/API.md) — All counting and cost functions
- [Supported Models](docs/MODELS.md) — Complete provider list
- [Examples](examples/) — Real-world code samples

---

## License

Proprietary License - Free to use with explicit attribution. See [LICENSE](LICENSE).

---

**PyTokenCalc v2.0.0** | Wheels-only distribution | Python 3.10+
