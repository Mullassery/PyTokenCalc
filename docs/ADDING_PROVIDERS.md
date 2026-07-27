# Adding New Token Counter Providers to PyTokenCalc v0.7

PyTokenCalc v0.7 is designed to support **any LLM provider's tokenizer**. New token counting methods can be added without modifying core code.

---

## Architecture: Pluggable Token Counters

Each provider has its own `TokenCounter` subclass that implements its specific token counting logic:

```
TokenCounter (abstract base)
├─ OpenAITokenCounter (tiktoken - local)
├─ HuggingFaceTokenCounter (transformers - local)
├─ ClaudeTokenCounter (API - cached)
├─ GeminiTokenCounter (API - cached)
├─ GroqTokenCounter (API - cached)
├─ DeepInfraTokenCounter (API - cached)
└─ [Your New Provider] (implement & register)
```

---

## Step 1: Create Your Token Counter

Subclass `TokenCounter` with your provider's token counting logic:

```python
from pytokencalc.tokenizers import TokenCounter, TokenCountResult

class MyProviderTokenCounter(TokenCounter):
    """Token counter for My Cool Provider"""

    @property
    def provider_name(self) -> str:
        """Unique provider identifier"""
        return "myprovider"

    def supports_model(self, model: str) -> bool:
        """Check if this counter handles the model"""
        return "myprovider" in model.lower() or model.startswith("mp-")

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens in text for the given model"""
        import time
        start = time.time()
        
        # Your token counting implementation
        # This could be:
        # - Local tokenizer (fast, <10ms)
        # - API call (cached, 200ms first time then instant)
        # - Formula-based estimation
        
        tokens = self._count_tokens(text, model)
        latency_ms = (time.time() - start) * 1000
        
        return TokenCountResult(
            input_tokens=tokens,
            source="local",  # or "api", or "formula"
            latency_ms=latency_ms,
            cached=False  # Set to True if result came from cache
        )

    def _count_tokens(self, text: str, model: str) -> int:
        """Implement your token counting logic"""
        # Example: Use a local library
        # from my_tokenizer import count_tokens
        # return count_tokens(text, model)
        
        # Or: Call provider API (will be cached by registry)
        # import requests
        # response = requests.post(f"https://api.myprovider.com/tokenize",
        #                         json={"text": text, "model": model})
        # return response.json()["token_count"]
        
        # Example: Simple approximation
        return len(text.split()) * 1.3
```

---

## Step 2: Handle Model Matching

The `supports_model()` method is critical for auto-routing:

```python
def supports_model(self, model: str) -> bool:
    """Return True if this counter can handle the model"""
    # Option 1: Prefix matching
    if model.startswith("mp-"):
        return True
    
    # Option 2: Name pattern matching
    if "myprovider" in model.lower():
        return True
    
    # Option 3: Explicit model list
    return model in ["mp-large", "mp-medium", "mp-small"]
```

---

## Step 3: Register Your Counter

### Option A: Runtime Registration (No Core Changes)

```python
from pytokencalc.tokenizers import TokenCounterRegistry
from my_module import MyProviderTokenCounter

# Create registry
registry = TokenCounterRegistry()

# Register your counter
registry.register(MyProviderTokenCounter())

# Use it immediately
result = registry.count_tokens("myprovider-model", "Your text here")
print(f"Tokens: {result.input_tokens}")
```

### Option B: Contribute to PyTokenCalc Core

1. Add your counter to `pytokencalc/tokenizers/myprovider_counter.py`
2. Register in `pytokencalc/tokenizers/registry.py`
3. Add import to `pytokencalc/tokenizers/__init__.py`
4. Write tests in `tests/`
5. Submit PR

---

## Step 4: Implement Caching (If Using APIs)

If your token counter calls an API, the registry automatically caches results:

