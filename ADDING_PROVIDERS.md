# Adding New Providers to PyTokenCalc v0.6

PyTokenCalc v0.6 is designed to support **any LLM provider with any token counting method**. New providers can be added without modifying core code.

## Architecture: Pluggable Provider Models

Each provider has its own `CostModel` subclass that implements its specific token counting logic:

```
CostModel (abstract base)
├─ ClaudeTokenModel (simple: input/output)
├─ GPT4oTokenModel (dual: full + mini tokens)
├─ GeminiCharacterModel (character-based)
├─ GroqSpeedTieredModel (speed-aware)
├─ DeepInfraTokenModel (token-based wrapper)
├─ TogetherAITokenModel (token-based wrapper)
└─ [Your New Provider] (register dynamically)
```

## Step 1: Create Your Provider Model

Subclass `CostModel` with your provider's unique token counting logic:

```python
from pycostaudit import CostModel, UsageData

class MyCoolProviderModel(CostModel):
    """My Cool Provider - token counting method XYZ"""

    # Pricing data (fetch from provider API or hardcode)
    PRICING = {
        "model-a": {"input": 0.01, "output": 0.02},
        "model-b": {"input": 0.05, "output": 0.10},
    }

    @property
    def provider_name(self) -> str:
        """Must match lowercase provider string in UsageData"""
        return "mycoolprovider"

    def calculate(self, usage: UsageData) -> float:
        """Implement your provider's unique cost calculation"""
        if not self.validate(usage):
            raise ValueError(f"Invalid usage for {self.provider_name}")

        pricing = self.PRICING.get(usage.model)
        if not pricing:
            raise ValueError(f"Unknown model: {usage.model}")

        # Your token counting logic (replace with actual method)
        input_cost = (usage.input_tokens * pricing["input"]) / 1_000_000
        output_cost = (usage.output_tokens * pricing["output"]) / 1_000_000
        return input_cost + output_cost

    def validate(self, usage: UsageData) -> bool:
        """Validate that usage has required fields for your provider"""
        return (
            usage.provider == self.provider_name
            and usage.input_tokens >= 0
            and usage.output_tokens >= 0
            and usage.model in self.PRICING
        )
```

## Step 2: Register Your Provider

### Option A: Runtime Registration (No Code Change)

```python
from pycostaudit import CostCalculatorV6, CostModelRegistry
from my_module import MyCoolProviderModel

# Create calculator
calc = CostCalculatorV6()

# Register your model
model = MyCoolProviderModel()
calc.model_registry.register_model("mycoolprovider", model)

# Use it immediately
usage = UsageData(
    provider="mycoolprovider",
    model="model-a",
    input_tokens=1_000_000,
    output_tokens=500_000
)
cost = calc.calculate(usage)
```

### Option B: Contribute to PyTokenCalc (Add to Core)

1. Add your provider to `pycostaudit/cost_models.py`
2. Update `CostModelRegistry.__init__()` to include your model
3. Update `__init__.py` to export your model class
4. Submit PR

## Step 3: Handle Provider-Specific Token Fields

If your provider has unique token counting (like GPT-4o or Gemini), extend `UsageData`:

```python
@dataclass
class UsageData:
    # Standard fields (all providers)
    provider: str
    model: str
    input_tokens: int
    output_tokens: int

    # Your provider's special fields (already supported)
    your_special_field: Optional[str] = None
    your_token_variant: Optional[int] = None
    # ...
```

## Real-World Examples

### Example 1: Simple Token-Based Provider

**Mistral API**: Simple input/output token rates

```python
class MistralTokenModel(CostModel):
    PRICING = {
        "mistral-large": {"input": 0.008, "output": 0.024},
        "mistral-small": {"input": 0.0007, "output": 0.0021},
    }

    @property
    def provider_name(self) -> str:
        return "mistral"

    def calculate(self, usage: UsageData) -> float:
        pricing = self.PRICING[usage.model]
        return (
            (usage.input_tokens * pricing["input"]) +
            (usage.output_tokens * pricing["output"])
        ) / 1_000_000

    def validate(self, usage: UsageData) -> bool:
        return usage.provider == "mistral" and usage.model in self.PRICING
```

### Example 2: Custom Token Counting

**Llama Quantization-Aware Model**: Token count varies by quantization

```python
class LlamaQuantizationModel(CostModel):
    PRICING = {
        "llama-70b": {
            "base_rate": 0.50,  # per 1M tokens
            "quantization": {
                "fp32": 1.0,      # Full precision
                "fp16": 0.75,     # Half precision
                "int8": 0.50,     # Quantized
                "int4": 0.30,     # Heavily quantized
            }
        }
    }

    @property
    def provider_name(self) -> str:
        return "quantized_inference"

    def calculate(self, usage: UsageData) -> float:
        model_config = self.PRICING[usage.model]
        base_rate = model_config["base_rate"]
        
        # Apply quantization multiplier
        quantization = usage.quantization_level or "fp32"
        multiplier = model_config["quantization"].get(quantization, 1.0)
        
        effective_rate = base_rate * multiplier
        return (
            (usage.input_tokens * effective_rate) +
            (usage.output_tokens * effective_rate)
        ) / 1_000_000

    def validate(self, usage: UsageData) -> bool:
        return (
            usage.provider == "quantized_inference"
            and usage.model in self.PRICING
        )
```

