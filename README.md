# PyTokenCalc

> **Universal token counting for any LLM.** 20+ providers, local inference engines, custom models. Pattern-based forward-compatibility with 99%+ accuracy.

![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Tests](https://img.shields.io/badge/Tests-157%20Passing-brightgreen.svg)
![Distribution](https://img.shields.io/badge/Distribution-Wheels--Only-blue.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

---

## Product Overview

**PyTokenCalc** is a proprietary, production-grade token counting library. Accurate tokenization across 20+ LLM providers with embedded quality validation.

### Why Teams Choose This

**The Problem**:
- Token counting varies across providers
- New model versions break existing counters
- No unified API for multi-provider systems
- Quality of tokenization is unverified

**The Solution**:
- 20+ providers in single API
- Local inference engines (no API calls)
- Pattern-based forward-compatibility
- Embedded StatGuardian quality validation
- 99%+ accuracy

**Result**: Unified token accounting, forward-compatible, trustworthy.

---

## Installation

```bash
pip install pytokencalc
# or with uv
uv pip install pytokencalc
```

### Requirements
- Python 3.10+
- Precompiled wheels

### Distribution Model

**Proprietary-first distribution**:
- ✅ Wheels-only via PyPI (no source code)
- ✅ Production-optimized token counting
- ✅ 157 comprehensive tests
- ✅ Embedded quality validation

---

## Quick Start

```python
from pytokencalc import TokenCounter

counter = TokenCounter()

# Count tokens for any provider
tokens = counter.count('claude-3-sonnet', text)
tokens = counter.count('gpt-4', text)
tokens = counter.count('llama-3', text)  # or custom

# Batch counting
texts = ['doc1', 'doc2', 'doc3']
token_counts = counter.count_batch('claude-3-sonnet', texts)

# Cost estimation
cost = counter.estimate_cost(
    provider='anthropic',
    model='claude-3-sonnet',
    input_tokens=1000,
    output_tokens=500,
)
print(f"Estimated cost: ${cost:.4f}")
```

---

## Features

- **20+ Providers**: Anthropic, OpenAI, Meta, Mistral, Google, and more
- **Local Inference**: No API calls required
- **Custom Models**: BYOM (Bring Your Own Model)
- **Pattern-Based Forward-Compatibility**: Works with new models
- **Quality Validation**: Embedded StatGuardian checks
- **Cost Estimation**: Automatic provider pricing
- **Production Ready**: 157 tests, high accuracy

---

## Supported Providers

- Anthropic (Claude)
- OpenAI (GPT)
- Meta (Llama)
- Google (Gemini)
- Mistral
- Cohere
- AWS Bedrock
- Azure OpenAI
- And 12+ more...

---

## Performance

- **Tokenization speed**: <1ms per 1000 tokens
- **Accuracy**: 99%+ vs official providers
- **Memory**: <10MB for all tokenizers

---

## Quality & Testing

- **157 tests** passing
- **Production-grade** — embedded quality validation
- **Accurate** — 99%+ match vs official providers

---

## Support

For production deployments: **mullassery@gmail.com**

---

**Version**: 1.0.1  
**License**: Proprietary  
**Distribution**: Wheels-only via PyPI  
**Python**: 3.10+  

Built for accurate, unified token accounting.