```python
class MyProviderTokenCounter(TokenCounter):
    """API-based token counter (results are cached automatically)"""

    @property
    def provider_name(self) -> str:
        return "myprovider"

    def supports_model(self, model: str) -> bool:
        return model.startswith("mp-")

    def count(self, text: str, model: str) -> TokenCountResult:
        import time
        import requests
        
        start = time.time()
        
        # Call provider API for token count
        response = requests.post(
            "https://api.myprovider.com/tokenize",
            json={"text": text, "model": model}
        )
        
        tokens = response.json()["token_count"]
        latency_ms = (time.time() - start) * 1000
        
        # Return with source="api"
        # Registry automatically caches this result
        return TokenCountResult(
            input_tokens=tokens,
            source="api",
            latency_ms=latency_ms,
            cached=False  # First call is never cached
        )
```

When the same `(model, text)` pair is counted again, the cache returns instantly without calling the API.

---

## Step 5: Write Tests

```python
# In tests/test_my_provider_counter.py
import pytest
from pytokencalc.tokenizers import TokenCounterRegistry
from my_module import MyProviderTokenCounter

def test_my_provider_basic():
    counter = MyProviderTokenCounter()
    text = "Hello world from My Provider"
    result = counter.count(text, "myprovider-model")
    
    assert result.input_tokens > 0
    assert result.source in ["local", "api", "formula"]
    assert result.latency_ms > 0

def test_auto_routing():
    registry = TokenCounterRegistry()
    registry.register(MyProviderTokenCounter())
    
    # Should auto-detect our counter
    result = registry.count_tokens("myprovider-model", "Test text")
    assert result.input_tokens > 0

def test_caching():
    registry = TokenCounterRegistry()
    registry.register(MyProviderTokenCounter())
    
    text = "This should be cached"
    model = "myprovider-model"
    
    # First call: not cached
    result1 = registry.count_tokens(model, text)
    assert not result1.cached
    
    # Second call: should be cached
    result2 = registry.count_tokens(model, text)
    assert result2.cached
    assert result1.input_tokens == result2.input_tokens
```

---

## Real-World Examples

### Example 1: Local Tokenizer (Fast, No API Calls)

**Mistral using HuggingFace tokenizer:**

```python
from pytokencalc.tokenizers import TokenCounter, TokenCountResult
from transformers import AutoTokenizer

class MistralTokenCounter(TokenCounter):
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B")

    @property
    def provider_name(self) -> str:
        return "mistral"

    def supports_model(self, model: str) -> bool:
        return "mistral" in model.lower()

    def count(self, text: str, model: str) -> TokenCountResult:
        import time
        start = time.time()
        
        tokens = len(self.tokenizer.encode(text))
        latency_ms = (time.time() - start) * 1000
        
        return TokenCountResult(
            input_tokens=tokens,
            source="local",
            latency_ms=latency_ms,
            cached=False
        )
```

### Example 2: API-Based Token Counter (Accurate, Cached)

**Claude token counter using Anthropic API:**

```python
from pytokencalc.tokenizers import TokenCounter, TokenCountResult
import anthropic

class ClaudeTokenCounter(TokenCounter):
    def __init__(self):
        self.client = anthropic.Anthropic()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def supports_model(self, model: str) -> bool:
        return "claude" in model.lower()

    def count(self, text: str, model: str) -> TokenCountResult:
        import time
        start = time.time()
        
        # Call Anthropic API for accurate token count
        # (Will be cached by TokenCounterRegistry)
        response = self.client.messages.count_tokens(
            model=model,
            messages=[{"role": "user", "content": text}]
        )
        
        tokens = response.input_tokens
        latency_ms = (time.time() - start) * 1000
        
        return TokenCountResult(
            input_tokens=tokens,
            source="api",
            latency_ms=latency_ms,
            cached=False
        )
```

### Example 3: Hybrid Counter (Local + API)

**Smart routing: local when available, API when needed:**

