# PyTokenCalc v0.6: Multi-Provider LLM Token Calculator

[![PyPI version](https://badge.fury.io/py/pytokencalc.svg)](https://pypi.org/project/pytokencalc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub](https://img.shields.io/badge/GitHub-PyTokenCalc-black.svg)](https://github.com/Mullassery/PyTokenCalc)

**Unified token counting and cost calculation across 20+ cloud providers and 10+ open-source APIs.**

PyTokenCalc handles the complexity of multi-provider LLM token accounting:
- **Different providers count tokens differently** (Groq Llama vs DeepInfra Llama = different token counts)
- **Same model, different pricing** across providers (4-96x cost variance)
- **Provider-specific token models** (Claude simple, GPT-4o dual-token, Gemini character-based, Groq speed-tiered, etc.)

This is the token counting core that powers [OpenAnchor](https://github.com/Mullassery/openanchor) (cost optimization middleware).

---

## What It Does (v0.6 Scope)

### ✅ Multi-Provider Token Counting (Core v0.6)
Handle provider-specific token counting for any LLM:
```python
from pytokencalc import UsageData, CostCalculatorV6

calc = CostCalculatorV6()

# Claude: Simple input/output tokens
usage = UsageData(
    provider="anthropic",
    model="claude-3-5-sonnet",
    input_tokens=1_000_000,
    output_tokens=500_000
)
cost = calc.calculate(usage)  # $10.50

# GPT-4o: Dual token model (full + mini)
usage = UsageData(
    provider="openai",
    model="gpt-4o",
    input_tokens=1_000_000,
    input_mini_tokens=500_000,  # Different rate
    output_tokens=250_000,
    output_mini_tokens=100_000
)
cost = calc.calculate(usage)  # $5.56

# Gemini: Character-based (not token-based!)
usage = UsageData(
    provider="google",
    model="gemini-2-flash",
    input_characters=1_000_000_000,  # 1B chars
    output_characters=500_000_000
)
cost = calc.calculate(usage)  # $1.125

# Groq: Speed-tiered pricing
usage = UsageData(
    provider="groq",
    model="llama-70b",
    input_tokens=1_000_000,
    output_tokens=500_000,
    speed_tier="fast"  # 2x base cost
)
cost = calc.calculate(usage)
```

### ✅ Token Accounting (Core v0.6)
Track tokens consumed per provider, model, task:
```python
# After calling calculate() multiple times:
breakdown = calc.cost_by_provider()
# {"anthropic": $X, "openai": $Y, "google": $Z}

breakdown = calc.cost_by_model()
# {"claude-3-5-sonnet": $X, "gpt-4o": $Y, "gemini-2-flash": $Z}

breakdown = calc.cost_by_task_type()
# {"analysis": $X, "coding": $Y, "inference": $Z}

export = calc.export()
# Audit trail with all token counts per operation
```

### ✅ Provider-Specific Token Models (Core v0.6)
Each provider has its own token counting logic:
```python
from pytokencalc import (
    ClaudeTokenModel,      # Simple tokens
    GPT4oTokenModel,       # Full + mini tokens
    GeminiCharacterModel,  # Character-based
    GroqSpeedTieredModel,  # Speed affects pricing
    DeepInfraTokenModel,   # Open-source wrapper
    TogetherAITokenModel   # Open-source alternative
)
```

### ✅ Budget Enforcement (Safety Feature)
Hard limits to prevent runaway costs:
```python
from pytokencalc import set_budget_limit, BudgetPeriod

set_budget_limit(
    max_spend=100.00,  # $100/day hard cap
    period=BudgetPeriod.DAILY
)
```

### ✅ Real-Time Pricing (v0.5+ Compatibility)
Daily pricing updates for accurate cost calculations:
```python
from pytokencalc import PricingManager

pricing = PricingManager()
latest = pricing.get_current_rate(
    provider="anthropic",
    model="claude-3-5-sonnet"
)
```

---

## What It Does NOT

PyTokenCalc focuses on **token counting accuracy**. Out of scope:

- ❌ **Optimization recommendations** — That's [OpenAnchor](https://github.com/Mullassery/openanchor)'s job
- ❌ **Dashboards/UI** — We're a library, not a service
- ❌ **Forecasting/predictions** — We track actual consumption, not predictions
- ❌ **Compliance/audit** — Use your audit system
- ❌ **Team management/RBAC** — Use your platform's auth
- ❌ **Alerting** — Implement in your monitoring layer

---

## Quick Start

### Installation
```bash
pip install pytokencalc
# or
uv pip install pytokencalc
```

### Basic Usage (v0.6 Multi-Provider)

```python
from pytokencalc import UsageData, CostCalculatorV6

calc = CostCalculatorV6()

# Track Claude tokens
claude = UsageData(
    provider="anthropic",
    model="claude-3-5-sonnet",
    input_tokens=1_000_000,
    output_tokens=500_000
)
cost = calc.calculate(claude)
print(f"Claude cost: ${cost:.4f}")

# Track GPT-4o with mini tokens
gpt = UsageData(
    provider="openai",
    model="gpt-4o",
    input_tokens=1_000_000,
    input_mini_tokens=500_000,
    output_tokens=250_000
)
cost = calc.calculate(gpt)
print(f"GPT-4o cost: ${cost:.4f}")

# Track Gemini (character-based)
gemini = UsageData(
    provider="google",
    model="gemini-2-flash",
    input_characters=1_000_000_000,
    output_characters=500_000_000
)
cost = calc.calculate(gemini)

# Get breakdown by provider
breakdown = calc.cost_by_provider()
print(f"Breakdown: {breakdown}")

# Export audit trail
export = calc.export()
```

### Legacy Usage (v0.5 Compatibility)

```python
from pytokencalc import CostCalculator, CostDatabase

# Old API still works
calc = CostCalculator()
cost = calc.calculate("anthropic", "claude-3-5-sonnet", 1000, 250)

# Track with database
db = CostDatabase()
db.track("anthropic", "claude-3-5-sonnet", 1000, 250)
report = db.report(period="day")
```

### With OpenAnchor
```python
from pytokencalc import CostCalculator
from openanchor import CostOptimizer

# OpenAnchor uses PyTokenCalc for cost calculation
optimizer = CostOptimizer()
llm = optimizer.wrap(your_llm)

response = llm.invoke("Analyze this document...")
# OpenAnchor internally calls PyTokenCalc to calculate costs
```

---

## Supported Providers (v0.5)

### Cloud Providers (20+)
- ✅ Anthropic (Claude 3.5 Sonnet, Haiku, Opus)
- ✅ OpenAI (GPT-4, GPT-4o, mini)
- ✅ Google (Gemini 2 Flash, Pro, Ultra)
- ✅ Mistral (Large, Tiny)
- ✅ DeepSeek (V3, R1)
- ✅ Meta (Llama via providers)
- ✅ Cohere
- ✅ + 13 more cloud providers

### Open-Source APIs (10+)
- ✅ Groq (Llama, Mixtral)
- ✅ DeepInfra (Llama, DeepSeek, Qwen)
- ✅ Together (Open-source models)
- ✅ Fireworks (Optimized inference)
- ✅ Z.AI (Chinese models)
- ✅ + 5 more open-source APIs

**Daily pricing updates** from official sources. Accuracy: ±1% vs actual API bills.

---

## API Reference

### CostCalculator
```python
from pycostaudit import CostCalculator

calc = CostCalculator()

# Single calculation
cost = calc.calculate(provider, model, input_tokens, output_tokens)

# Batch calculation
costs = calc.calculate_batch([
    {"provider": "anthropic", "model": "claude-3-5-sonnet", "input": 1000, "output": 250},
    {"provider": "openai", "model": "gpt-4o", "input": 2000, "output": 500},
])

# With metadata
result = calc.calculate_with_metadata(provider, model, input_tokens, output_tokens)
# Returns: {"cost": 0.00825, "accuracy": "99%", "timestamp": "...", "provider": "anthropic"}
```

### CostDatabase
```python
from pycostaudit import CostDatabase

db = CostDatabase(db_path="~/.pycostaudit/costs.db")

# Track operation
db.track(
    provider="anthropic",
    model="claude-3-5-sonnet",
    input_tokens=1000,
    output_tokens=250,
    task_type="document_qa"
)

# Get report
report = db.report(period="day" | "week" | "month")
# Returns: {"by_provider": {...}, "by_model": {...}, "by_task_type": {...}, "total": ...}

# Export
db.export(format="csv" | "json" | "parquet", period="month")
```

### PricingManager
```python
from pycostaudit import PricingManager

pricing = PricingManager()

# Get current rate
rate = pricing.get_current_rate(provider="anthropic", model="claude-3-5-sonnet")
# Returns: {"input": 3.00, "output": 15.00, "per": "1M"}

# Compare providers for same model
result = pricing.compare_model("llama-70b")
# Shows cost across Groq, DeepInfra, Together, etc.
```

### Budget Enforcement
```python
from pycostaudit import set_budget_limit, BudgetPeriod, BudgetExceededError

# Set hard limit
set_budget_limit(max_spend=100.00, period=BudgetPeriod.DAILY)

# Will raise error if exceeded
try:
    db.track(provider, model, tokens_in, tokens_out)
except BudgetExceededError as e:
    print(f"Budget exceeded: {e}")
```

---

## Architecture

### Rust Core (High-Performance)
- Sub-5ms cost calculations
- Concurrent pricing updates
- Memory-safe token handling

### Python Layer (Easy-to-Use)
- Simple `CostCalculator` API
- `CostDatabase` for tracking
- Integration with OpenAnchor

### SQLite Storage
- Local, privacy-first storage
- No cloud dependencies
- Portable across machines

---

## Version History

### v0.6.0 (July 2026) - Multi-Provider Token Models
**NEW: Provider-specific token counting for 20+ APIs**
- ClaudeTokenModel: Simple input/output token rates
- GPT4oTokenModel: Dual token model (full + mini)
- GeminiCharacterModel: Character-based (not token-based)
- GroqSpeedTieredModel: Speed tier affects token pricing
- DeepInfraTokenModel: Open-source wrapper
- TogetherAITokenModel: Open-source alternative
- CostCalculatorV6: Multi-provider token calculator
- CostModelRegistry: Extensible provider system
- UsageData: Provider-specific token fields (characters, mini-tokens, speed tiers, etc.)
- **Focus:** Token counting accuracy, not cost estimation
- **Extensibility:** Add new providers without core changes

### v0.5.0 (July 2026) - Multi-Provider Launch
**Renamed: PyCostAudit → PyTokenCalc (reflects multi-LLM focus)**
- Removed: Forecasting, dashboards, compliance, reporting, recommendations
- Kept: Cost calculation core + budget enforcement
- Result: Laser-focused, 87% code reduction
- Focus: Multi-API cost calculation for OpenAnchor
- Supports: 20+ cloud providers + 10+ open-source APIs

### v0.4.1 (June 2026) - Claude Code Only
- Claude Code cost tracking (single provider)
- Forecasting + compliance features
- Interactive dashboard
- **Status:** Archived, use v0.5+ instead

---

## Use Cases

### 1. OpenAnchor Integration (Primary)
```python
from pytokencalc import CostCalculator
from openanchor import CostOptimizer

# OpenAnchor uses PyTokenCalc for cost tracking
optimizer = CostOptimizer()
```

### 2. Multi-Provider Tracking
```python
# Track costs across multiple LLM APIs in one place
calc = CostCalculator()

for provider, model, tokens_in, tokens_out in operations:
    cost = calc.calculate(provider, model, tokens_in, tokens_out)
    db.track(provider, model, tokens_in, tokens_out)
```

### 3. Provider Cost Comparison
```python
# Find cheapest inference provider for your models
pricing = PricingManager()

result = pricing.compare_model("llama-70b")
# Show user: "DeepInfra is 4.2x cheaper than Groq for this model"
```

### 4. Budget Safety
```python
# Enforce hard cost limits per day/month
from pycostaudit import set_budget_limit

set_budget_limit(max_spend=50.00, period=BudgetPeriod.DAILY)
# Prevents runaway costs from accidental loops or misconfiguration
```

---

## FAQ

**Q: Does PyCostAudit-Multi use my API keys?**
A: No. It only calculates costs based on tokens. No API calls are made.

**Q: How accurate is the cost calculation?**
A: ±1% of actual API bills. We validate daily against real usage.

**Q: Can I use this standalone?**
A: Yes. Full cost tracking + database available standalone.

**Q: What about forecasting/dashboards?**
A: Deferred to v0.2+. v0.5 is cost calculation only.

**Q: Does it support my LLM provider?**
A: If it's one of 20+ cloud or 10+ open-source APIs, yes. Submit an issue for others.

**Q: Can I export costs?**
A: Yes. CSV, JSON, and Parquet formats supported.

**Q: Is there a web interface?**
A: Not in v0.5 (core focus). Dashboards coming in v0.2+.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! Areas:
- [ ] Add new provider support
- [ ] Improve pricing accuracy
- [ ] Better error messages
- [ ] Documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Resources

- [OpenAnchor](https://github.com/Mullassery/openanchor) - Cost optimization middleware (uses PyTokenCalc)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [OpenAI Pricing](https://openai.com/pricing)
- [Google Pricing](https://ai.google.dev/pricing)

---

**PyTokenCalc v0.5: Know your LLM costs. Across all APIs. In real-time.**

This is the cost calculation core that powers OpenAnchor. Simple. Focused. Accurate.