### Example 3: Batch-Based Pricing

**DeepSeek Batch Optimizer**: Costs vary by batch size

```python
class DeepSeekBatchModel(CostModel):
    PRICING = {
        "deepseek-v3": {
            "per_token": 0.014,
            "batch_multipliers": {
                1: 1.0,          # Single request
                "1-10": 0.95,    # Small batch
                "11-100": 0.85,  # Medium batch
                "100+": 0.70,    # Large batch
            }
        }
    }

    @property
    def provider_name(self) -> str:
        return "deepseek"

    def calculate(self, usage: UsageData) -> float:
        pricing = self.PRICING[usage.model]
        base_rate = pricing["per_token"]
        
        # Apply batch discount
        batch_size = usage.batch_size or 1
        multiplier = self._get_batch_multiplier(batch_size)
        
        effective_rate = base_rate * multiplier
        return (
            (usage.input_tokens * effective_rate) +
            (usage.output_tokens * effective_rate)
        ) / 1_000_000

    def _get_batch_multiplier(self, batch_size: int) -> float:
        multipliers = self.PRICING["deepseek-v3"]["batch_multipliers"]
        if batch_size == 1:
            return multipliers[1]
        elif batch_size <= 10:
            return multipliers["1-10"]
        elif batch_size <= 100:
            return multipliers["11-100"]
        else:
            return multipliers["100+"]

    def validate(self, usage: UsageData) -> bool:
        return (
            usage.provider == "deepseek"
            and usage.model in self.PRICING
        )
```

## Pricing Data Sources

Keep your pricing current by fetching from provider APIs:

```python
import requests

class DynamicPricingModel(CostModel):
    def __init__(self):
        self.pricing = self._fetch_from_provider()
        self.last_update = datetime.now()

    def _fetch_from_provider(self) -> Dict:
        """Fetch live pricing from provider API"""
        response = requests.get("https://api.provider.com/pricing")
        return response.json()

    def calculate(self, usage: UsageData) -> float:
        # Use self.pricing which is dynamically updated
        # ...
```

## Testing Your Provider

```python
import pytest
from pycostaudit import UsageData, CostCalculatorV6

def test_my_provider():
    calc = CostCalculatorV6()
    
    usage = UsageData(
        provider="mycoolprovider",
        model="model-a",
        input_tokens=1_000_000,
        output_tokens=500_000
    )
    
    cost = calc.calculate(usage)
    
    # Assert expected cost
    expected = (1_000_000 * 0.01 + 500_000 * 0.02) / 1_000_000
    assert abs(cost - expected) < 0.001
```

## Multi-Provider Cost Comparison

Once registered, your provider is automatically available in cost comparisons:

```python
# Register your provider
registry = CostModelRegistry()
registry.register_model("mycoolprovider", MyCoolProviderModel())

# Compare across all providers
usage = UsageData(provider="mycoolprovider", ...)
calc = CostCalculatorV6()
calc.calculate(usage)

# See breakdown across all providers
breakdown = calc.cost_by_provider()
# {"anthropic": X, "openai": Y, "mycoolprovider": Z}
```

## Diversity of Token Models Supported

PyTokenCalc v0.6 handles:

| Token Model | Examples | Implementation |
|---|---|---|
| **Simple tokens** | Claude, Mistral | Input/output rate × tokens ÷ 1M |
| **Dual tokens** | GPT-4o (full+mini) | Multiple token streams with different rates |
| **Character-based** | Gemini | Characters × rate (no token count) |
| **Speed-tiered** | Groq | Base rate × speed multiplier |
| **Batch-aware** | DeepSeek | Rate × batch size discount |
| **Quantization-aware** | Llama on various providers | Rate × quantization multiplier |
| **Region-aware** | Bedrock | Rate × regional multiplier |
| **Time-based** | Future providers | Rate × time-of-day multiplier |
| **Usage-based** | Future providers | Dynamic rate based on usage patterns |
| **Custom logic** | Any provider | Implement your own calculation |

## Contributing

1. **Create your provider model** in `pycostaudit/cost_models.py`
2. **Add tests** in `tests/test_cost_models_v6.py`
3. **Update registry** in `CostModelRegistry.__init__()`
4. **Update exports** in `__init__.py`
5. **Submit PR** with real pricing examples

## FAQ

**Q: What if a new provider launches tomorrow?**
A: Create a `CostModel` subclass and register it. No core changes needed.

**Q: What if token counting changes mid-month?**
A: Override `calculate()` to handle multiple versions or dynamic rates.

**Q: Can I use my provider's real-time API for pricing?**
A: Yes! Override `PRICING` with dynamic fetching in `__init__()`.

**Q: What if my provider has 10 different pricing tiers?**
A: Extend `UsageData` with tier field, use it in `calculate()`.

**Q: Do all fields in UsageData apply to my provider?**
A: No. Validate what you need in `validate()`. Ignore others.

---

**PyTokenCalc is built for flexibility.** It handles 20+ current providers and is ready for 100+ future ones. Any token counting method. Any pricing model. Fully pluggable.