```python
from pytokencalc.tokenizers import TokenCounter, TokenCountResult

class HybridTokenCounter(TokenCounter):
    def __init__(self):
        # Try to load local tokenizer
        try:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b")
            self.has_local = True
        except:
            self.has_local = False
            self.api_client = self._setup_api()

    @property
    def provider_name(self) -> str:
        return "hybrid"

    def supports_model(self, model: str) -> bool:
        return model.startswith("llama-") or model.startswith("hybrid-")

    def count(self, text: str, model: str) -> TokenCountResult:
        import time
        start = time.time()
        
        # Use local tokenizer if available (5ms)
        if self.has_local:
            tokens = len(self.tokenizer.encode(text))
            source = "local"
        else:
            # Fall back to API (200ms, but cached)
            tokens = self._call_api(text, model)
            source = "api"
        
        latency_ms = (time.time() - start) * 1000
        
        return TokenCountResult(
            input_tokens=tokens,
            source=source,
            latency_ms=latency_ms,
            cached=False
        )

    def _call_api(self, text: str, model: str) -> int:
        # Your API call logic
        pass

    def _setup_api(self):
        # Initialize API client
        pass
```

---

## Important: Avoid Common Mistakes

❌ **Don't**: Modify `TokenCountResult` after creation
```python
result = TokenCountResult(input_tokens=100, source="local", latency_ms=5)
result.cached = True  # DON'T DO THIS
```

✅ **Do**: Create result with correct values
```python
result = TokenCountResult(
    input_tokens=100,
    source="cache" if from_cache else "local",
    latency_ms=0.3 if from_cache else 5,
    cached=from_cache
)
```

❌ **Don't**: Block in `count()` with retries or loops
```python
def count(self, text: str, model: str):
    for i in range(3):  # DON'T RETRY HERE
        try:
            return self._count_with_retries()
        except:
            pass
```

✅ **Do**: Let the caller handle retries
```python
def count(self, text: str, model: str):
    return self._count_tokens(text, model)  # Fail fast
```

---

## Testing Your Provider

```bash
# Test your counter in isolation
pytest tests/test_my_provider.py -v

# Test with registry
pytest tests/ -k "my_provider" -v

# Test caching behavior
pytest tests/ -k "cache" -v
```

---

## Contributing

1. **Create** `pytokencalc/tokenizers/myprovider_counter.py`
2. **Implement** `TokenCounter` subclass
3. **Register** in `pytokencalc/tokenizers/registry.py`
4. **Export** in `pytokencalc/tokenizers/__init__.py`
5. **Test** in `tests/test_myprovider_counter.py` or existing test file
6. **Submit PR** with:
   - Working example
   - Test coverage
   - Latency benchmarks
   - Real usage examples

---

## FAQ

**Q: What's the difference between token counting and financial analysis?**
A: Token counting determines how many tokens are in text. Financial analysis converts tokens to monetary value. PyTokenCalc only does token counting. You can build financial analysis on top using PyTokenCalc's token counts + your own data.

**Q: Can I use an API-based tokenizer?**
A: Yes! The registry automatically caches API results, achieving 70-80% API call reduction.

**Q: What if my provider's tokenizer isn't public?**
A: Use their API. The registry caches results so 99% of calls return instantly.

**Q: How do I handle multiple models from the same provider?**
A: Use `supports_model()` to handle pattern matching:
```python
def supports_model(self, model: str) -> bool:
    return any(m in model for m in ["mp-", "myprovider-", "mp:"])
```

**Q: What if token counting changes for my provider?**
A: Update your `count()` implementation. Existing cached results won't be affected.

**Q: Can I use a probabilistic/approximate tokenizer?**
A: Yes, but set `source="formula"` to indicate it's an estimate, not exact.

---

**PyTokenCalc is built for flexibility.** It handles 20+ current providers and is ready for 100+ future ones. Any token counting method. Any provider. Fully pluggable.

For advanced analytics and optimization, build on top of PyTokenCalc's token counting API using your own business logic and provider data.
